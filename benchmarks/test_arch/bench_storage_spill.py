#!/usr/bin/env python3
"""KV cache spill/retrieve benchmark on local NVMe.

Measures write throughput and read latency for compressed KV blocks
at different coalescing depths (1, 10, 20, 50, 100 blocks per write).
"""
import argparse, os, sys, time, tempfile
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common import detect_node, save_json, PerBits, ArchResult
from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant


def bench_write(data: bytes, path: str, count: int) -> float:
    """Write data count times, return avg us per write."""
    times = []
    for i in range(count):
        fname = os.path.join(path, f"block_{i}.bin")
        t0 = time.perf_counter()
        with open(fname, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        times.append((time.perf_counter() - t0) * 1e6)
    return float(np.median(times))


def bench_read(path: str, count: int) -> float:
    """Read back blocks, return avg us per read."""
    times = []
    files = sorted(Path(path).glob("block_*.bin"))[:count]
    for f in files:
        # drop page cache
        try:
            fd = os.open(str(f), os.O_RDONLY)
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
            os.close(fd)
        except Exception:
            pass
        t0 = time.perf_counter()
        data = f.read_bytes()
        times.append((time.perf_counter() - t0) * 1e6)
    return float(np.median(times)) if times else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bits", type=int, default=3)
    parser.add_argument("--dim", type=int, default=128)
    parser.add_argument("--seq-len", type=int, default=256)
    parser.add_argument("--heads", type=int, default=32)
    parser.add_argument("--coalesce", nargs="+", type=int, default=[1, 10, 20, 50])
    parser.add_argument("--writes", type=int, default=50)
    args = parser.parse_args()

    hostname, gpu = detect_node()
    print(f"Storage spill benchmark on {hostname}")

    # Generate a fake KV cache block (one layer, all heads)
    sq = ScuffedQuant(dim=args.dim, bits=args.bits)
    kv_block = np.random.randn(args.heads * args.seq_len, args.dim).astype(np.float32)
    comp = sq.compress(kv_block)

    # Serialize compressed block
    single_block = comp.indices.tobytes() + comp.norms.tobytes() + comp.qjl_signs.tobytes()
    single_kb = len(single_block) / 1024
    print(f"  Single block: {single_kb:.1f} KB ({args.bits}-bit, {args.seq_len} tokens, {args.heads} heads)")

    results = []
    for coalesce in args.coalesce:
        payload = single_block * coalesce
        payload_kb = len(payload) / 1024

        with tempfile.TemporaryDirectory(prefix="kv_spill_") as tmpdir:
            write_us = bench_write(payload, tmpdir, args.writes)
            read_us = bench_read(tmpdir, args.writes)
            write_mbps = (len(payload) / 1e6) / (write_us / 1e6)
            read_mbps = (len(payload) / 1e6) / (read_us / 1e6) if read_us > 0 else 0

        print(f"  coalesce={coalesce:>3}  payload={payload_kb:>7.1f} KB  "
              f"write={write_us:>8.0f} us ({write_mbps:>6.0f} MB/s)  "
              f"read={read_us:>8.0f} us ({read_mbps:>6.0f} MB/s)")
        results.append({
            "coalesce": coalesce, "payload_kb": payload_kb,
            "write_us": write_us, "write_mbps": write_mbps,
            "read_us": read_us, "read_mbps": read_mbps,
        })

    save_json({
        "hostname": hostname, "bits": args.bits,
        "dim": args.dim, "seq_len": args.seq_len,
        "heads": args.heads, "single_block_kb": single_kb,
        "coalesce_results": results,
    }, "storage_spill")


if __name__ == "__main__":
    main()
