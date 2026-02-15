#!/usr/bin/env python3
"""
End-to-end RDMA tensor cache benchmark.

Measures cache put/get throughput, serialize/deserialize overhead,
prefetch hit rates, and round-trip accuracy across precision formats.
"""

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from middleware.rdma_tensor_cache.precision import (
    PrecisionFormat, PrecisionManager, RTX5070TI_PROFILE, V100_PROFILE,
)
from middleware.rdma_tensor_cache.cache import RdmaTensorCache
from middleware.rdma_tensor_cache.prefetch import PrefetchEngine, AccessPattern
from middleware.rdma_tensor_cache.quantization import AdaptiveQuantizer
from middleware.rdma_tensor_cache.sae_steering import SAEFeatureStore, SparseVector, steer_model
from middleware.rdma_tensor_cache.vllm_connector import RDMAKVCacheConnector, KVCacheBlock


@dataclass
class CacheBenchResult:
    operation: str
    tensor_size: int
    wire_format: str
    ops_per_sec: float
    throughput_mbps: float
    avg_latency_us: float


def benchmark_cache_ops(wire_format: PrecisionFormat,
                        shape: tuple = (1024, 1024),
                        n_ops: int = 200) -> List[CacheBenchResult]:
    """Benchmark put/get/serialize cycle for a given wire format."""
    cache = RdmaTensorCache(
        device=RTX5070TI_PROFILE,
        wire_format=wire_format,
        enable_prefetch=False,
    )
    rng = np.random.default_rng(42)
    tensor = rng.standard_normal(shape).astype(np.float32)
    results = []

    # PUT benchmark
    times = []
    for i in range(n_ops):
        t0 = time.perf_counter()
        cache.put_tensor(f"bench_{i}", tensor)
        times.append(time.perf_counter() - t0)
    med = np.median(times)
    results.append(CacheBenchResult(
        operation="put",
        tensor_size=tensor.nbytes,
        wire_format=wire_format.value,
        ops_per_sec=1.0 / med,
        throughput_mbps=tensor.nbytes / med / 1e6,
        avg_latency_us=med * 1e6,
    ))

    # GET benchmark
    times = []
    for i in range(n_ops):
        t0 = time.perf_counter()
        cache.get_tensor(f"bench_{i % n_ops}", target_format=wire_format)
        times.append(time.perf_counter() - t0)
    med = np.median(times)
    results.append(CacheBenchResult(
        operation="get",
        tensor_size=tensor.nbytes,
        wire_format=wire_format.value,
        ops_per_sec=1.0 / med,
        throughput_mbps=tensor.nbytes / med / 1e6,
        avg_latency_us=med * 1e6,
    ))

    # SERIALIZE benchmark
    cache.put_tensor("ser_test", tensor)
    times = []
    for _ in range(n_ops):
        t0 = time.perf_counter()
        wire_data, meta = cache.serialize_for_wire("ser_test")
        times.append(time.perf_counter() - t0)
    med = np.median(times)
    results.append(CacheBenchResult(
        operation="serialize",
        tensor_size=tensor.nbytes,
        wire_format=wire_format.value,
        ops_per_sec=1.0 / med,
        throughput_mbps=tensor.nbytes / med / 1e6,
        avg_latency_us=med * 1e6,
    ))

    # DESERIALIZE benchmark
    wire_data, meta = cache.serialize_for_wire("ser_test")
    times = []
    for _ in range(n_ops):
        t0 = time.perf_counter()
        cache.deserialize_from_wire(wire_data, meta)
        times.append(time.perf_counter() - t0)
    med = np.median(times)
    results.append(CacheBenchResult(
        operation="deserialize",
        tensor_size=tensor.nbytes,
        wire_format=wire_format.value,
        ops_per_sec=1.0 / med,
        throughput_mbps=tensor.nbytes / med / 1e6,
        avg_latency_us=med * 1e6,
    ))

    return results


def benchmark_prefetch():
    """Benchmark prefetch engine pattern detection and hit rates."""
    engine = PrefetchEngine(prefetch_depth=4)

    # Sequential pattern
    for i in range(50):
        engine.record_access(f"layer_{i}")
    pattern = engine.classify_pattern()
    preds = engine.predict_next(3)
    print(f"  Sequential: pattern={pattern.value}, "
          f"predictions={preds}, hit_rate={engine.hit_rate:.2%}")

    # Strided pattern
    engine2 = PrefetchEngine(prefetch_depth=4)
    for i in range(0, 100, 3):
        engine2.record_access(f"weight_{i}")
    pattern = engine2.classify_pattern()
    preds = engine2.predict_next(3)
    print(f"  Strided:    pattern={pattern.value}, "
          f"predictions={preds}")

    # Layer sweep
    engine3 = PrefetchEngine(prefetch_depth=4)
    for sweep in range(3):
        for layer in range(8):
            engine3.record_access(f"attn_{layer}", layer_idx=layer)
    pattern = engine3.classify_pattern()
    print(f"  LayerSweep: pattern={pattern.value}")


def benchmark_gradient_accumulation():
    """Benchmark mixed-precision gradient application."""
    cache = RdmaTensorCache(device=V100_PROFILE, wire_format=PrecisionFormat.FP16)
    rng = np.random.default_rng(42)

    shape = (2048, 2048)
    weights = rng.standard_normal(shape).astype(np.float32)
    cache.put_tensor("model_weight", weights)

    n_steps = 100
    times = []
    for _ in range(n_steps):
        grad = rng.standard_normal(shape).astype(np.float16)
        t0 = time.perf_counter()
        cache.apply_gradient("model_weight", grad, lr=1e-4)
        times.append(time.perf_counter() - t0)

    med = np.median(times)
    print(f"  Gradient apply (FP16->FP32 accum): {med * 1e6:.1f} us, "
          f"{1.0/med:.0f} ops/sec")

    final = cache.get_tensor("model_weight")
    drift = np.abs(final - weights).mean()
    print(f"  Weight drift after {n_steps} steps: {drift:.6f}")


def benchmark_sae_features():
    """Benchmark SAE feature store operations."""
    store = SAEFeatureStore(feature_dim=4096)
    rng = np.random.default_rng(42)

    # Store sparse features
    n_features = 256
    times = []
    for i in range(n_features):
        direction = np.zeros(4096, dtype=np.float32)
        nnz = rng.integers(10, 100)
        indices = rng.choice(4096, nnz, replace=False)
        direction[indices] = rng.standard_normal(nnz).astype(np.float32)
        t0 = time.perf_counter()
        store.store_feature(layer=0, feature_idx=i, direction=direction)
        times.append(time.perf_counter() - t0)

    print(f"  Store: {np.median(times)*1e6:.1f} us/feature, "
          f"avg sparsity={store.avg_sparsity:.2%}")

    # Retrieve
    times = []
    for i in range(n_features):
        t0 = time.perf_counter()
        store.get_dense(0, i)
        times.append(time.perf_counter() - t0)
    print(f"  Retrieve: {np.median(times)*1e6:.1f} us/feature")

    # Steer
    activations = rng.standard_normal((128, 4096)).astype(np.float32)
    features = {0: 2.0, 5: -1.0, 10: 0.5}
    t0 = time.perf_counter()
    steered = steer_model(activations, features, store, layer=0)
    steer_time = time.perf_counter() - t0
    print(f"  Steer (128 tokens, 3 features): {steer_time*1e3:.2f} ms")


def benchmark_kv_connector():
    """Benchmark KV cache connector pack/unpack cycle."""
    cache = RdmaTensorCache(wire_format=PrecisionFormat.FP16)
    connector = RDMAKVCacheConnector(cache=cache)
    rng = np.random.default_rng(42)

    num_layers = 24
    num_heads = 16
    head_dim = 64
    seq_len = 512

    blocks = []
    for l in range(num_layers):
        blocks.append(KVCacheBlock(
            layer_idx=l,
            key_data=rng.standard_normal((num_heads, seq_len, head_dim)).astype(np.float32),
            value_data=rng.standard_normal((num_heads, seq_len, head_dim)).astype(np.float32),
            seq_len=seq_len,
        ))

    total_bytes = num_layers * 2 * num_heads * seq_len * head_dim * 4

    t0 = time.perf_counter()
    meta = connector.send_kv_cache("req_bench", blocks, num_heads, head_dim)
    send_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    received = connector.recv_kv_cache("req_bench", meta)
    recv_time = time.perf_counter() - t0

    print(f"  KV send ({num_layers} layers, {total_bytes/1e6:.1f} MB): "
          f"{send_time*1e3:.1f} ms")
    print(f"  KV recv: {recv_time*1e3:.1f} ms")
    print(f"  Throughput: {total_bytes / send_time / 1e9:.2f} GB/s (send), "
          f"{total_bytes / recv_time / 1e9:.2f} GB/s (recv)")


def main():
    print("=" * 80)
    print("RDMA Tensor Cache - End-to-End Benchmark")
    print("=" * 80)

    # Cache operations per format
    formats = [PrecisionFormat.FP16, PrecisionFormat.BF16,
               PrecisionFormat.INT8, PrecisionFormat.MXFP4]

    print("\n--- Cache Operations (1024x1024 FP32 tensor, 4 MB) ---")
    print(f"{'Op':<15} {'Format':<8} {'Ops/s':>10} {'MB/s':>10} {'Latency(us)':>12}")
    for fmt in formats:
        results = benchmark_cache_ops(fmt)
        for r in results:
            print(f"{r.operation:<15} {r.wire_format:<8} {r.ops_per_sec:>10.0f} "
                  f"{r.throughput_mbps:>10.0f} {r.avg_latency_us:>12.1f}")
        print()

    print("--- Prefetch Engine ---")
    benchmark_prefetch()
    print()

    print("--- Gradient Accumulation ---")
    benchmark_gradient_accumulation()
    print()

    print("--- SAE Feature Store ---")
    benchmark_sae_features()
    print()

    print("--- KV Cache Connector ---")
    benchmark_kv_connector()
    print()

    print("=" * 80)
    print("Benchmark complete.")


if __name__ == '__main__':
    main()