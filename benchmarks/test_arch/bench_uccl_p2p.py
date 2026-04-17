#!/usr/bin/env python3
"""UCCL P2P benchmark wrapper. Requires UCCL to be built first."""
import subprocess, sys, json, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import save_json, detect_node

UCCL_DIR = Path(__file__).parent.parent.parent / "uccl"
BENCH_SCRIPT = UCCL_DIR / "p2p" / "benchmarks" / "benchmark_uccl.py"

def main():
    if not BENCH_SCRIPT.exists():
        print(f"UCCL benchmark not found at {BENCH_SCRIPT}")
        print("Build UCCL first:")
        print(f"  cd {UCCL_DIR} && bash build.sh cu12 p2p --install")
        sys.exit(1)

    try:
        import uccl  # noqa: F401
    except ImportError:
        print("UCCL not installed. Build it:")
        print(f"  cd {UCCL_DIR} && bash build.sh cu12 p2p --install")
        sys.exit(1)

    # UCCL requires torchrun for multi-process setup
    print("UCCL benchmark requires torchrun with 2 nodes.")
    print("Run manually:")
    print(f"  torchrun --nproc_per_node=1 --nnodes=2 --node_rank=0 \\")
    print(f"    --master_addr=<IP> --master_port=29500 {BENCH_SCRIPT}")
    print()
    print("Then save results via:")
    print("  python bench_compare.py")

if __name__ == "__main__":
    main()
