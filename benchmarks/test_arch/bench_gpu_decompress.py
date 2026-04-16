#!/usr/bin/env python3
"""
GPU-side decompression micro-benchmark.

Produces a CompressedKV on CPU (the existing pipeline), then decompresses
it on the local GPU using the torch port in ScuffedQuant.decompress_torch.
The output timing is what ends up being consumed on the decode side when
a compressed KV block arrives over RDMA.

Runs on a fixed synthetic workload (n rows by d dim) so the comparison
between nodes is apples-to-apples independent of which HF model happens
to be loadable.
"""

import argparse
import json
import socket
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import detect_node, results_dir


def time_cuda(fn, iters: int, warmup: int):
    import torch
    for _ in range(warmup):
        _ = fn()
        torch.cuda.synchronize()
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(iters):
        _ = fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t0) / iters * 1e6


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dim", type=int, default=128,
                   help="Head dim for the synthetic workload (Granite-3.3 uses 64; Granite-4 uses 128).")
    p.add_argument("--bits", nargs="+", type=int, default=[8, 4, 3])
    p.add_argument("--rows", nargs="+", type=int, default=[4096, 32768, 131072],
                   help="Number of (n) rows per run; picks several sizes to show scaling.")
    p.add_argument("--iters", type=int, default=50)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--qjl-dim", type=int, default=256)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    import torch
    if not torch.cuda.is_available():
        raise SystemExit("CUDA not available; this bench is GPU-only.")

    host, gpu = detect_node()
    device = "cuda"
    rng = np.random.default_rng(args.seed)

    records = []
    for rows in args.rows:
        x = rng.standard_normal((rows, args.dim)).astype(np.float32)

        for bits in args.bits:
            sq = ScuffedQuant(dim=args.dim, bits=bits, qjl_dim=args.qjl_dim)
            c = sq.compress(x)
            # prime the per-device table caches
            _ = sq.decompress_torch(c, device=device)
            gpu_us = time_cuda(lambda: sq.decompress_torch(c, device=device),
                               iters=args.iters, warmup=args.warmup)

            # CPU baseline for the same CompressedKV.
            # Each call copies, so time the steady-state best-of-K.
            cpu_times = []
            for _ in range(args.iters):
                t0 = time.perf_counter()
                sq.decompress(c)
                cpu_times.append((time.perf_counter() - t0) * 1e6)
            cpu_us = float(np.median(cpu_times))

            records.append({
                "rows": rows,
                "dim": args.dim,
                "bits": bits,
                "compression_ratio": sq.compression_ratio(rows),
                "decompress_gpu_us": gpu_us,
                "decompress_cpu_us": cpu_us,
                "cpu_over_gpu": cpu_us / gpu_us,
            })
            print(f"  rows={rows:7d}  dim={args.dim}  bits={bits}   "
                  f"gpu={gpu_us:8.2f}us  cpu={cpu_us:10.2f}us  x{cpu_us/gpu_us:6.1f}")

    out = {
        "hostname": host,
        "gpu": gpu,
        "gpu_name": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "records": records,
    }
    path = results_dir() / f"{host}_gpu_decompress.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[bench_gpu_decompress] wrote {path}")


if __name__ == "__main__":
    main()
