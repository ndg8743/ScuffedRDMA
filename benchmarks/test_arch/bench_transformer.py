#!/usr/bin/env python3
"""
Transformer KV-cache baseline for the per-architecture suite.

Ports the logic from benchmarks/benchmark_scuffed_quant_llm.py into the
test_arch Result schema so its JSON output slots into the cross-node
aggregator alongside the Mamba / Granite-hybrid / MoE runs.
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
    p.add_argument("--model", default="ibm-granite/granite-3.3-2b-instruct")
    p.add_argument("--device", default="cuda", choices=["cuda", "cpu", "auto"])
    p.add_argument("--bits", nargs="+", type=int, default=[8, 4, 3])
    p.add_argument("--qjl-dim", type=int, default=256)
    p.add_argument("--max-layers", type=int, default=0,
                   help="Cap the number of KV layers sampled (0 = all).")
    args = p.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant

    device = args.device
    if device in ("cuda", "auto"):
        device = "cuda" if torch.cuda.is_available() else "cpu"

    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype, device_map=device)
    tok = AutoTokenizer.from_pretrained(args.model)

    cfg = model.config
    head_dim = cfg.hidden_size // cfg.num_attention_heads

    prompt = (
        "The key-value cache in transformer inference trades memory for "
        "computation: each decode step reads a grown prefix of K and V "
        "instead of recomputing attention over the full sequence."
    )
    inputs = tok(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs, use_cache=True)
    seq_len = int(inputs["input_ids"].shape[1])

    layers = list(outputs.past_key_values.layers)
    if args.max_layers:
        layers = layers[: args.max_layers]

    host, gpu = detect_node()
    result = Result(
        model=args.model,
        architecture="transformer",
        hostname=host,
        gpu=gpu,
        seq_len=seq_len,
        state_shape=[len(layers), cfg.num_key_value_heads if hasattr(cfg, "num_key_value_heads") else cfg.num_attention_heads, seq_len, head_dim],
        notes="KV cache from outputs.past_key_values; per-layer K flattened to (heads*seq, head_dim).",
    )

    for bits in args.bits:
        sq = ScuffedQuant(dim=head_dim, bits=bits, qjl_dim=args.qjl_dim)
        overlaps, ratios = [], []
        compress_us_total, decompress_us_total = 0.0, 0.0

        for layer in layers:
            K = layer.keys[0].float().cpu().numpy()            # (heads, seq, head_dim)
            K_flat = K.reshape(-1, head_dim)
            compressed, compress_us = timed_us(sq.compress, K_flat)
            compress_us_total += compress_us
            _, decompress_us = timed_us(sq.decompress, compressed)
            decompress_us_total += decompress_us

            # Per-head top-k accuracy on last-token query.
            for h in range(K.shape[0]):
                keys_h = K[h]
                query = keys_h[-1:, :]
                exact = (query @ keys_h.T).squeeze()
                approx = sq.attention_scores(query, sq.compress(keys_h)).squeeze()
                overlaps.append(top_k_overlap(exact, approx, k=8))

            ratios.append(sq.compression_ratio(K_flat.shape[0]))

        result.per_bits.append(PerBitsResult(
            bits=bits,
            compression_ratio=float(np.mean(ratios)),
            rank_overlap_topk=float(np.mean(overlaps)),
            decompress_us=decompress_us_total / max(len(layers), 1),
            compress_us=compress_us_total / max(len(layers), 1),
        ))

    out = save_json(result, "transformer")
    print(f"[bench_transformer] wrote {out}")


if __name__ == "__main__":
    main()
