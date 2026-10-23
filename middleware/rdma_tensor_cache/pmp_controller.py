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

Storage arm (Update 6), decide_with_storage():
  Add GPU KV occupancy u in [0, 1] to the state and a running cost
  gamma * max(0, u - u0) for occupancy above a watermark u0. A third
  control u_S sends the transfer to the NVMe spill queue q_S (service
  rate mu_S), which is the only arm that lowers u. With the controls on
  the simplex u_H + u_C + u_S = 1, the Hamiltonian stays linear in them,
  so the optimum is still bang-bang: pick the arm with the smallest
  switching coefficient

    sigma_H = alpha * q_H * C * mu_H
    sigma_C = beta  * q_C * C * mu_C
    sigma_S = delta * q_S * mu_S - gamma * p,   p = max(0, u - u0) / (1 - u0)

  using the same costate approximation as the two-arm case (shadow
  price proportional to queue depth). With no pressure (u <= u0) the
  spill arm is never chosen and the result equals decide().
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

from .dual_qp_pool import QueueSelection


@dataclass
class SwitchEvent:
    """Record of a control switching event."""
    timestamp: float
    switching_function: float
    decision: QueueSelection
    hot_depth: int
    cold_depth: int


class StorageDecision(Enum):
    """Three-arm decision. Kept separate from QueueSelection so existing users are unaffected."""
    HOT = "hot"
    COLD = "cold"
    SPILL = "spill"

    @classmethod
    def from_queue(cls, q: QueueSelection) -> "StorageDecision":
        return cls.HOT if q == QueueSelection.HOT_QP else cls.COLD


@dataclass
class StorageSwitchEvent:
    """Record of a three-arm decision."""
    timestamp: float
    sigma_hot: float
    sigma_cold: float
    sigma_spill: float
    pressure: float
    decision: StorageDecision
    hot_depth: int
    cold_depth: int
    spill_depth: int
    gpu_mem_util: float


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
                 beta: float = 1.0, deadband: float = 0.1,
                 mu_spill: float = 500.0, delta: float = 1.0,
                 gamma: float = 50000.0, u0: float = 0.85):
        """mu_spill, delta, gamma, u0 only affect decide_with_storage()."""
        if not 0.0 <= u0 < 1.0:
            raise ValueError("u0 must be in [0, 1)")
        self._mu_spill = mu_spill
        self._delta = delta
        self._gamma = gamma
        self._u0 = u0
        self._last_storage: Optional[StorageDecision] = None
        self._storage_history: List[StorageSwitchEvent] = []
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

    def pressure(self, gpu_mem_util: float) -> float:
        """Normalized occupancy above the watermark, in [0, 1]."""
        u = min(max(float(gpu_mem_util), 0.0), 1.0)
        return max(0.0, u - self._u0) / (1.0 - self._u0)

    def decide_with_storage(self, hot_depth: int, cold_depth: int,
                            gpu_mem_util: float, spill_depth: int = 0) -> StorageDecision:
        """
        Three-arm bang-bang decision (hot / cold / spill). See module docstring.

        Below the watermark this defers to decide() so two-arm behavior is
        unchanged. Above it, the arm with the smallest switching coefficient
        wins; the previous storage decision is kept while its coefficient is
        within `deadband` of the minimum (hysteresis).
        """
        p = self.pressure(gpu_mem_util)
        s_h = self._alpha * hot_depth * self._capacity * self._mu_hot
        s_c = self._beta * cold_depth * self._capacity * self._mu_cold
        s_s = self._delta * spill_depth * self._mu_spill - self._gamma * p
        if p <= 0.0:
            decision = StorageDecision.from_queue(self.decide(hot_depth, cold_depth))
            s_s = float("inf")
        else:
            sig = {StorageDecision.HOT: s_h, StorageDecision.COLD: s_c, StorageDecision.SPILL: s_s}
            best = min(sig, key=lambda k: (sig[k], k.value))
            last = self._last_storage
            if last is not None and sig[last] - sig[best] <= self._deadband:
                decision = last
            else:
                decision = best
        self._storage_history.append(StorageSwitchEvent(
            timestamp=time.monotonic(), sigma_hot=s_h, sigma_cold=s_c, sigma_spill=s_s,
            pressure=p, decision=decision, hot_depth=hot_depth, cold_depth=cold_depth,
            spill_depth=spill_depth, gpu_mem_util=float(gpu_mem_util)))
        self._last_storage = decision
        return decision

    @property
    def storage_history(self) -> List[StorageSwitchEvent]:
        return self._storage_history

    def get_storage_stats(self) -> dict:
        h = self._storage_history
        out = {d.value: sum(1 for e in h if e.decision == d) for d in StorageDecision}
        out["total_decisions"] = len(h)
        out["max_pressure"] = max((e.pressure for e in h), default=0.0)
        return out

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
        self._last_storage = None
        self._storage_history.clear()
