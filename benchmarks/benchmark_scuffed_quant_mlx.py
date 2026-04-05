#!/usr/bin/env python3
"""
scuffedQuant on MLX: test KV cache compression on Apple Silicon.

Same quantizer as the cluster, different model loading.
Requires: pip install mlx mlx-lm numpy
"""

import json
import os
import sys
import time
import platform
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant


def main():
    model_name = "mlx-community/granite-3.3-2b-instruct-4bit"
    bits = 3
    qjl_dim = 256  # match cluster benchmark_scuffed_quant_llm.py
    output_dir = str(Path(__file__).parent / "results")
    os.makedirs(output_dir, exist_ok=True)

    # Parse simple args
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--model" and i < len(sys.argv):
            model_name = sys.argv[i + 1]
        if arg == "--bits" and i < len(sys.argv):
            bits = int(sys.argv[i + 1])

    try:
        import mlx.core as mx
        from mlx_lm import load
        from mlx_lm.models.cache import make_prompt_cache
    except ImportError:
        print("Install: pip install mlx mlx-lm")
        sys.exit(1)

    print(f"scuffedQuant MLX")
    print(f"  {platform.system()} {platform.machine()}")
    print(f"  Model: {model_name}")
    print(f"  Bits: {bits}")
    print()

    # Load
    t0 = time.time()
    model, tokenizer = load(model_name)
    print(f"  Loaded in {time.time()-t0:.1f}s")

    n_layers = len(model.model.layers)
    head_dim = model.model.layers[0].self_attn.head_dim
    n_kv_heads = model.model.layers[0].self_attn.n_kv_heads
    print(f"  {n_layers} layers, {n_kv_heads} kv_heads, {head_dim} head_dim")

    # Prefill with the same prompt the cluster benchmark uses, so seq_len
    # and top-k selectivity line up with benchmark_scuffed_quant_llm.py.
    prompt = (
        "The key-value cache in transformer inference trades memory for "
        "computation. Without it, each decode step would recompute attention "
        "over the entire sequence, which is quadratic in sequence length. "
        "With the cache, decode is linear: each new token only computes its "
        "own key and value projections."
    )
    tokens = mx.array(tokenizer.encode(prompt))
    cache = make_prompt_cache(model)
    logits = model(tokens[None], cache=cache)
    mx.eval(logits)
    seq_len = tokens.shape[0]
    print(f"  Prefilled {seq_len} tokens")
    print()

    # Quantize each layer's KV and check attention accuracy
    sq = ScuffedQuant(dim=head_dim, bits=bits, qjl_dim=qjl_dim)
    results = {"model": model_name, "platform": f"{platform.system()} {platform.machine()}",
               "bits": bits, "layers": []}
    all_topk = []

    print(f"=== Per-Layer ({bits}-bit) ===")
    for li, entry in enumerate(cache):
        K = np.array(entry.keys[0])    # (n_heads, seq, dim)
        V = np.array(entry.values[0])

        n_h, s, d = K.shape
        layer_topk = []

        for h in range(n_h):
            keys_h = K[h].astype(np.float32)
            query = keys_h[-1:, :]
            c = sq.compress(keys_h)

            exact = (query @ keys_h.T).squeeze()
            approx = sq.attention_scores(query, c).squeeze()

            topk = min(8, s)
            e_set = set(np.argsort(-exact)[:topk])
            a_set = set(np.argsort(-approx)[:topk])
            layer_topk.append(len(e_set & a_set) / topk)

        mean_topk = np.mean(layer_topk)
        all_topk.append(mean_topk)

        if li % 4 == 0 or li == len(cache) - 1:
            print(f"  L{li:2d}: top-{topk}={mean_topk:.0%}")

        results["layers"].append({"layer": li, "topk_overlap": float(mean_topk)})

    print(f"\n  Mean top-{topk}: {np.mean(all_topk):.1%}")
    print(f"  Compression: {sq.compression_ratio(n_kv_heads * seq_len):.1f}x vs FP32")

    results["summary"] = {
        "mean_topk_overlap": float(np.mean(all_topk)),
        "compression_ratio": sq.compression_ratio(n_kv_heads * seq_len),
    }

    out = os.path.join(output_dir, "scuffed_quant_mlx.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Saved to {out}")


if __name__ == "__main__":
    main()
