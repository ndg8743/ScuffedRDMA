"""
MUTABLE optimization file — the ONLY file agents should modify.

Contains tunable hyperparameters and the optimization function.
All changes are tracked via git for experiment reproducibility.
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class WireFormat(Enum):
    """Wire format for tensor transfers."""
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"


class TransportMode(Enum):
    """Transport backend selection."""
    TCP = "tcp"
    SOFTROCE = "softroce"
    HARDWARE_ROCE = "hardware_roce"


# ============================================================================
# TUNABLE PARAMETERS — Agents modify these values
# ============================================================================

TUNABLE_PARAMS = {
    "BATCH_SIZE": 64,            # Number of tensors per batch transfer
    "QP_DEPTH": 16,              # Queue pair send/recv depth
    "PREFETCH_DEPTH": 3,         # Layers to prefetch ahead
    "WIRE_FORMAT": WireFormat.FP16,
    "TRANSPORT_MODE": TransportMode.SOFTROCE,
    "BUFFER_POOL_SIZE": 8,       # Pre-registered RDMA buffers
    "MAX_INLINE_BYTES": 256,     # Inline data threshold
    "CONGESTION_WINDOW": 32,     # Outstanding RDMA ops before backpressure
    "RETRY_COUNT": 3,            # RDMA retry on timeout
    "USE_ADAPTIVE_ROUTING": False,
}


@dataclass
class TransferConfig:
    """Transfer configuration derived from tunable params."""
    batch_size: int = TUNABLE_PARAMS["BATCH_SIZE"]
    qp_depth: int = TUNABLE_PARAMS["QP_DEPTH"]
    prefetch_depth: int = TUNABLE_PARAMS["PREFETCH_DEPTH"]
    wire_format: WireFormat = TUNABLE_PARAMS["WIRE_FORMAT"]
    transport_mode: TransportMode = TUNABLE_PARAMS["TRANSPORT_MODE"]
    buffer_pool_size: int = TUNABLE_PARAMS["BUFFER_POOL_SIZE"]
    max_inline_bytes: int = TUNABLE_PARAMS["MAX_INLINE_BYTES"]
    congestion_window: int = TUNABLE_PARAMS["CONGESTION_WINDOW"]
    retry_count: int = TUNABLE_PARAMS["RETRY_COUNT"]
    use_adaptive_routing: bool = TUNABLE_PARAMS["USE_ADAPTIVE_ROUTING"]


class RDMAOptimizer:
    """
    Optimization function that agents modify to improve RDMA performance.

    The optimize_rdma_transfer method is the main entry point.
    Agents should modify the logic here and the TUNABLE_PARAMS above.
    """

    def __init__(self, config: Optional[TransferConfig] = None):
        self.config = config or TransferConfig()

    def optimize_rdma_transfer(self, data: bytes) -> bytes:
        """
        Apply optimizations to an RDMA transfer.

        This is the function agents optimize. The prepare.py harness
        calls this and measures performance.

        Args:
            data: Raw tensor data to transfer

        Returns:
            Transferred data (possibly transformed)
        """
        # Step 1: Batch if beneficial
        if len(data) > self.config.max_inline_bytes:
            data = self._batch_transfer(data)

        # Step 2: Apply wire format compression
        data = self._apply_wire_format(data)

        # Step 3: Simulate transfer with current config
        data = self._transfer(data)

        return data

    def _batch_transfer(self, data: bytes) -> bytes:
        """Split large transfers into batches for pipeline overlap."""
        # Current strategy: pass through (agents can add batching logic)
        return data

    def _apply_wire_format(self, data: bytes) -> bytes:
        """Apply wire format transformation."""
        # Placeholder: in real impl, would convert tensor precision
        return data

    def _transfer(self, data: bytes) -> bytes:
        """Execute the transfer with current settings."""
        # Placeholder: in real impl, would use actual transport
        return data
