#!/usr/bin/env python3
"""
scuffedQuant on a real LLM: compress KV cache and verify attention scores.

Loads Granite 3.3-2B, runs prefill, extracts the KV cache, compresses it
with scuffedQuant, and compares attention outputs between exact and
compressed KV. This proves the math on real model activations, not just
random vectors.

Usage:
    # In the ScuffedRDMA venv:
    source .venv/bin/activate
    python benchmarks/benchmark_scuffed_quant_llm.py

    # On Mac (MLX not needed, runs on CPU):
    python benchmarks/benchmark_scuffed_quant_llm.py --device cpu
"""

import argparse
import json
import os
import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant


def extract_kv_cache(model, tokenizer, prompt: str, device: str):
    """Run prefill and extract the KV cache from all layers."""
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model(**inputs, use_cache=True)

    cache = outputs.past_key_values
    # DynamicCache.layers[i].keys / .values
    # each shape: (batch, num_kv_heads, seq_len, head_dim)
    kv = []
    for layer in cache.layers:
        kv.append((layer.keys, layer.values))
    return kv, inputs['input_ids'].shape[1]


def compress_kv_layer(sq: ScuffedQuant, keys: np.ndarray,
                       values: np.ndarray):
    """Compress one layer's K and V tensors."""
    # keys shape: (num_heads, seq_len, head_dim)
    # Reshape to (num_heads * seq_len, head_dim) for compression
    n_heads, seq_len, head_dim = keys.shape
    K_flat = keys.reshape(-1, head_dim)
    V_flat = values.reshape(-1, head_dim)

    K_compressed = sq.compress(K_flat)
    V_compressed = sq.compress(V_flat)

    return K_compressed, V_compressed


def compare_attention(sq: ScuffedQuant, queries: np.ndarray,
                       keys_exact: np.ndarray,
                       K_compressed):
    """Compare exact vs compressed attention scores for one head."""
    # queries: (1, head_dim) -- the last token's query
    # keys_exact: (seq_len, head_dim)
    exact_scores = queries @ keys_exact.T  # (1, seq_len)

    approx_scores = sq.attention_scores(queries, K_compressed)

    return exact_scores.squeeze(), approx_scores.squeeze()


def main():
    parser = argparse.ArgumentParser(
        description='scuffedQuant on real LLM KV cache')
    parser.add_argument('--model', type=str,
                        default='ibm-granite/granite-3.3-2b-instruct')
    parser.add_argument('--device', type=str, default='cuda',
                        choices=['cuda', 'cpu'])
    parser.add_argument('--bits', type=int, default=3)
    parser.add_argument('--qjl-dim', type=int, default=256)
    parser.add_argument('--output', type=str,
                        default=str(Path(__file__).parent / 'results'))
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if args.device == 'cuda' and not torch.cuda.is_available():
        print("CUDA not available, falling back to CPU")
        args.device = 'cpu'

    print(f"scuffedQuant LLM Benchmark")
    print(f"  Model: {args.model}")
    print(f"  Device: {args.device}")
    print(f"  Bits: {args.bits}")
    print()

    # Load model
    print("Loading model...")
    t0 = time.time()
    dtype = torch.bfloat16 if args.device == 'cuda' else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=dtype, device_map=args.device,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    print(f"  Loaded in {time.time()-t0:.1f}s")

    # Get model config
    config = model.config
    n_layers = config.num_hidden_layers
    n_kv_heads = getattr(config, 'num_key_value_heads', config.num_attention_heads)
    head_dim = config.hidden_size // config.num_attention_heads
    print(f"  Layers: {n_layers}, KV heads: {n_kv_heads}, head_dim: {head_dim}")
    print()

    # Prefill with a real prompt
    prompt = (
        "The key-value cache in transformer inference trades memory for "
        "computation. Without it, each decode step would recompute attention "
        "over the entire sequence, which is quadratic in sequence length. "
        "With the cache, decode is linear: each new token only computes its "
        "own key and value projections."
    )

    print(f"Running prefill ({len(prompt)} chars)...")
    kv_cache, seq_len = extract_kv_cache(model, tokenizer, prompt, args.device)
    print(f"  Sequence length: {seq_len} tokens")
    print(f"  KV cache: {n_layers} layers x {n_kv_heads} heads x {seq_len} "
          f"tokens x {head_dim} dim")

    # Compute total KV size
    kv_bytes_fp16 = n_layers * 2 * n_kv_heads * seq_len * head_dim * 2
    print(f"  Total KV size (FP16): {kv_bytes_fp16/1024:.0f} KB")
    print()

    # Create quantizer
    sq = ScuffedQuant(dim=head_dim, bits=args.bits, qjl_dim=args.qjl_dim)

    # Compress and compare each layer
    print(f"=== Per-Layer Compression ({args.bits}-bit) ===")
    results = {
        'model': args.model,
        'bits': args.bits,
        'qjl_dim': args.qjl_dim,
        'n_layers': n_layers,
        'n_kv_heads': n_kv_heads,
        'head_dim': head_dim,
        'seq_len': seq_len,
        'layers': [],
    }

    total_abs_err_qjl = []
    total_abs_err_naive = []
    total_topk_overlap = []
    total_compress_ms = 0

    for layer_idx in range(n_layers):
        kv_pair = kv_cache[layer_idx]
        # Shape: (batch=1, n_kv_heads, seq_len, head_dim)
        K = kv_pair[0][0].float().cpu().numpy()  # (n_kv_heads, seq_len, head_dim)
        V = kv_pair[1][0].float().cpu().numpy()

        # Compress
        t0 = time.perf_counter()
        K_flat = K.reshape(-1, head_dim)
        V_flat = V.reshape(-1, head_dim)
        K_compressed = sq.compress(K_flat)
        V_compressed = sq.compress(V_flat)
        compress_ms = (time.perf_counter() - t0) * 1000
        total_compress_ms += compress_ms

        # Compare attention scores for each head using last token as query
        # Simulate: query = last key (approximate, just to test score accuracy)
        layer_abs_err_qjl = []
        layer_abs_err_naive = []
        layer_topk = []

        for h in range(n_kv_heads):
            keys_h = K[h]  # (seq_len, head_dim)
            query = keys_h[-1:, :]  # (1, head_dim) -- last token

            # Per-head compressed keys
            K_h_flat = keys_h  # already (seq_len, head_dim)
            K_h_comp = sq.compress(K_h_flat)

            exact = query @ keys_h.T  # (1, seq_len)
            with_qjl = sq.attention_scores(query, K_h_comp)
            without_qjl = query @ sq.decompress(K_h_comp).T

            exact = exact.squeeze()
            with_qjl = with_qjl.squeeze()
            without_qjl = without_qjl.squeeze()

            layer_abs_err_qjl.append(np.abs(exact - with_qjl).mean())
            layer_abs_err_naive.append(np.abs(exact - without_qjl).mean())

            # Top-k overlap
            topk = min(8, seq_len)
            exact_topk = set(np.argsort(-exact)[:topk])
            qjl_topk = set(np.argsort(-with_qjl)[:topk])
            layer_topk.append(len(exact_topk & qjl_topk) / topk)

        mean_err_qjl = np.mean(layer_abs_err_qjl)
        mean_err_naive = np.mean(layer_abs_err_naive)
        mean_topk = np.mean(layer_topk)

        total_abs_err_qjl.append(mean_err_qjl)
        total_abs_err_naive.append(mean_err_naive)
        total_topk_overlap.append(mean_topk)

        ratio = sq.compression_ratio(n_kv_heads * seq_len)

        if layer_idx % 4 == 0 or layer_idx == n_layers - 1:
            print(f"  L{layer_idx:2d}: abs_err={mean_err_qjl:.3f} "
                  f"(naive={mean_err_naive:.3f})  "
                  f"top-{topk}={mean_topk:.0%}  "
                  f"{compress_ms:.0f}ms")

        results['layers'].append({
            'layer': layer_idx,
            'abs_err_qjl': float(mean_err_qjl),
            'abs_err_naive': float(mean_err_naive),
            'topk_overlap': float(mean_topk),
            'compress_ms': compress_ms,
        })

    # Summary
    print()
    print(f"=== Summary ===")
    print(f"  Mean abs error (with QJL):    {np.mean(total_abs_err_qjl):.4f}")
    print(f"  Mean abs error (without QJL): {np.mean(total_abs_err_naive):.4f}")
    qjl_better = np.mean(total_abs_err_qjl) < np.mean(total_abs_err_naive)
    print(f"  QJL helps: {qjl_better}")
    print(f"  Mean top-{topk} overlap: {np.mean(total_topk_overlap):.1%}")
    print(f"  Total compress time: {total_compress_ms:.0f}ms")
    print(f"  Compression ratio: {sq.compression_ratio(n_kv_heads * seq_len):.1f}x")

    # What this means for RDMA transfer
    compressed_bytes = kv_bytes_fp16 / sq.compression_ratio(n_kv_heads * seq_len)
    print()
    print(f"=== RDMA Transfer Impact ===")
    print(f"  FP16 KV: {kv_bytes_fp16/1024:.0f} KB")
    print(f"  scuffedQuant {args.bits}b: {compressed_bytes/1024:.0f} KB")
    print(f"  On 10GbE (1.2 GB/s): {kv_bytes_fp16/1.2e9*1000:.1f}ms -> "
          f"{compressed_bytes/1.2e9*1000:.1f}ms")

    results['summary'] = {
        'mean_abs_err_qjl': float(np.mean(total_abs_err_qjl)),
        'mean_abs_err_naive': float(np.mean(total_abs_err_naive)),
        'qjl_helps': bool(qjl_better),
        'mean_topk_overlap': float(np.mean(total_topk_overlap)),
        'compression_ratio': sq.compression_ratio(n_kv_heads * seq_len),
        'kv_fp16_bytes': kv_bytes_fp16,
        'kv_compressed_bytes': compressed_bytes,
    }

    output_file = os.path.join(args.output, 'scuffed_quant_llm.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_file}")


if __name__ == '__main__':
    main()
