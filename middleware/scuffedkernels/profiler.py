"""
Kernel profiling and Amdahl's Law ranking for RDMA-aware optimization.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import time

@dataclass
class KernelProfile:
    """Profile data for a single kernel."""
    name: str
    total_time_ms: float  # Wall-clock time for this kernel
    gpu_time_ms: float    # GPU-only time (excludes host overhead)
    memory_bytes: int     # Peak memory usage
    flops: int            # Estimated FLOPs
    call_count: int       # Number of invocations per forward pass
    is_rdma_bound: bool = False  # True if kernel waits on network

    @property
    def time_fraction(self) -> float:
        """Fraction of total model time spent in this kernel."""
        return self.gpu_time_ms  # Normalized externally by profiler

    @property
    def arithmetic_intensity(self) -> float:
        """FLOPs per byte - key roofline metric."""
        if self.memory_bytes == 0:
            return float('inf')
        return self.flops / self.memory_bytes


@dataclass
class AmdahlRanking:
    """Amdahl's Law ranking for kernel optimization priority."""
    kernel: KernelProfile
    time_fraction: float      # p in Amdahl's formula
    max_speedup_2x: float     # S(2) = 1/((1-p) + p/2)
    max_speedup_inf: float    # S(inf) = 1/(1-p)
    priority_score: float     # Combined ranking score


class KernelProfiler:
    """
    Profiles PyTorch models to identify optimization targets.
    Uses Amdahl's Law to rank kernels by potential speedup impact.

    S(n) = 1 / ((1-p) + p/n)
    where p = fraction of time in kernel, n = speedup factor
    """

    def __init__(self):
        self._profiles: List[KernelProfile] = []
        self._total_time_ms: float = 0.0

    def profile_model(self, model, sample_input, num_warmup: int = 3,
                      num_iterations: int = 10) -> List[KernelProfile]:
        """
        Profile a PyTorch model to extract per-kernel timing.

        Uses torch.profiler to capture CUDA kernel events, then aggregates
        by kernel name. Returns sorted list of KernelProfile objects.

        Args:
            model: PyTorch nn.Module
            sample_input: Representative input tensor/tuple
            num_warmup: Warmup iterations (not profiled)
            num_iterations: Profiled iterations

        Returns:
            List of KernelProfile, one per unique kernel
        """
        try:
            import torch
            from torch.profiler import profile, ProfilerActivity
        except ImportError:
            raise RuntimeError("PyTorch required for kernel profiling")

        # Warmup
        with torch.no_grad():
            for _ in range(num_warmup):
                if isinstance(sample_input, tuple):
                    model(*sample_input)
                else:
                    model(sample_input)

        # Profile
        kernel_times: Dict[str, List[float]] = {}
        kernel_memory: Dict[str, int] = {}

        with profile(
            activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
            record_shapes=True,
            profile_memory=True,
        ) as prof:
            with torch.no_grad():
                for _ in range(num_iterations):
                    if isinstance(sample_input, tuple):
                        model(*sample_input)
                    else:
                        model(sample_input)

        # Aggregate kernel events
        for event in prof.key_averages():
            if event.cuda_time_total > 0:
                name = event.key
                gpu_time = event.cuda_time_total / 1000.0  # us -> ms
                cpu_time = event.cpu_time_total / 1000.0

                if name not in kernel_times:
                    kernel_times[name] = []
                    kernel_memory[name] = 0

                kernel_times[name].append(gpu_time / num_iterations)
                kernel_memory[name] = max(
                    kernel_memory[name],
                    getattr(event, 'cuda_memory_usage', 0)
                )

        # Build profiles
        self._profiles = []
        self._total_time_ms = 0.0

        for name, times in kernel_times.items():
            avg_time = sum(times) / len(times) if times else 0.0
            p = KernelProfile(
                name=name,
                total_time_ms=avg_time,
                gpu_time_ms=avg_time,
                memory_bytes=kernel_memory.get(name, 0),
                flops=0,  # Estimated separately if needed
                call_count=len(times),
            )
            self._profiles.append(p)
            self._total_time_ms += avg_time

        return self._profiles

    def rank_by_amdahl(self, speedup_factor: float = 2.0) -> List[AmdahlRanking]:
        """
        Rank kernels by Amdahl's Law potential speedup.

        S(n) = 1 / ((1-p) + p/n)

        Kernels with highest time fraction p yield the greatest
        whole-program speedup when optimized.

        Args:
            speedup_factor: Assumed per-kernel speedup (default 2x)

        Returns:
            List of AmdahlRanking sorted by priority (highest first)
        """
        if not self._profiles or self._total_time_ms == 0:
            return []

        rankings = []
        for kernel in self._profiles:
            p = kernel.gpu_time_ms / self._total_time_ms

            # Amdahl's Law: S(n) = 1 / ((1-p) + p/n)
            s_nx = 1.0 / ((1.0 - p) + p / speedup_factor) if p < 1.0 else speedup_factor
            s_inf = 1.0 / (1.0 - p) if p < 1.0 else float('inf')

            # Priority: weight by both speedup potential and absolute time
            priority = (s_nx - 1.0) * kernel.gpu_time_ms

            rankings.append(AmdahlRanking(
                kernel=kernel,
                time_fraction=p,
                max_speedup_2x=s_nx,
                max_speedup_inf=s_inf,
                priority_score=priority,
            ))

        rankings.sort(key=lambda r: r.priority_score, reverse=True)
        return rankings

    def profile_rdma_pipeline(self, transfer_fn, tensor_sizes: List[int],
                               num_iterations: int = 50) -> List[KernelProfile]:
        """
        Profile RDMA transfer pipeline stages.

        Measures compute vs. network time to identify whether kernels
        are compute-bound or network-bound.

        Args:
            transfer_fn: Callable that performs an RDMA transfer of given size
            tensor_sizes: List of tensor sizes in bytes to profile
            num_iterations: Iterations per size

        Returns:
            KernelProfile for each pipeline stage
        """
        profiles = []

        for size in tensor_sizes:
            times = []
            for _ in range(num_iterations):
                start = time.perf_counter()
                transfer_fn(size)
                elapsed = (time.perf_counter() - start) * 1000  # ms
                times.append(elapsed)

            avg_time = sum(times) / len(times)
            profiles.append(KernelProfile(
                name=f"rdma_transfer_{size}B",
                total_time_ms=avg_time,
                gpu_time_ms=0.0,  # Network, not GPU
                memory_bytes=size,
                flops=0,
                call_count=num_iterations,
                is_rdma_bound=True,
            ))

        return profiles
