"""
WFA (Work-First Adaptive) Classifier for dual QP pool routing.

Extends TensorClassifier with size-based routing and phase detection
to decide whether a transfer belongs on the hot (latency-sensitive)
or cold (throughput-optimized) QP pool.

Addresses UCX transport selection opacity issues:
  - #10652, #6511, #9364, #9560, #10608: Users can't control/observe
    transport selection. WFA makes the decision explicit and logged.

Also addresses protocol transition cliffs:
  - #10552: 50x latency cliff at eager->RNDV boundary
  - #10486: >32KB messages switch RDMA send->read
  - #10532: Latency drop at eager->zcopy transition (~30,000B)
  By routing explicitly based on size, we avoid UCX's heuristic cliffs.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .dual_qp_pool import QueueSelection


class Phase(Enum):
    """Inference phase detected from access patterns."""
    PREFILL = "prefill"
    DECODE = "decode"
    UNKNOWN = "unknown"


@dataclass
class ClassificationRecord:
    """A single classification decision for analysis."""
    tensor_id: str
    size_bytes: int
    queue: QueueSelection
    phase: Phase
    access_count: int
    timestamp: float


class WFAClassifier:
    """
    Work-First Adaptive classifier for QP pool routing.

    Size-based routing:
      - < hot_threshold (4KB): HOT_QP (latency-critical, attention scores, tokens)
      - > cold_threshold (256KB): COLD_QP (bulk KV cache, weight shards)
      - Between: use access pattern (frequent=HOT, infrequent=COLD)

    Phase detection:
      - Sequential layer sweep (L0, L1, L2, ...) = prefill phase
      - Repeated single-layer access = decode phase
      - Prefill biases toward COLD (large sequential), decode toward HOT
    """

    def __init__(self, hot_threshold: int = 4096,
                 cold_threshold: int = 262144,
                 hot_access_count: int = 10,
                 phase_window: int = 8):
        self._hot_threshold = hot_threshold
        self._cold_threshold = cold_threshold
        self._hot_access_count = hot_access_count
        self._phase_window = phase_window

        self._access_counts: Dict[str, int] = {}
        self._access_times: Dict[str, float] = {}
        self._recent_layers: List[int] = []
        self._current_phase = Phase.UNKNOWN
        self._history: List[ClassificationRecord] = []

    def classify(self, tensor_id: str, size_bytes: int,
                 layer_idx: Optional[int] = None) -> QueueSelection:
        """
        Classify a transfer and return the QP pool selection.

        Args:
            tensor_id: Unique tensor identifier.
            size_bytes: Transfer size in bytes.
            layer_idx: Optional layer index for phase detection.

        Returns:
            QueueSelection.HOT_QP or QueueSelection.COLD_QP
        """
        now = time.monotonic()

        # Update access tracking
        self._access_counts[tensor_id] = self._access_counts.get(tensor_id, 0) + 1
        self._access_times[tensor_id] = now
        count = self._access_counts[tensor_id]

        # Update phase detection
        if layer_idx is not None:
            self._update_phase(layer_idx)

        # Size-based routing (primary)
        if size_bytes < self._hot_threshold:
            queue = QueueSelection.HOT_QP
        elif size_bytes > self._cold_threshold:
            queue = QueueSelection.COLD_QP
        else:
            # Mid-range: use access frequency
            if count >= self._hot_access_count:
                queue = QueueSelection.HOT_QP
            else:
                queue = QueueSelection.COLD_QP

        # Phase adjustment
        if self._current_phase == Phase.PREFILL and queue == QueueSelection.HOT_QP:
            # During prefill, only truly small transfers stay hot
            if size_bytes > self._hot_threshold // 2:
                queue = QueueSelection.COLD_QP
        elif self._current_phase == Phase.DECODE and queue == QueueSelection.COLD_QP:
            # During decode, frequently accessed mid-range tensors go hot
            if count >= self._hot_access_count // 2:
                queue = QueueSelection.HOT_QP

        record = ClassificationRecord(
            tensor_id=tensor_id,
            size_bytes=size_bytes,
            queue=queue,
            phase=self._current_phase,
            access_count=count,
            timestamp=now,
        )
        self._history.append(record)

        return queue

    def _update_phase(self, layer_idx: int) -> None:
        """Detect inference phase from layer access pattern."""
        self._recent_layers.append(layer_idx)
        if len(self._recent_layers) > self._phase_window:
            self._recent_layers = self._recent_layers[-self._phase_window:]

        if len(self._recent_layers) < 3:
            return

        # Check for sequential sweep (prefill): L0, L1, L2, ...
        diffs = [
            self._recent_layers[i+1] - self._recent_layers[i]
            for i in range(len(self._recent_layers) - 1)
        ]
        if all(d == 1 for d in diffs):
            self._current_phase = Phase.PREFILL
        # Check for repeated single layer (decode)
        elif len(set(self._recent_layers[-3:])) == 1:
            self._current_phase = Phase.DECODE
        else:
            self._current_phase = Phase.UNKNOWN

    @property
    def phase(self) -> Phase:
        return self._current_phase

    @property
    def history(self) -> List[ClassificationRecord]:
        return self._history

    def get_stats(self) -> Dict:
        """Return classification statistics."""
        hot_count = sum(1 for r in self._history if r.queue == QueueSelection.HOT_QP)
        cold_count = sum(1 for r in self._history if r.queue == QueueSelection.COLD_QP)
        total = len(self._history)
        return {
            'total_classifications': total,
            'hot_count': hot_count,
            'cold_count': cold_count,
            'hot_ratio': hot_count / total if total > 0 else 0.0,
            'phase_distribution': {
                phase.value: sum(1 for r in self._history if r.phase == phase)
                for phase in Phase
            },
        }

    def reset(self) -> None:
        """Reset all state."""
        self._access_counts.clear()
        self._access_times.clear()
        self._recent_layers.clear()
        self._current_phase = Phase.UNKNOWN
        self._history.clear()
