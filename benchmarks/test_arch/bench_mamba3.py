#!/usr/bin/env python3
"""
Mamba-3 (or Mamba-2 fallback) SSM state compression.

Mamba's per-layer hidden state is O(1) in the sequence length — a fixed
(d_state, d_model) matrix per layer. We extract that state after a
prefill pass and run scuffedQuant on the last axis (d_model), so the
same Walsh-Hadamard + codebook pipeline applies as in the Transformer
path.

Model selection:
  - If state-spaces/mamba-3-1b is reachable, use it.
  - Otherwise fall back to state-spaces/mamba2-2.7b and tag the result
    with notes="mamba2-fallback". The shape story is the same.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    PerBitsResult, Result, detect_node, save_json, timed_us, top_k_overlap,
)


def try_load(name, device, dtype):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model = AutoModelForCausalLM.from_pretrained(name, dtype=dtype, device_map=device)
    tok = AutoTokenizer.from_pretrained(name)
    return model, tok


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="state-spaces/mamba-3-1b")
    p.add_argument("--fallback", default="state-spaces/mamba-130m-hf",
                   help="HF-compatible Mamba v1 (smallest) used when mamba-3 is unavailable.")
    p.add_argument("--device", default="auto", choices=["cuda", "cpu", "auto"])
    p.add_argument("--bits", nargs="+", type=int, default=[8, 4, 3])
    p.add_argument("--qjl-dim", type=int, default=256)
    args = p.parse_args()

    import torch
    from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32

    notes = ""
    try:
        model, tok = try_load(args.model, device, dtype)
        model_name = args.model
    except Exception as e:
        notes = f"mamba-3 unavailable ({e.__class__.__name__}); fell back to {args.fallback}"
        model, tok = try_load(args.fallback, device, dtype)
        model_name = args.fallback

    prompt = (
        "State-space models replace the growing KV cache with a fixed-size "
        "hidden state that evolves step-by-step like a linear RNN."
    )
    inputs = tok(prompt, return_tensors="pt").to(device)
    seq_len = int(inputs["input_ids"].shape[1])

    # Hook the SSM state. The HF Mamba models return ssm_states as part of the
    # MambaCache in outputs.cache_params after a forward pass. We collect one
    # state per layer.
    with torch.no_grad():
        outputs = model(**inputs, use_cache=True)

    cache = getattr(outputs, "cache_params", None)
    layer_states = []
    if cache is not None:
        # New API: cache.layers[i] is a LinearAttentionLayer with
        # .recurrent_states shape (batch, d_model, d_state).
        if hasattr(cache, "layers") and cache.layers:
            for l in cache.layers:
                rs = getattr(l, "recurrent_states", None)
                if rs is not None:
                    layer_states.append(rs[0].float().cpu().numpy())
        # Older HF path: cache.ssm_states dict keyed by layer index.
        elif hasattr(cache, "ssm_states"):
            layer_states = [v[0].float().cpu().numpy() for v in cache.ssm_states.values()]

    if not layer_states:
        raise SystemExit("No SSM layer states extracted; check HF version.")

    # shape is (d_model, d_state)
    d_model = layer_states[0].shape[0]
    d_state = layer_states[0].shape[1]

    host, gpu = detect_node()
    result = Result(
        model=model_name,
        architecture="mamba3",
        hostname=host,
        gpu=gpu,
        seq_len=seq_len,
        state_shape=[len(layer_states), d_model, d_state],
        notes=notes or "ssm_states extracted per layer, shape (d_model, d_state).",
    )

    for bits in args.bits:
        sq = ScuffedQuant(dim=d_state, bits=bits, qjl_dim=args.qjl_dim)
        overlaps, ratios = [], []
        compress_us_total, decompress_us_total = 0.0, 0.0

        for state in layer_states:
            # state shape: (d_model, d_state). Treat each row as a vector.
            flat = state.astype(np.float32)
            compressed, compress_us = timed_us(sq.compress_ssm_state, flat[None, ...])
            compress_us_total += compress_us
            _, decompress_us = timed_us(sq.decompress, compressed)
            decompress_us_total += decompress_us

            # Proxy retrieval: treat last row as query, score other rows.
            query = flat[-1:, :]
            exact = (query @ flat.T).squeeze()
            approx = sq.attention_scores(query, sq.compress(flat)).squeeze()
            overlaps.append(top_k_overlap(exact, approx, k=8))
            ratios.append(sq.compression_ratio(flat.shape[0]))

        result.per_bits.append(PerBitsResult(
            bits=bits,
            compression_ratio=float(np.mean(ratios)),
            rank_overlap_topk=float(np.mean(overlaps)),
            decompress_us=decompress_us_total / max(len(layer_states), 1),
            compress_us=compress_us_total / max(len(layer_states), 1),
        ))

    out = save_json(result, "mamba3")
    print(f"[bench_mamba3] wrote {out}")


if __name__ == "__main__":
    main()
