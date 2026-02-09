"""
Prefetch engine for RDMA tensor cache.

Tracks tensor access patterns and predicts upcoming fetches to hide
RDMA transfer latency behind computation. Uses ring buffer history
with stride and layer-sweep detection.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Awaitable, Dict, List, Optional, Set


class AccessPattern(Enum):
    Sequential = "sequential"
    Strided = "strided"
    LayerSweep = "layer_sweep"
    Random = "random"


@dataclass
class AccessRecord:
    key: str
    timestamp: float
    layer_idx: Optional[int] = None


class RingBuffer:
    """Fixed-size ring buffer for access history."""

    def __init__(self, capacity: int = 1024):
        self._buf: List[Optional[AccessRecord]] = [None] * capacity
        self._cap = capacity
        self._head = 0
        self._size = 0

    def append(self, record: AccessRecord) -> None:
        self._buf[self._head] = record
        self._head = (self._head + 1) % self._cap
        self._size = min(self._size + 1, self._cap)

    def recent(self, n: int) -> List[AccessRecord]:
        n = min(n, self._size)
        result = []
        idx = (self._head - n) % self._cap
        for _ in range(n):
            result.append(self._buf[idx])
            idx = (idx + 1) % self._cap
        return result

    def __len__(self) -> int:
        return self._size


class PrefetchEngine:
    """
    Predictive prefetch engine for tensor cache.

    Records access patterns and issues asynchronous prefetch requests
    to overlap RDMA transfers with GPU computation.
    """

    def __init__(self, history_size: int = 1024, prefetch_depth: int = 3,
                 min_confidence: float = 0.6):
        self._history = RingBuffer(history_size)
        self._prefetch_depth = prefetch_depth
        self._min_confidence = min_confidence

        # Pattern tracking
        self._key_sequence: List[str] = []
        self._stride_table: Dict[str, int] = {}
        self._layer_order: List[str] = []
        self._layer_set: Set[str] = set()
        self._sweep_count = 0

        # Stats
        self._hits = 0
        self._misses = 0
        self._prefetched: Set[str] = set()
        self._running = False

    def record_access(self, key: str, layer_idx: Optional[int] = None) -> None:
        """Record a tensor access for pattern detection."""
        record = AccessRecord(key=key, timestamp=time.monotonic(), layer_idx=layer_idx)
        self._history.append(record)
        self._key_sequence.append(key)

        if key in self._prefetched:
            self._hits += 1
            self._prefetched.discard(key)
        else:
            self._misses += 1

        self._update_stride(key)
        self._update_layer_sweep(key, layer_idx)

    def _update_stride(self, key: str) -> None:
        seq = self._key_sequence
        if len(seq) < 3:
            return
        # Detect numeric suffixes for stride computation
        try:
            nums = [int(k.rsplit('_', 1)[-1]) for k in seq[-3:]]
        except (ValueError, IndexError):
            return
        d1 = nums[1] - nums[0]
        d2 = nums[2] - nums[1]
        if d1 == d2 and d1 != 0:
            prefix = key.rsplit('_', 1)[0]
            self._stride_table[prefix] = d1

    def _update_layer_sweep(self, key: str, layer_idx: Optional[int]) -> None:
        if layer_idx is None:
            return
        lkey = f"L{layer_idx}:{key}"
        if lkey in self._layer_set:
            self._sweep_count += 1
            self._layer_set.clear()
            self._layer_order.clear()
        self._layer_set.add(lkey)
        self._layer_order.append(key)

    def classify_pattern(self) -> AccessPattern:
        """Classify the dominant access pattern from recent history."""
        if self._sweep_count >= 2:
            return AccessPattern.LayerSweep

        if self._stride_table:
            return AccessPattern.Strided

        recent = self._history.recent(min(32, len(self._history)))
        if len(recent) < 3:
            return AccessPattern.Random

        # Check for sequential numeric keys
        try:
            nums = [int(r.key.rsplit('_', 1)[-1]) for r in recent]
            diffs = [nums[i+1] - nums[i] for i in range(len(nums) - 1)]
            if len(set(diffs)) == 1 and diffs[0] == 1:
                return AccessPattern.Sequential
            if len(set(diffs)) == 1 and diffs[0] != 0:
                return AccessPattern.Strided
        except (ValueError, IndexError):
            pass

        return AccessPattern.Random

    def predict_next(self, count: Optional[int] = None) -> List[str]:
        """
        Predict the next tensor keys to be accessed.

        Args:
            count: Number of predictions (defaults to prefetch_depth).

        Returns:
            List of predicted tensor keys.
        """
        count = count or self._prefetch_depth
        pattern = self.classify_pattern()

        if pattern == AccessPattern.Sequential:
            return self._predict_sequential(count)
        elif pattern == AccessPattern.Strided:
            return self._predict_strided(count)
        elif pattern == AccessPattern.LayerSweep:
            return self._predict_layer_sweep(count)
        return []

    def _predict_sequential(self, count: int) -> List[str]:
        if not self._key_sequence:
            return []
        last = self._key_sequence[-1]
        try:
            prefix, num_str = last.rsplit('_', 1)
            num = int(num_str)
            return [f"{prefix}_{num + i + 1}" for i in range(count)]
        except (ValueError, IndexError):
            return []

    def _predict_strided(self, count: int) -> List[str]:
        if not self._key_sequence:
            return []
        last = self._key_sequence[-1]
        try:
            prefix, num_str = last.rsplit('_', 1)
            num = int(num_str)
            stride = self._stride_table.get(prefix, 1)
            return [f"{prefix}_{num + stride * (i + 1)}" for i in range(count)]
        except (ValueError, IndexError):
            return []

    def _predict_layer_sweep(self, count: int) -> List[str]:
        if not self._layer_order:
            return []
        # Replay recorded layer order
        return self._layer_order[:count]

    async def prefetch_loop(self, fetch_fn: Callable[[str], Awaitable[None]],
                            interval: float = 0.001) -> None:
        """
        Background loop that issues prefetch requests.

        Args:
            fetch_fn: Async callable that fetches a tensor by key.
            interval: Seconds between prediction cycles.
        """
        self._running = True
        while self._running:
            predictions = self.predict_next()
            for key in predictions:
                if key not in self._prefetched:
                    try:
                        await fetch_fn(key)
                        self._prefetched.add(key)
                    except Exception:
                        pass
            await asyncio.sleep(interval)

    def stop(self) -> None:
        self._running = False

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> Dict[str, float]:
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
            "pattern": self.classify_pattern().value,
            "history_size": len(self._history),
        }
