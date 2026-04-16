#!/usr/bin/env python3
"""
Granite 4 MoE expert-activation compression.

The all-to-all shuffle between tokens and experts is the long-payload
RDMA queue in Update 4's Config E. Compressing the expert-output
activation before the all-to-all shrinks the bulk path and matches the
cold-QP role.

If the model exposes expert outputs via a forward hook we use them
directly; otherwise we fall back to synthesising an activation tensor
of the right shape from the router logits so the compression pipeline
can still be exercised end-to-end.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    PerBitsResult, Result, detect_node, save_json, timed_us, top_k_overlap,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="ibm-granite/granite-4.0-h-tiny",
                   help="MoE variants: h-tiny (smaller MoE), h-small (full), h-small-FP8.")
    p.add_argument("--device", default="auto", choices=["cuda", "cpu", "auto"])
    p.add_argument("--bits", nargs="+", type=int, default=[8, 4, 3])
    p.add_argument("--qjl-dim", type=int, default=256)
    p.add_argument("--tokens-per-expert", type=int, default=128)
    args = p.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    device_map = "auto" if device == "cuda" else device

    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype, device_map=device_map)
    tok = AutoTokenizer.from_pretrained(args.model)

    prompt = "Mixture of experts dispatches tokens to expert FFNs via all-to-all."
    target = next(model.parameters()).device if device == "cuda" else device
    inputs = tok(prompt, return_tensors="pt").to(target)
    seq_len = int(inputs["input_ids"].shape[1])

    cfg = model.config
    d_model = cfg.hidden_size
    n_experts = getattr(cfg, "num_local_experts", getattr(cfg, "num_experts", 8))

    # Capture the first MoE layer's expert-output activation with a hook.
    captured = {}

    def grab(_module, _inputs, output):
        if "act" in captured:
            return
        # Accept plain tensors or (tensor, router_logits) tuples.
        t = output[0] if isinstance(output, tuple) else output
        if not isinstance(t, torch.Tensor):
            return
        captured["act"] = t.detach().float().cpu().numpy()

    # Target the MoE block by explicit name suffix (Granite 4 hybrid).
    handle = None
    for name, mod in model.named_modules():
        cls = mod.__class__.__name__
        if name.endswith("block_sparse_moe") and "MoE" in cls and "Gating" not in cls and "Expert" not in cls:
            handle = mod.register_forward_hook(grab)
            break

    with torch.no_grad():
        _ = model(**inputs, use_cache=True)
    if handle is not None:
        handle.remove()

    act = captured.get("act")
    note = ""
    if act is None or act.ndim < 2 or act.shape[-1] != d_model:
        # Fallback: synthesise a routed-activation tensor of the expected shape.
        rng = np.random.default_rng(seed=0)
        act = rng.standard_normal((n_experts, args.tokens_per_expert, d_model)).astype(np.float32)
        note = "no MoE hook available; used synthetic (n_experts, tokens, d_model) activation."
    else:
        act = act.reshape(-1, d_model).astype(np.float32)

    host, gpu = detect_node()
    result = Result(
        model=args.model,
        architecture="granite4_moe",
        hostname=host,
        gpu=gpu,
        seq_len=seq_len,
        state_shape=list(act.shape),
        notes=note or "captured expert-output activation pre-all-to-all.",
    )

    for bits in args.bits:
        sq = ScuffedQuant(dim=d_model, bits=bits, qjl_dim=args.qjl_dim)
        compressed, compress_us = timed_us(sq.compress_expert_activation, act)
        _, decompress_us = timed_us(sq.decompress, compressed)

        # Rank overlap: use first row as query against the full expert batch.
        flat = act.reshape(-1, d_model)
        query = flat[:1, :]
        exact = (query @ flat.T).squeeze()
        approx = sq.attention_scores(query, sq.compress(flat)).squeeze()
        overlap = top_k_overlap(exact, approx, k=8)
        ratio = sq.compression_ratio(flat.shape[0])

        result.per_bits.append(PerBitsResult(
            bits=bits,
            compression_ratio=float(ratio),
            rank_overlap_topk=float(overlap),
            decompress_us=decompress_us,
            compress_us=compress_us,
        ))

    out = save_json(result, "granite4_moe")
    print(f"[bench_granite4_moe] wrote {out}")


if __name__ == "__main__":
    main()
