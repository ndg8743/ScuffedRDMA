"""
IMMUTABLE evaluation harness for RDMA optimization experiments.

This file defines the topology, metrics, benchmark harness, and scoring.
Agents MUST NOT modify this file — only optimize.py is mutable.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import time
import numpy as np


@dataclass(frozen=True)
class NetworkTopology:
    """Frozen description of the physical network — cannot be changed by agents."""
    link_bandwidth_gbps: float = 100.0    # 100GbE
    link_latency_us: float = 2.0          # Hardware RoCE baseline
    mtu_bytes: int = 4096                 # RoCE v2 MTU
    max_qps: int = 1024                   # ConnectX-4 limit
    num_gpus_tower1: int = 1              # RTX 5070 Ti
    num_gpus_tower2: int = 2              # 2x Tesla V100
    gpu_memory_tower1_gb: float = 16.0
    gpu_memory_tower2_gb: float = 32.0
    # SoftRoCEv2 baseline (measured, not targets)
    softroce_latency_us: float = 190.0
    softroce_bandwidth_gbps: float = 8.0


@dataclass
class RDMAMetrics:
    """Measured RDMA performance metrics for a single experiment."""
    throughput_gbps: float = 0.0
    latency_us: float = 0.0
    cpu_utilization: float = 0.0
    gpu_utilization: float = 0.0
    transfer_size_bytes: int = 0
    qp_depth: int = 0
    # Derived
    bandwidth_efficiency: float = 0.0  # throughput / link_bandwidth

    def compute_efficiency(self, topology: NetworkTopology) -> None:
        """Compute derived metrics from raw measurements."""
        if topology.link_bandwidth_gbps > 0:
            self.bandwidth_efficiency = self.throughput_gbps / topology.link_bandwidth_gbps


@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run."""
    transfer_sizes: List[int] = field(default_factory=lambda: [
        1024, 4096, 16384, 65536, 262144, 1048576, 4194304, 16777216
    ])
    num_iterations: int = 100
    num_warmup: int = 10
    timeout_seconds: float = 300.0


class BenchmarkHarness:
    """
    Evaluation harness for RDMA optimization experiments.

    Provides standardized measurement and scoring. The harness
    is immutable — agents optimize via optimize.py only.
    """

    def __init__(self, topology: Optional[NetworkTopology] = None,
                 config: Optional[BenchmarkConfig] = None):
        self.topology = topology or NetworkTopology()
        self.config = config or BenchmarkConfig()
        self._results: List[RDMAMetrics] = []

    @property
    def results(self) -> List[RDMAMetrics]:
        return list(self._results)

    def evaluate(self, transfer_fn, transfer_size: int,
                 num_iterations: Optional[int] = None) -> RDMAMetrics:
        """
        Evaluate a transfer function's performance.

        Args:
            transfer_fn: Callable(data: bytes) -> bytes or None
            transfer_size: Size of data to transfer
            num_iterations: Override default iteration count

        Returns:
            RDMAMetrics with measured performance
        """
        iterations = num_iterations or self.config.num_iterations
        data = bytes(transfer_size)

        # Warmup
        for _ in range(self.config.num_warmup):
            transfer_fn(data)

        # Measure
        latencies = []
        total_bytes = 0

        start_wall = time.perf_counter()
        for _ in range(iterations):
            t0 = time.perf_counter()
            transfer_fn(data)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1e6)  # seconds -> us
            total_bytes += transfer_size
        elapsed = time.perf_counter() - start_wall

        metrics = RDMAMetrics(
            throughput_gbps=(total_bytes * 8) / (elapsed * 1e9) if elapsed > 0 else 0.0,
            latency_us=float(np.median(latencies)) if latencies else 0.0,
            transfer_size_bytes=transfer_size,
        )
        metrics.compute_efficiency(self.topology)
        self._results.append(metrics)
        return metrics

    def evaluate_sweep(self, transfer_fn) -> List[RDMAMetrics]:
        """
        Evaluate across all configured transfer sizes.

        Args:
            transfer_fn: Callable(data: bytes) -> bytes or None

        Returns:
            List of RDMAMetrics, one per transfer size
        """
        results = []
        for size in self.config.transfer_sizes:
            metrics = self.evaluate(transfer_fn, size)
            results.append(metrics)
        return results

    def score(self, metrics: RDMAMetrics) -> float:
        """
        Compute a single scalar score for an experiment.

        Score = throughput_efficiency * latency_factor

        Higher is better. Normalized to [0, 1] range.

        Args:
            metrics: Measured performance

        Returns:
            Scalar score in [0, 1]
        """
        # Throughput component: fraction of line rate
        throughput_score = min(
            metrics.throughput_gbps / self.topology.link_bandwidth_gbps, 1.0
        ) if self.topology.link_bandwidth_gbps > 0 else 0.0

        # Latency component: how close to hardware RoCE baseline
        if metrics.latency_us > 0:
            latency_ratio = self.topology.link_latency_us / metrics.latency_us
            latency_score = min(latency_ratio, 1.0)
        else:
            latency_score = 0.0

        # Combined score (geometric mean)
        if throughput_score > 0 and latency_score > 0:
            return (throughput_score * latency_score) ** 0.5
        return 0.0

    def reset(self) -> None:
        """Clear stored results."""
        self._results = []
