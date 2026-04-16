"""
Shared harness for per-architecture scuffedQuant benchmarks.

Each bench_*.py script in this folder loads a model, extracts an
architecture-specific state tensor, runs scuffedQuant at a few bit
widths, and writes one JSON per (hostname, model) into
benchmarks/results/test_arch/. The aggregator in
benchmarks/aggregate_results.py joins Chimera and Cerberus outputs
into a single cross-node table.

This module stays thin on purpose: it does not reimplement anything
from middleware/rdma_tensor_cache. It only owns the result schema,
node detection, and file I/O.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Tuple

# Make the repo importable when scripts are run from this directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


@dataclass
class PerBitsResult:
    bits: int
    compression_ratio: float
    rank_overlap_topk: float
    decompress_us: float
    compress_us: float


@dataclass
class Result:
    model: str
    architecture: str              # "transformer" | "mamba3" | "granite4_hybrid" | "granite4_moe"
    hostname: str
    gpu: str
    seq_len: int
    state_shape: List[int]
    per_bits: List[PerBitsResult] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["per_bits"] = [asdict(p) for p in self.per_bits]
        return d


def detect_node() -> Tuple[str, str]:
    """Return (hostname_tag, gpu_tag). Falls back gracefully when CUDA is absent."""
    host = socket.gethostname().lower()
    # Map the long hostname to the short thesis tag.
    if "chimera" in host:
        host_tag = "chimera"
    elif "cerberus" in host:
        host_tag = "cerberus"
    else:
        host_tag = host.split(".")[0]

    gpu_tag = "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0).lower()
            for tag in ("5090", "3090", "a100", "h100", "5070", "v100"):
                if tag in name:
                    gpu_tag = tag
                    break
            else:
                gpu_tag = name.replace(" ", "_")
    except Exception:
        pass

    return host_tag, gpu_tag


def results_dir() -> Path:
    d = Path(__file__).resolve().parent.parent / "results" / "test_arch"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_json(result: Result, model_tag: str) -> Path:
    out = results_dir() / f"{result.hostname}_{model_tag}.json"
    with open(out, "w") as f:
        json.dump(result.to_dict(), f, indent=2)
    return out


def top_k_overlap(exact, approx, k: int = 8) -> float:
    """Rank-overlap on the top-k indices of two 1-D score arrays."""
    import numpy as np
    k = min(k, exact.size)
    if k == 0:
        return 0.0
    e = set(np.argsort(-exact)[:k].tolist())
    a = set(np.argsort(-approx)[:k].tolist())
    return len(e & a) / k


def timed_us(fn, *args, **kwargs) -> Tuple[object, float]:
    """Run fn and return (result, elapsed_microseconds)."""
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    return out, (time.perf_counter() - t0) * 1e6
