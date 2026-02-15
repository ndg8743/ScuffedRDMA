"""Configuration presets for the RDMA tensor database."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .precision import PrecisionFormat


class TransportMode(Enum):
    MEMORY = "memory"
    TCP = "tcp"
    SOFTROCE = "softroce"
    HARDWARE = "hardware"


class PrefetchStrategy(Enum):
    NONE = "none"
    SEQUENTIAL = "sequential"
    STRIDED = "strided"
    LAYER_SWEEP = "layer_sweep"


@dataclass
class DatabaseConfig:
    """Configuration for the RDMA tensor database."""
    local_capacity: int = 4096
    local_capacity_bytes: int = 1 << 30  # 1 GB
    master_precision: PrecisionFormat = PrecisionFormat.FP32
    wire_precision: PrecisionFormat = PrecisionFormat.FP16
    enable_stochastic_rounding: bool = True
    prefetch_depth: int = 3
    prefetch_strategy: PrefetchStrategy = PrefetchStrategy.LAYER_SWEEP
    transport: TransportMode = TransportMode.TCP
    enable_delta_compression: bool = False

    @classmethod
    def v100_preset(cls) -> 'DatabaseConfig':
        """V100: FP16 wire, stochastic rounding, GPUDirect RDMA capable."""
        return cls(
            wire_precision=PrecisionFormat.FP16,
            enable_stochastic_rounding=True,
            prefetch_strategy=PrefetchStrategy.LAYER_SWEEP,
            transport=TransportMode.SOFTROCE,
        )

    @classmethod
    def rtx5070ti_preset(cls) -> 'DatabaseConfig':
        """RTX 5070 Ti: BF16 wire, no RDMA (Windows), TCP fallback."""
        return cls(
            wire_precision=PrecisionFormat.BF16,
            enable_stochastic_rounding=False,
            prefetch_strategy=PrefetchStrategy.SEQUENTIAL,
            transport=TransportMode.TCP,
        )

    @classmethod
    def heterogeneous_preset(cls) -> 'DatabaseConfig':
        """Mixed V100 + 5070 Ti: FP16 common denominator, layer sweep."""
        return cls(
            wire_precision=PrecisionFormat.FP16,
            enable_stochastic_rounding=True,
            prefetch_strategy=PrefetchStrategy.LAYER_SWEEP,
            transport=TransportMode.TCP,
            enable_delta_compression=True,
        )
