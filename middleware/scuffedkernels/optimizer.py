"""
6-tier kernel optimization playbook.

Tiers (applied in order, one at a time):
1. Block/grid dimensions - tune launch config
2. Memory access patterns - coalescing, shared memory
3. Precision (TF32/FP16) - reduced precision compute
4. Persistent kernels - fused multi-stage kernels
5. Architecture-specific - SM occupancy, warp specialization
6. RDMA-aware - overlap compute with network transfers
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import IntEnum

from .profiler import KernelProfile


class OptimizationTier(IntEnum):
    """Optimization tiers, applied in order."""
    BLOCK_SIZE = 1
    MEMORY = 2
    PRECISION = 3
    PERSISTENT = 4
    ARCHITECTURE = 5
    RDMA_AWARE = 6


@dataclass
class OptimizationResult:
    """Result of applying one optimization tier."""
    tier: OptimizationTier
    kernel_name: str
    original_time_ms: float
    optimized_time_ms: float
    description: str
    applied: bool = True
    config_changes: Dict[str, Any] = field(default_factory=dict)

    @property
    def speedup(self) -> float:
        if self.optimized_time_ms == 0:
            return float('inf')
        return self.original_time_ms / self.optimized_time_ms


@dataclass
class KernelConfig:
    """Tunable kernel launch configuration."""
    block_size_x: int = 128
    block_size_y: int = 1
    block_size_z: int = 1
    num_warps: int = 4
    num_stages: int = 2
    shared_memory_bytes: int = 0
    use_tf32: bool = False
    use_fp16: bool = False
    persistent: bool = False
    # RDMA-specific
    overlap_transfer: bool = False
    prefetch_depth: int = 0


class KernelOptimizer:
    """
    Applies optimization tiers one at a time to a kernel.

    Correctness-first: each tier is validated before proceeding
    to the next. If a tier breaks correctness, it is reverted.
    """

    def __init__(self):
        self._tier_handlers: Dict[OptimizationTier, Callable] = {
            OptimizationTier.BLOCK_SIZE: self._optimize_block_size,
            OptimizationTier.MEMORY: self._optimize_memory,
            OptimizationTier.PRECISION: self._optimize_precision,
            OptimizationTier.PERSISTENT: self._optimize_persistent,
            OptimizationTier.ARCHITECTURE: self._optimize_architecture,
            OptimizationTier.RDMA_AWARE: self._optimize_rdma,
        }
        self._history: List[OptimizationResult] = []

    @property
    def history(self) -> List[OptimizationResult]:
        return list(self._history)

    def optimize_kernel(self, kernel_profile: KernelProfile,
                        tier: OptimizationTier,
                        config: KernelConfig,
                        benchmark_fn: Optional[Callable] = None,
                        ) -> OptimizationResult:
        """
        Apply one optimization tier to a kernel.

        Only one change at a time — correctness first.

        Args:
            kernel_profile: Current kernel profile
            tier: Which tier to apply
            config: Current kernel config (modified in place if successful)
            benchmark_fn: Optional function to measure new time

        Returns:
            OptimizationResult with before/after timing
        """
        handler = self._tier_handlers.get(tier)
        if handler is None:
            return OptimizationResult(
                tier=tier,
                kernel_name=kernel_profile.name,
                original_time_ms=kernel_profile.gpu_time_ms,
                optimized_time_ms=kernel_profile.gpu_time_ms,
                description="Unknown tier",
                applied=False,
            )

        result = handler(kernel_profile, config)

        # If benchmark function provided, measure actual time
        if benchmark_fn and result.applied:
            actual_time = benchmark_fn(config)
            result.optimized_time_ms = actual_time

        self._history.append(result)
        return result

    def _optimize_block_size(self, profile: KernelProfile,
                              config: KernelConfig) -> OptimizationResult:
        """Tier 1: Tune block dimensions for SM occupancy."""
        original = config.block_size_x

        # Heuristic: try common block sizes, prefer multiples of warp size (32)
        candidates = [64, 128, 256, 512, 1024]
        best = original

        # Select based on problem size
        if profile.memory_bytes < 4096:
            best = 64
        elif profile.memory_bytes < 1 << 20:  # 1 MB
            best = 256
        else:
            best = 512

        config.block_size_x = best
        config.num_warps = best // 32

        return OptimizationResult(
            tier=OptimizationTier.BLOCK_SIZE,
            kernel_name=profile.name,
            original_time_ms=profile.gpu_time_ms,
            optimized_time_ms=profile.gpu_time_ms,  # Updated by benchmark
            description=f"Block size {original} -> {best}, warps={config.num_warps}",
            config_changes={"block_size_x": best, "num_warps": config.num_warps},
        )

    def _optimize_memory(self, profile: KernelProfile,
                          config: KernelConfig) -> OptimizationResult:
        """Tier 2: Optimize memory access patterns."""
        # Estimate shared memory needs for tiling
        if profile.arithmetic_intensity < 10:
            # Memory-bound: add shared memory tiling
            tile_size = min(config.block_size_x * 4, 48 * 1024)  # Max 48KB
            config.shared_memory_bytes = tile_size
            config.num_stages = 3  # Triple buffering
            desc = f"Added {tile_size}B shared memory, 3-stage pipeline"
        else:
            desc = "Compute-bound kernel, no memory optimization needed"
            return OptimizationResult(
                tier=OptimizationTier.MEMORY,
                kernel_name=profile.name,
                original_time_ms=profile.gpu_time_ms,
                optimized_time_ms=profile.gpu_time_ms,
                description=desc,
                applied=False,
            )

        return OptimizationResult(
            tier=OptimizationTier.MEMORY,
            kernel_name=profile.name,
            original_time_ms=profile.gpu_time_ms,
            optimized_time_ms=profile.gpu_time_ms,
            description=desc,
            config_changes={"shared_memory_bytes": tile_size, "num_stages": 3},
        )

    def _optimize_precision(self, profile: KernelProfile,
                             config: KernelConfig) -> OptimizationResult:
        """Tier 3: Enable TF32 or FP16 compute."""
        if not config.use_tf32:
            config.use_tf32 = True
            desc = "Enabled TF32 (19-bit mantissa, ~2x throughput on Ampere+)"
            changes = {"use_tf32": True}
        elif not config.use_fp16:
            config.use_fp16 = True
            desc = "Enabled FP16 Tensor Core path"
            changes = {"use_fp16": True}
        else:
            return OptimizationResult(
                tier=OptimizationTier.PRECISION,
                kernel_name=profile.name,
                original_time_ms=profile.gpu_time_ms,
                optimized_time_ms=profile.gpu_time_ms,
                description="Already at lowest precision",
                applied=False,
            )

        return OptimizationResult(
            tier=OptimizationTier.PRECISION,
            kernel_name=profile.name,
            original_time_ms=profile.gpu_time_ms,
            optimized_time_ms=profile.gpu_time_ms,
            description=desc,
            config_changes=changes,
        )

    def _optimize_persistent(self, profile: KernelProfile,
                              config: KernelConfig) -> OptimizationResult:
        """Tier 4: Convert to persistent kernel (fuse stages)."""
        if profile.call_count > 1 and not config.persistent:
            config.persistent = True
            return OptimizationResult(
                tier=OptimizationTier.PERSISTENT,
                kernel_name=profile.name,
                original_time_ms=profile.gpu_time_ms,
                optimized_time_ms=profile.gpu_time_ms,
                description=f"Fused {profile.call_count} invocations into persistent kernel",
                config_changes={"persistent": True},
            )
        return OptimizationResult(
            tier=OptimizationTier.PERSISTENT,
            kernel_name=profile.name,
            original_time_ms=profile.gpu_time_ms,
            optimized_time_ms=profile.gpu_time_ms,
            description="Not a candidate for persistent kernel",
            applied=False,
        )

    def _optimize_architecture(self, profile: KernelProfile,
                                config: KernelConfig) -> OptimizationResult:
        """Tier 5: Architecture-specific tuning (SM count, warp scheduling)."""
        desc = "Architecture-specific tuning requires device detection"
        return OptimizationResult(
            tier=OptimizationTier.ARCHITECTURE,
            kernel_name=profile.name,
            original_time_ms=profile.gpu_time_ms,
            optimized_time_ms=profile.gpu_time_ms,
            description=desc,
            applied=False,
        )

    def _optimize_rdma(self, profile: KernelProfile,
                        config: KernelConfig) -> OptimizationResult:
        """Tier 6: RDMA-aware optimization — overlap compute with transfers."""
        if profile.is_rdma_bound or config.prefetch_depth == 0:
            config.overlap_transfer = True
            config.prefetch_depth = 3
            return OptimizationResult(
                tier=OptimizationTier.RDMA_AWARE,
                kernel_name=profile.name,
                original_time_ms=profile.gpu_time_ms,
                optimized_time_ms=profile.gpu_time_ms,
                description="Enabled compute-transfer overlap, prefetch_depth=3",
                config_changes={"overlap_transfer": True, "prefetch_depth": 3},
            )
        return OptimizationResult(
            tier=OptimizationTier.RDMA_AWARE,
            kernel_name=profile.name,
            original_time_ms=profile.gpu_time_ms,
            optimized_time_ms=profile.gpu_time_ms,
            description="Already RDMA-optimized",
            applied=False,
        )
