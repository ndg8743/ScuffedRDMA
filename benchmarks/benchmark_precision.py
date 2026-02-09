#!/usr/bin/env python3
"""
Precision conversion benchmarks for RDMA tensor cache.

Measures throughput of FP32 -> FP16/BF16/INT8/MXFP4 conversions and
stochastic rounding at various tensor sizes representative of LLM
weight tensors and KV cache blocks.
"""

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from middleware.rdma_tensor_cache.precision import (
    PrecisionFormat, PrecisionManager, V100_PROFILE, RTX5070TI_PROFILE,
    _BYTES_PER_ELEMENT,
)
from middleware.rdma_tensor_cache.quantization import AdaptiveQuantizer


@dataclass
class ConversionResult:
    format: str
    tensor_size: int
    elements: int
    convert_ms: float
    roundtrip_ms: float
    throughput_gbps: float
    max_abs_error: float
    mean_rel_error: float
    compression_ratio: float


def benchmark_conversion(pm: PrecisionManager, quantizer: AdaptiveQuantizer,
                         tensor: np.ndarray, fmt: PrecisionFormat,
                         warmup: int = 3, repeats: int = 20) -> ConversionResult:
    """Benchmark a single format conversion."""
    # Warmup
    for _ in range(warmup):
        q, meta = quantizer.quantize(tensor, fmt)
        quantizer.dequantize(q, meta)

    # Forward conversion
    times_fwd = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        q, meta = quantizer.quantize(tensor, fmt)
        times_fwd.append(time.perf_counter() - t0)

    # Roundtrip
    times_rt = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        q, meta = quantizer.quantize(tensor, fmt)
        restored = quantizer.dequantize(q, meta)
        times_rt.append(time.perf_counter() - t0)

    # Error analysis
    q, meta = quantizer.quantize(tensor, fmt)
    restored = quantizer.dequantize(q, meta).reshape(tensor.shape)
    fp32 = tensor.astype(np.float32)
    abs_err = np.abs(fp32 - restored)
    denom = np.abs(fp32)
    denom = np.where(denom < 1e-12, 1.0, denom)

    fwd_ms = np.median(times_fwd) * 1000
    rt_ms = np.median(times_rt) * 1000
    tensor_bytes = tensor.nbytes
    wire_bytes = tensor.size * _BYTES_PER_ELEMENT[fmt]
    throughput = (tensor_bytes / (np.median(times_fwd))) * 8 / 1e9

    return ConversionResult(
        format=fmt.value,
        tensor_size=tensor_bytes,
        elements=tensor.size,
        convert_ms=fwd_ms,
        roundtrip_ms=rt_ms,
        throughput_gbps=throughput,
        max_abs_error=float(abs_err.max()),
        mean_rel_error=float((abs_err / denom).mean()),
        compression_ratio=4.0 / _BYTES_PER_ELEMENT[fmt],
    )


def run_benchmarks():
    """Run precision conversion benchmarks at multiple tensor sizes."""
    pm = PrecisionManager(RTX5070TI_PROFILE)
    quantizer = AdaptiveQuantizer(pm)

    # Tensor sizes representative of LLM operations
    sizes = {
        "4K (attention block)": (64, 64),
        "256K (small weight)": (512, 512),
        "1M (medium weight)": (1024, 1024),
        "4M (large weight)": (2048, 2048),
        "16M (KV cache block)": (4096, 4096),
    }

    formats = [
        PrecisionFormat.FP16,
        PrecisionFormat.BF16,
        PrecisionFormat.INT8,
        PrecisionFormat.MXFP4,
    ]

    rng = np.random.default_rng(42)

    print("=" * 90)
    print("RDMA Tensor Cache - Precision Conversion Benchmark")
    print("=" * 90)
    print(f"Device profile: {RTX5070TI_PROFILE.name}")
    print(f"Repeats per measurement: 20 (median reported)")
    print()

    for size_name, shape in sizes.items():
        tensor = rng.standard_normal(shape).astype(np.float32)
        print(f"--- {size_name}: shape={shape}, {tensor.nbytes / 1024:.0f} KB ---")
        print(f"{'Format':<8} {'Conv(ms)':>10} {'RT(ms)':>10} {'Gbps':>10} "
              f"{'MaxErr':>12} {'MeanRelErr':>12} {'Compress':>10}")

        for fmt in formats:
            result = benchmark_conversion(pm, quantizer, tensor, fmt)
            print(f"{result.format:<8} {result.convert_ms:>10.3f} "
                  f"{result.roundtrip_ms:>10.3f} {result.throughput_gbps:>10.1f} "
                  f"{result.max_abs_error:>12.6f} {result.mean_rel_error:>12.6f} "
                  f"{result.compression_ratio:>9.1f}x")
        print()

    # Stochastic rounding verification
    print("--- Stochastic Rounding Bias Test ---")
    test_val = 0.3
    tensor = np.full(100000, test_val, dtype=np.float32)
    n_trials = 50
    means = []
    for _ in range(n_trials):
        rounded = pm.stochastic_round(tensor, np.float16)
        means.append(float(rounded.astype(np.float32).mean()))
    overall_mean = np.mean(means)
    bias = abs(overall_mean - test_val)
    print(f"True value:      {test_val}")
    print(f"Mean of rounded: {overall_mean:.6f}")
    print(f"Bias:            {bias:.6f} ({'PASS' if bias < 0.001 else 'FAIL'})")
    print()

    # Optimal format selection
    print("--- Optimal Format Selection ---")
    for bw in [10.0, 25.0, 100.0]:
        for budget_ms in [0.1, 1.0, 10.0]:
            fmt = pm.optimal_format(
                tensor_bytes=4 * 1024 * 1024,
                bandwidth_gbps=bw,
                latency_budget_ms=budget_ms,
            )
            print(f"  BW={bw:>5.0f} Gbps, budget={budget_ms:>5.1f} ms -> {fmt.value}")


if __name__ == '__main__':
    run_benchmarks()
