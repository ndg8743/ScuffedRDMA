#!/usr/bin/env python3
"""
Scuffed auto-kernel benchmark: eager vs compiled vs max-autotune.

Times the GPU decompression kernel in three forms:
  - eager: plain torch ops (decompress_torch)
  - compiled-ro: torch.compile(mode="reduce-overhead")
  - compiled-max: torch.compile(mode="max-autotune")

First call under torch.compile pays compilation cost; we measure
steady-state latency after a warmup of `--warmup` iterations.

Output: results/test_arch/{host}_auto_kernel.json
"""

import argparse
import json
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
    t0 = time.perf_counter()
    for _ in range(iters):
        _ = fn()
    torch.cuda.synchronize()
    return (time.perf_counter() - t0) / iters * 1e6


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dim", type=int, default=128)
    p.add_argument("--bits", nargs="+", type=int, default=[3, 4, 8])
    p.add_argument("--rows", nargs="+", type=int, default=[4096, 32768, 131072])
    p.add_argument("--iters", type=int, default=50)
    p.add_argument("--warmup", type=int, default=20)
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()

    import torch
    if not torch.cuda.is_available():
        raise SystemExit("CUDA not available; auto-kernel bench is GPU-only.")
    torch.set_float32_matmul_precision("high")

    host, gpu = detect_node()
    device = "cuda"
    rng = np.random.default_rng(args.seed)

    records = []
    for rows in args.rows:
        x = rng.standard_normal((rows, args.dim)).astype(np.float32)

        for bits in args.bits:
            sq = ScuffedQuant(dim=args.dim, bits=bits)
            c = sq.compress(x)

            # warmup each path (also triggers torch.compile)
            _ = sq.decompress_torch(c, device=device)
            _ = sq.decompress_torch_autotune(c, device=device, mode="reduce-overhead")
            # max-autotune is slow to compile; time the compile step separately
            t0 = time.perf_counter()
            _ = sq.decompress_torch_autotune(c, device=device, mode="max-autotune")
            compile_s = time.perf_counter() - t0

            eager_us = time_cuda(lambda: sq.decompress_torch(c, device=device),
                                 iters=args.iters, warmup=args.warmup)
            ro_us = time_cuda(
                lambda: sq.decompress_torch_autotune(c, device=device, mode="reduce-overhead"),
                iters=args.iters, warmup=args.warmup,
            )
            mx_us = time_cuda(
                lambda: sq.decompress_torch_autotune(c, device=device, mode="max-autotune"),
                iters=args.iters, warmup=args.warmup,
            )

            records.append({
                "rows": rows,
                "dim": args.dim,
                "bits": bits,
                "eager_us": eager_us,
                "compiled_reduce_overhead_us": ro_us,
                "compiled_max_autotune_us": mx_us,
                "max_autotune_compile_s": compile_s,
                "speedup_ro_over_eager": eager_us / ro_us,
                "speedup_mx_over_eager": eager_us / mx_us,
            })
            print(f"  rows={rows:7d}  bits={bits}   "
                  f"eager={eager_us:8.1f}us  "
                  f"ro={ro_us:8.1f}us (x{eager_us/ro_us:.2f})  "
                  f"mx={mx_us:8.1f}us (x{eager_us/mx_us:.2f})  "
                  f"[compile={compile_s:5.1f}s]")

    out = {
        "hostname": host,
        "gpu": gpu,
        "gpu_name": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "records": records,
    }
    path = results_dir() / f"{host}_auto_kernel.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"[bench_auto_kernel] wrote {path}")


if __name__ == "__main__":
    main()
