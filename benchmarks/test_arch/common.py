"""Shared harness for architecture benchmarks."""
import json, os, socket, time
import numpy as np
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List

@dataclass
class PerBits:
    bits: int
    compression_ratio: float
    rank_overlap_topk: float
    compress_us: float

@dataclass
class ArchResult:
    model: str
    architecture: str  # "transformer", "mamba", "hybrid", "moe"
    hostname: str
    gpu: str
    seq_len: int
    per_bits: list
    notes: str = ""

def detect_node():
    hostname = socket.gethostname().lower()
    try:
        import torch
        gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"
    except ImportError:
        gpu = "cpu"
    return hostname, gpu

def results_dir():
    d = Path(__file__).parent.parent / "results" / "test_arch"
    d.mkdir(parents=True, exist_ok=True)
    return d

def save_json(data: dict, tag: str):
    hostname = detect_node()[0]
    out = results_dir() / f"{hostname}_{tag}.json"
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {out}")
    return out

def top_k_overlap(exact, approx, k=8):
    k = min(k, len(exact))
    e = set(np.argsort(-exact)[:k])
    a = set(np.argsort(-approx)[:k])
    return len(e & a) / k
