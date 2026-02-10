"""
RDMA Tensor Cache.

Central cache layer wrapping transport + precision management.
Maintains master weights in FP32 while transferring tensors in
configurable wire format over RDMA or TCP-simulated transport.
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np

from .precision import PrecisionFormat, PrecisionManager, DeviceProfile
from .quantization import AdaptiveQuantizer, QuantizationMeta
from .prefetch import PrefetchEngine


@dataclass
class CacheEntry:
    """Single tensor in the cache."""
    key: str
    data: np.ndarray
    version: int = 0
    wire_format: PrecisionFormat = PrecisionFormat.FP16
    last_access: float = field(default_factory=time.monotonic)
    checksum: str = ""


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    puts: int = 0
    evictions: int = 0
    bytes_transferred: int = 0
    prefetch_hits: int = 0
    prefetch_misses: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    @property
    def prefetch_hit_rate(self) -> float:
        total = self.prefetch_hits + self.prefetch_misses
        return self.prefetch_hits / total if total > 0 else 0.0


class RdmaTensorCache:
    """
    Tensor cache with RDMA-optimized transfers.

    Stores master weights in FP32, converts to wire format for
    transport, and applies incoming gradients with precision-aware
    accumulation.
    """

    def __init__(self, transport: Any = None,
                 device: Optional[DeviceProfile] = None,
                 wire_format: PrecisionFormat = PrecisionFormat.FP16,
                 max_entries: int = 4096,
                 enable_prefetch: bool = True):
        """
        Args:
            transport: Transport backend (PyverbsTransport or TcpSimTransport).
            device: Device profile for precision decisions.
            wire_format: Default wire format for transfers.
            max_entries: Maximum cache entries before eviction.
            enable_prefetch: Enable predictive prefetching.
        """
        self._transport = transport
        self._precision = PrecisionManager(device)
        self._quantizer = AdaptiveQuantizer(self._precision)
        self._wire_format = wire_format
        self._max_entries = max_entries
        self._store: Dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._prefetch = PrefetchEngine() if enable_prefetch else None

    @property
    def stats(self) -> CacheStats:
        return self._stats

    @property
    def wire_format(self) -> PrecisionFormat:
        return self._wire_format

    @wire_format.setter
    def wire_format(self, fmt: PrecisionFormat) -> None:
        self._wire_format = fmt

    def put_tensor(self, key: str, tensor: np.ndarray,
                   wire_format: Optional[PrecisionFormat] = None) -> None:
        """
        Store a tensor in the cache.

        Master copy is kept in FP32. The wire_format determines how it
        will be serialized for RDMA transfer.

        Args:
            key: Unique tensor identifier.
            tensor: Tensor data (any precision, stored as FP32).
            wire_format: Override default wire format for this entry.
        """
        fp32 = tensor.astype(np.float32)
        checksum = hashlib.md5(fp32.tobytes()).hexdigest()[:8]

        if key in self._store:
            entry = self._store[key]
            entry.data = fp32
            entry.version += 1
            entry.wire_format = wire_format or self._wire_format
            entry.last_access = time.monotonic()
            entry.checksum = checksum
        else:
            if len(self._store) >= self._max_entries:
                self._evict()
            self._store[key] = CacheEntry(
                key=key,
                data=fp32,
                wire_format=wire_format or self._wire_format,
                checksum=checksum,
            )

        self._stats.puts += 1

    def get_tensor(self, key: str,
                   target_format: Optional[PrecisionFormat] = None,
                   layer_idx: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Retrieve a tensor, optionally converting to target precision.

        Args:
            key: Tensor identifier.
            target_format: Desired output format (None = FP32 master copy).
            layer_idx: Layer index hint for prefetch engine.

        Returns:
            Tensor in requested format, or None if not found.
        """
        if self._prefetch:
            was_prefetch_hit = key in self._prefetch._prefetched
            self._prefetch.record_access(key, layer_idx)
            if was_prefetch_hit:
                self._stats.prefetch_hits += 1
            else:
                self._stats.prefetch_misses += 1

        entry = self._store.get(key)
        if entry is None:
            self._stats.misses += 1
            return None

        self._stats.hits += 1
        entry.last_access = time.monotonic()

        if self._prefetch:
            self._prefetch_next(target_format)

        if target_format is None or target_format == PrecisionFormat.FP32:
            return entry.data.copy()

        return self._precision.convert(entry.data, target_format)

    def apply_gradient(self, key: str, gradient: np.ndarray,
                       lr: float = 1e-3) -> bool:
        """
        Apply a gradient update to master weights in FP32.

        Args:
            key: Tensor identifier.
            gradient: Gradient tensor (any precision, upcast to FP32).
            lr: Learning rate.

        Returns:
            True if the update was applied.
        """
        entry = self._store.get(key)
        if entry is None:
            return False

        grad_fp32 = gradient.astype(np.float32)
        entry.data -= lr * grad_fp32
        entry.version += 1
        entry.checksum = hashlib.md5(entry.data.tobytes()).hexdigest()[:8]
        return True

    def serialize_for_wire(self, key: str) -> Optional[Tuple[bytes, QuantizationMeta]]:
        """
        Serialize a cached tensor for RDMA transfer.

        Args:
            key: Tensor identifier.

        Returns:
            (wire_bytes, metadata) or None if key not found.
        """
        entry = self._store.get(key)
        if entry is None:
            return None

        quantized, meta = self._quantizer.quantize(entry.data, entry.wire_format)
        wire_bytes = quantized.tobytes()
        self._stats.bytes_transferred += len(wire_bytes)
        return wire_bytes, meta

    def deserialize_from_wire(self, wire_bytes: bytes,
                              meta: QuantizationMeta) -> np.ndarray:
        """
        Reconstruct a tensor from wire data.

        Args:
            wire_bytes: Raw bytes from transport.
            meta: Quantization metadata.

        Returns:
            FP32 tensor.
        """
        if meta.format == PrecisionFormat.BF16:
            data = np.frombuffer(wire_bytes, dtype=np.uint16)
        elif meta.format == PrecisionFormat.INT8:
            data = np.frombuffer(wire_bytes, dtype=np.int8)
        elif meta.format == PrecisionFormat.MXFP4:
            data = np.frombuffer(wire_bytes, dtype=np.uint8)
        elif meta.format == PrecisionFormat.FP16:
            data = np.frombuffer(wire_bytes, dtype=np.float16)
        else:
            data = np.frombuffer(wire_bytes, dtype=np.float32)

        return self._quantizer.dequantize(data, meta)

    def _prefetch_next(self, target_format: Optional[PrecisionFormat] = None) -> None:
        """Pre-warm cache for predicted next tensors via transport."""
        if not self._prefetch or not self._transport:
            return

        predictions = self._prefetch.predict_next()
        for pred_key in predictions:
            if pred_key in self._store:
                continue
            try:
                data = self._transport.fetch(pred_key)
                if data is not None:
                    self.put_tensor(pred_key, data)
                    self._prefetch._prefetched.add(pred_key)
            except Exception:
                pass

    @property
    def prefetch_stats(self) -> Optional[Dict[str, float]]:
        if not self._prefetch:
            return None
        return {
            **self._prefetch.stats,
            "cache_prefetch_hits": self._stats.prefetch_hits,
            "cache_prefetch_misses": self._stats.prefetch_misses,
            "cache_prefetch_hit_rate": self._stats.prefetch_hit_rate,
        }

    def _evict(self) -> None:
        """Evict least-recently-used entry."""
        if not self._store:
            return
        lru_key = min(self._store, key=lambda k: self._store[k].last_access)
        del self._store[lru_key]
        self._stats.evictions += 1

    def keys(self):
        return self._store.keys()

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: str) -> bool:
        return key in self._store