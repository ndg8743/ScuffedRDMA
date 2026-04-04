"""
PMP (Pontryagin's Maximum Principle) Bang-Bang Controller.

Implements optimal control for the dual QP pool: given queue depths
of hot and cold pools, decides whether to shift the next transfer
to the hot pool (u=1) or cold pool (u=0) using a bang-bang switching
function derived from PMP.

The switching function:
  S = lambda_qH * C * mu_H - lambda_qC * C * mu_C

where:
  lambda_qH, lambda_qC = costate variables (shadow prices of queue depths)
  C = link capacity (constant for a given NIC)
  mu_H, mu_C = service rates for hot/cold pools

When S > 0: hot is congested, allocate to cold (u=0)
When S < 0: cold is congested, allocate to hot (u=1)
"""

import time
from dataclasses import dataclass, field
from typing import List, Tuple

from .dual_qp_pool import QueueSelection


@dataclass
class SwitchEvent:
    """Record of a control switching event."""
    timestamp: float
    switching_function: float
    decision: QueueSelection
    hot_depth: int
    cold_depth: int


class PMPController:
    """
    Bang-bang controller for dual QP pool scheduling.

    Parameters:
        mu_hot: Service rate of hot pool (ops/sec). Higher = faster drain.
        mu_cold: Service rate of cold pool (ops/sec).
        capacity: Link capacity constant C (normalized, default 1.0).
        alpha: Weight for hot queue cost (higher = more aggressive hot draining).
        beta: Weight for cold queue cost.
        deadband: Hysteresis width around S=0 to prevent chattering.
    """

    def __init__(self, mu_hot: float = 10000.0, mu_cold: float = 2000.0,
                 capacity: float = 1.0, alpha: float = 2.0,
                 beta: float = 1.0, deadband: float = 0.1):
        self._mu_hot = mu_hot
        self._mu_cold = mu_cold
        self._capacity = capacity
        self._alpha = alpha
        self._beta = beta
        self._deadband = deadband

        self._last_decision = QueueSelection.COLD_QP
        self._history: List[SwitchEvent] = []

    def decide(self, hot_depth: int, cold_depth: int) -> QueueSelection:
        """
        Compute the bang-bang control decision.

        The costate variables are approximated by queue depths weighted
        by alpha/beta: deeper queues have higher shadow cost.

        Args:
            hot_depth: Current outstanding operations on hot pool.
            cold_depth: Current outstanding operations on cold pool.

        Returns:
            QueueSelection indicating which pool to use.
        """
        # Costate approximation: lambda_qH ~ alpha * hot_depth,
        # lambda_qC ~ beta * cold_depth
        lambda_h = self._alpha * hot_depth
        lambda_c = self._beta * cold_depth

        # Switching function
        S = lambda_h * self._capacity * self._mu_hot \
            - lambda_c * self._capacity * self._mu_cold

        # Bang-bang with deadband for hysteresis
        if S > self._deadband:
            # Hot pool is congested relative to cold: send to cold
            decision = QueueSelection.COLD_QP
        elif S < -self._deadband:
            # Cold pool is congested relative to hot: send to hot
            decision = QueueSelection.HOT_QP
        else:
            # Within deadband: maintain last decision
            decision = self._last_decision

        event = SwitchEvent(
            timestamp=time.monotonic(),
            switching_function=S,
            decision=decision,
            hot_depth=hot_depth,
            cold_depth=cold_depth,
        )
        self._history.append(event)
        self._last_decision = decision
        return decision

    @property
    def history(self) -> List[SwitchEvent]:
        return self._history

    def get_stats(self) -> dict:
        """Return controller switching statistics."""
        if not self._history:
            return {
                'total_decisions': 0,
                'hot_decisions': 0,
                'cold_decisions': 0,
                'switches': 0,
                'avg_switching_fn': 0.0,
            }

        hot_count = sum(
            1 for e in self._history if e.decision == QueueSelection.HOT_QP
        )
        cold_count = len(self._history) - hot_count

        switches = sum(
            1 for i in range(1, len(self._history))
            if self._history[i].decision != self._history[i-1].decision
        )

        avg_s = sum(e.switching_function for e in self._history) / len(self._history)

        return {
            'total_decisions': len(self._history),
            'hot_decisions': hot_count,
            'cold_decisions': cold_count,
            'switches': switches,
            'avg_switching_fn': avg_s,
        }

    def reset(self) -> None:
        """Reset controller state."""
        self._last_decision = QueueSelection.COLD_QP
        self._history.clear()
