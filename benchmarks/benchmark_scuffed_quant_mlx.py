#!/usr/bin/env python3
"""
scuffedQuant on MLX: test KV cache compression on Apple Silicon.

Loads a model via mlx-lm, extracts KV cache, compresses with scuffedQuant,
and verifies attention scores. Same quantizer as the cluster benchmark,
different model loading frontend.

Usage (Mac only):
    pip install mlx mlx-lm numpy
    python benchmarks/benchmark_scuffed_quant_mlx.py
"""

import argparse
import json
import os
import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant


def load_model_and_prefill(model_name: str, prompt: str):
    """Load model with mlx-lm and run prefill to get KV cache."""
    import mlx.core as mx
    from mlx_lm import load
    from mlx_lm.utils import generate_step

    model, tokenizer = load(model_name)

    # Tokenize
    input_ids = mx.array(tokenizer.encode(prompt))[None]  # (1, seq_len)

    # Run prefill to populate KV cache
    cache = []
    for layer in model.model.layers:
        cache.append(None)  # Will be populated by forward pass

    # Single forward pass to populate cache
    logits = model(input_ids)
    mx.eval(logits)

    return model, tokenizer, input_ids, logits


def extract_kv_from_mlx(model):
    """Extract KV cache tensors from MLX model layers."""
    import mlx.core as mx

    kv_layers = []
    for layer in model.model.layers:
        if hasattr(layer, 'self_attn'):
            attn = layer.self_attn
            # MLX caches are stored on the attention module after forward
            # Need to run with cache to extract
            pass

    return kv_layers


def run_with_cache(model, tokenizer, prompt: str):
    """Run model forward pass and capture KV cache via hooks."""
    import mlx.core as mx
    from mlx_lm.models.cache import make_prompt_cache

    input_ids = mx.array(tokenizer.encode(prompt))

    # Create cache
    cache = make_prompt_cache(model)

    # Prefill: process all tokens through the model with cache
    # mlx-lm processes tokens and fills cache entries
    for i in range(len(input_ids)):
        token = input_ids[i:i+1][None]  # (1, 1)
        logits = model(token, cache=cache)
        mx.eval(logits)

    # Extract numpy arrays from cache
    kv_data = []
    for entry in cache:
        if hasattr(entry, 'keys') and entry.keys is not None:
            K = np.array(entry.keys)    # (1, n_heads, seq_len, head_dim) or similar
            V = np.array(entry.values)
            kv_data.append((K, V))

    return kv_data, len(input_ids)


def main():
    parser = argparse.ArgumentParser(
        description='scuffedQuant on MLX (Apple Silicon)')
    parser.add_argument('--model', type=str,
                        default='mlx-community/Llama-3.2-3B-Instruct-4bit')
    parser.add_argument('--bits', type=int, default=3)
    parser.add_argument('--qjl-dim', type=int, default=256)
    parser.add_argument('--output', type=str,
                        default=str(Path(__file__).parent / 'results'))
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    import platform
    print(f"scuffedQuant MLX Benchmark")
    print(f"  Platform: {platform.system()} {platform.machine()}")
    print(f"  Model: {args.model}")
    print(f"  Bits: {args.bits}")
    print()

    try:
        import mlx.core as mx
        from mlx_lm import load
        from mlx_lm.models.cache import make_prompt_cache
    except ImportError:
        print("MLX not available. Install with: pip install mlx mlx-lm")
        print("This script is for Apple Silicon Macs only.")
        sys.exit(1)

    # Load model
    print("Loading model...")
    t0 = time.time()
    model, tokenizer = load(args.model)
    print(f"  Loaded in {time.time()-t0:.1f}s")

    # Get config
    config = model.model.layers[0].self_attn
    n_layers = len(model.model.layers)
    # Try to get head_dim from the model
    head_dim = None
    if hasattr(config, 'head_dim'):
        head_dim = config.head_dim
    elif hasattr(model.config, 'hidden_size') and hasattr(model.config, 'num_attention_heads'):
        head_dim = model.config.hidden_size // model.config.num_attention_heads

    n_kv_heads = getattr(model.config, 'num_key_value_heads',
                         model.config.num_attention_heads)
    print(f"  Layers: {n_layers}, KV heads: {n_kv_heads}, head_dim: {head_dim}")
    print()

    # Prefill
    prompt = (
        "The key-value cache in transformer inference trades memory for "
        "computation. Without it, each decode step would recompute attention "
        "over the entire sequence."
    )

    print("Running prefill...")
    kv_data, seq_len = run_with_cache(model, tokenizer, prompt)
    print(f"  Sequence length: {seq_len} tokens")
    print(f"  Extracted KV from {len(kv_data)} layers")

    if not kv_data:
        print("  ERROR: Could not extract KV cache. The MLX cache API may")
        print("  differ for this model. Try running manually:")
        print(f"    from mlx_lm import load")
        print(f"    model, tok = load('{args.model}')")
        print(f"    # inspect model.model.layers[0].self_attn")
        sys.exit(1)

    # Create quantizer
    sq = ScuffedQuant(dim=head_dim, bits=args.bits, qjl_dim=args.qjl_dim)

    # Test each layer
    print(f"\n=== Per-Layer Compression ({args.bits}-bit) ===")
    results = {
        'model': args.model,
        'platform': f"{platform.system()} {platform.machine()}",
        'bits': args.bits,
        'n_layers': len(kv_data),
        'head_dim': head_dim,
        'n_kv_heads': n_kv_heads,
        'seq_len': seq_len,
        'layers': [],
    }

    total_topk = []

    for layer_idx, (K, V) in enumerate(kv_data):
        # K shape varies by model: (1, n_heads, seq, dim) or (n_heads, seq, dim)
        if K.ndim == 4:
            K = K[0]  # remove batch dim
        if V.ndim == 4:
            V = V[0]

        n_h, s, d = K.shape

        layer_topk = []
        layer_err_qjl = []
        layer_err_naive = []

        for h in range(n_h):
            keys_h = K[h].astype(np.float32)  # (seq, head_dim)
            query = keys_h[-1:, :]

            K_h_comp = sq.compress(keys_h)
            exact = (query @ keys_h.T).squeeze()
            with_qjl = sq.attention_scores(query, K_h_comp).squeeze()
            without_qjl = (query @ sq.decompress(K_h_comp).T).squeeze()

            layer_err_qjl.append(np.abs(exact - with_qjl).mean())
            layer_err_naive.append(np.abs(exact - without_qjl).mean())

            topk = min(8, s)
            exact_top = set(np.argsort(-exact)[:topk])
            qjl_top = set(np.argsort(-with_qjl)[:topk])
            layer_topk.append(len(exact_top & qjl_top) / topk)

        mean_topk = np.mean(layer_topk)
        total_topk.append(mean_topk)

        if layer_idx % 4 == 0 or layer_idx == len(kv_data) - 1:
            print(f"  L{layer_idx:2d}: err={np.mean(layer_err_qjl):.3f}  "
                  f"top-{topk}={mean_topk:.0%}")

        results['layers'].append({
            'layer': layer_idx,
            'abs_err_qjl': float(np.mean(layer_err_qjl)),
            'abs_err_naive': float(np.mean(layer_err_naive)),
            'topk_overlap': float(mean_topk),
        })

    print(f"\n=== Summary ===")
    print(f"  Mean top-{topk} overlap: {np.mean(total_topk):.1%}")
    print(f"  Compression: {sq.compression_ratio(n_kv_heads * seq_len):.1f}x")

    results['summary'] = {
        'mean_topk_overlap': float(np.mean(total_topk)),
        'compression_ratio': sq.compression_ratio(n_kv_heads * seq_len),
    }

    output_file = os.path.join(args.output, 'scuffed_quant_mlx.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_file}")


if __name__ == '__main__':
    main()
