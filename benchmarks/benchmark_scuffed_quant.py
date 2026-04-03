#!/usr/bin/env python3
"""
scuffedQuant benchmark: KV cache compression accuracy and speed.

Tests the two-stage PolarQuant + QJL quantizer on realistic KV cache sizes.
Runs on any platform (cluster with numpy, Mac with numpy or MLX).

Usage:
    python benchmark_scuffed_quant.py [--bits 3] [--heads 32] [--dim 128]
"""

import argparse
import json
import os
import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant, CompressedKV


def benchmark_accuracy(sq: ScuffedQuant, n_keys: int, n_queries: int,
                       label: str) -> dict:
    """Test inner product preservation at a given scale."""
    rng = np.random.RandomState(0)
    keys = rng.randn(n_keys, sq.dim).astype(np.float32)
    queries = rng.randn(n_queries, sq.dim).astype(np.float32)

    # Exact scores
    exact = queries @ keys.T

    # Compress and score
    compressed = sq.compress(keys)
    approx = sq.attention_scores(queries, compressed)

    # Also test naive decompression (no QJL correction)
    naive = queries @ sq.decompress(compressed).T

    # Error metrics
    abs_err = np.abs(exact - approx)
    naive_err = np.abs(exact - naive)
    denom = np.abs(exact) + 1e-8

    result = {
        'label': label,
        'n_keys': n_keys,
        'n_queries': n_queries,
        'dim': sq.dim,
        'bits': sq.bits,
        'with_qjl': {
            'mean_abs_error': float(abs_err.mean()),
            'max_abs_error': float(abs_err.max()),
            'mean_rel_error': float((abs_err / denom).mean()),
            'p99_rel_error': float(np.percentile(abs_err / denom, 99)),
        },
        'without_qjl': {
            'mean_abs_error': float(naive_err.mean()),
            'max_abs_error': float(naive_err.max()),
            'mean_rel_error': float((naive_err / denom).mean()),
            'p99_rel_error': float(np.percentile(naive_err / denom, 99)),
        },
        'compression_ratio': sq.compression_ratio(n_keys),
        'original_bytes': n_keys * sq.dim * 4,
        'compressed_bytes': compressed.nbytes,
    }

    print(f"  {label}:")
    print(f"    With QJL:    mean_rel={result['with_qjl']['mean_rel_error']:.4%}"
          f"  p99_rel={result['with_qjl']['p99_rel_error']:.4%}")
    print(f"    Without QJL: mean_rel={result['without_qjl']['mean_rel_error']:.4%}"
          f"  p99_rel={result['without_qjl']['p99_rel_error']:.4%}")
    print(f"    Compression: {result['original_bytes']/1024:.0f}KB -> "
          f"{result['compressed_bytes']/1024:.0f}KB "
          f"({result['compression_ratio']:.1f}x)")

    return result


def benchmark_speed(sq: ScuffedQuant, n_keys: int, n_queries: int,
                    n_iters: int = 20) -> dict:
    """Measure compress/score throughput."""
    rng = np.random.RandomState(0)
    keys = rng.randn(n_keys, sq.dim).astype(np.float32)
    queries = rng.randn(n_queries, sq.dim).astype(np.float32)

    # Warmup
    compressed = sq.compress(keys)
    sq.attention_scores(queries, compressed)

    # Compress speed
    t0 = time.perf_counter()
    for _ in range(n_iters):
        compressed = sq.compress(keys)
    compress_ms = (time.perf_counter() - t0) / n_iters * 1000

    # Score speed
    t0 = time.perf_counter()
    for _ in range(n_iters):
        sq.attention_scores(queries, compressed)
    score_ms = (time.perf_counter() - t0) / n_iters * 1000

    # Baseline: raw matmul
    t0 = time.perf_counter()
    for _ in range(n_iters):
        queries @ keys.T
    matmul_ms = (time.perf_counter() - t0) / n_iters * 1000

    result = {
        'n_keys': n_keys,
        'compress_ms': compress_ms,
        'score_ms': score_ms,
        'raw_matmul_ms': matmul_ms,
        'score_overhead': score_ms / matmul_ms,
    }

    print(f"  {n_keys} keys: compress={compress_ms:.1f}ms  "
          f"score={score_ms:.1f}ms  raw={matmul_ms:.1f}ms  "
          f"overhead={result['score_overhead']:.1f}x")

    return result


def benchmark_bits_sweep(dim: int, n_keys: int = 512,
                         n_queries: int = 8) -> list:
    """Test accuracy across bit widths."""
    results = []
    for bits in [2, 3, 4, 6, 8]:
        sq = ScuffedQuant(dim=dim, bits=bits)
        r = benchmark_accuracy(sq, n_keys, n_queries, f"{bits}-bit")
        results.append(r)
    return results


def benchmark_kv_cache_simulation(num_heads: int, head_dim: int,
                                   seq_len: int, bits: int) -> dict:
    """Simulate compressing a full KV cache layer."""
    rng = np.random.RandomState(0)

    # K and V for one layer: (num_heads, seq_len, head_dim)
    K = rng.randn(num_heads * seq_len, head_dim).astype(np.float32)
    V = rng.randn(num_heads * seq_len, head_dim).astype(np.float32)
    queries = rng.randn(num_heads, head_dim).astype(np.float32)

    sq = ScuffedQuant(dim=head_dim, bits=bits)

    # Compress K and V
    t0 = time.perf_counter()
    K_compressed = sq.compress(K)
    V_compressed = sq.compress(V)
    compress_time = time.perf_counter() - t0

    # Attention scores with correction
    t0 = time.perf_counter()
    scores = sq.attention_scores(queries, K_compressed)
    score_time = time.perf_counter() - t0

    # Compare to exact
    exact_scores = queries @ K.T
    abs_err = np.abs(exact_scores - scores)
    denom = np.abs(exact_scores) + 1e-8

    original_bytes = (K.nbytes + V.nbytes)
    compressed_bytes = K_compressed.nbytes + V_compressed.nbytes

    result = {
        'num_heads': num_heads,
        'head_dim': head_dim,
        'seq_len': seq_len,
        'bits': bits,
        'compress_ms': compress_time * 1000,
        'score_ms': score_time * 1000,
        'mean_rel_error': float((abs_err / denom).mean()),
        'original_KB': original_bytes / 1024,
        'compressed_KB': compressed_bytes / 1024,
        'ratio': original_bytes / compressed_bytes,
    }

    print(f"  KV cache ({num_heads}h, {head_dim}d, {seq_len}s, {bits}b):")
    print(f"    {result['original_KB']:.0f}KB -> {result['compressed_KB']:.0f}KB "
          f"({result['ratio']:.1f}x)")
    print(f"    Score error: {result['mean_rel_error']:.4%}")
    print(f"    Compress: {result['compress_ms']:.1f}ms  "
          f"Score: {result['score_ms']:.1f}ms")

    return result


def main():
    parser = argparse.ArgumentParser(description='scuffedQuant Benchmark')
    parser.add_argument('--bits', type=int, default=3)
    parser.add_argument('--heads', type=int, default=32)
    parser.add_argument('--dim', type=int, default=128)
    parser.add_argument('--seq-len', type=int, default=512)
    parser.add_argument('--output', type=str,
                        default=str(Path(__file__).parent / 'results'))
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    import platform
    print(f"scuffedQuant Benchmark")
    print(f"  Platform: {platform.system()} {platform.machine()}")
    print(f"  Python: {platform.python_version()}")
    print(f"  NumPy: {np.__version__}")
    print()

    results = {}

    # 1. Accuracy across bit widths
    print("=== Bit Width Sweep ===")
    results['bits_sweep'] = benchmark_bits_sweep(args.dim)
    print()

    # 2. Speed at different scales
    print("=== Speed Benchmark ===")
    sq = ScuffedQuant(dim=args.dim, bits=args.bits)
    results['speed'] = []
    for n_keys in [128, 512, 2048, 8192]:
        r = benchmark_speed(sq, n_keys, n_queries=8)
        results['speed'].append(r)
    print()

    # 3. Full KV cache layer simulation
    print("=== KV Cache Simulation ===")
    results['kv_cache'] = []
    for seq_len in [128, 512, 2048]:
        r = benchmark_kv_cache_simulation(
            args.heads, args.dim, seq_len, args.bits)
        results['kv_cache'].append(r)
    print()

    # 4. Attention softmax accuracy (do the top-k positions stay the same?)
    print("=== Softmax Ranking Preservation ===")
    rng = np.random.RandomState(0)
    keys = rng.randn(args.seq_len, args.dim).astype(np.float32)
    queries = rng.randn(args.heads, args.dim).astype(np.float32)

    exact = queries @ keys.T
    compressed = sq.compress(keys)
    approx = sq.attention_scores(queries, compressed)

    # Check if top-k positions are preserved
    top_k = min(32, args.seq_len)
    exact_topk = np.argsort(-exact, axis=1)[:, :top_k]
    approx_topk = np.argsort(-approx, axis=1)[:, :top_k]

    overlap = 0
    total = 0
    for i in range(len(queries)):
        overlap += len(set(exact_topk[i]) & set(approx_topk[i]))
        total += top_k

    ranking_accuracy = overlap / total
    print(f"  Top-{top_k} overlap: {ranking_accuracy:.1%}")
    print(f"  ({overlap}/{total} positions match)")
    results['ranking'] = {
        'top_k': top_k,
        'overlap_ratio': ranking_accuracy,
    }
    print()

    # 5. RDMA transfer size comparison
    print("=== Transfer Size for Disaggregated Serving ===")
    for layers in [32, 80]:
        orig = 2 * layers * args.heads * args.dim * args.seq_len * 4  # K+V, FP32
        orig_fp16 = orig // 2
        ratio = sq.compression_ratio(args.heads * args.seq_len)
        compressed_size = orig_fp16 / ratio
        print(f"  {layers}L, {args.heads}h, {args.dim}d, seq={args.seq_len}:")
        print(f"    FP16: {orig_fp16/1024/1024:.0f}MB  "
              f"scuffedQuant {args.bits}b: {compressed_size/1024/1024:.0f}MB  "
              f"({ratio:.1f}x)")

    # Save
    output_file = os.path.join(args.output, 'scuffed_quant_benchmark.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_file}")


if __name__ == '__main__':
    main()
