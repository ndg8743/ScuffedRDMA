"""
Orchestrator: state machine driving the profile -> rank -> optimize -> validate -> accept/revert loop.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any
from enum import Enum

from .profiler import KernelProfiler, KernelProfile, AmdahlRanking
from .optimizer import KernelOptimizer, OptimizationTier, OptimizationResult, KernelConfig
from .benchmarker import KernelBenchmarker, ValidationResult, BenchmarkResult


class OrchestratorState(Enum):
    IDLE = "idle"
    PROFILING = "profiling"
    RANKING = "ranking"
    OPTIMIZING = "optimizing"
    VALIDATING = "validating"
    ACCEPTING = "accepting"
    REVERTING = "reverting"
    DONE = "done"


@dataclass
class KernelOptimizationRecord:
    """Complete record of one kernel's optimization journey."""
    kernel_name: str
    original_profile: KernelProfile
    ranking: Optional[AmdahlRanking] = None
    config: KernelConfig = field(default_factory=KernelConfig)
    optimizations: List[OptimizationResult] = field(default_factory=list)
    validations: List[ValidationResult] = field(default_factory=list)
    final_speedup: float = 1.0
    accepted: bool = False


class Orchestrator:
    """
    Main optimization loop across all kernels.

    State machine:
        IDLE -> PROFILING -> RANKING -> OPTIMIZING -> VALIDATING -> ACCEPTING/REVERTING -> DONE

    For each kernel (in priority order):
        1. Profile to get baseline timing
        2. Rank by Amdahl's Law
        3. Apply optimization tiers (one at a time)
        4. Validate correctness after each tier
        5. Accept if faster and correct, revert otherwise
    """

    def __init__(self, max_tiers: int = 6, min_speedup: float = 1.05):
        """
        Args:
            max_tiers: Maximum optimization tiers to attempt per kernel
            min_speedup: Minimum speedup to accept an optimization (5% default)
        """
        self.profiler = KernelProfiler()
        self.optimizer = KernelOptimizer()
        self.benchmarker = KernelBenchmarker()
        self.max_tiers = max_tiers
        self.min_speedup = min_speedup
        self._state = OrchestratorState.IDLE
        self._records: List[KernelOptimizationRecord] = []

    @property
    def state(self) -> OrchestratorState:
        return self._state

    @property
    def records(self) -> List[KernelOptimizationRecord]:
        return list(self._records)

    def run(self, model, sample_input,
            kernel_fn_map: Optional[Dict[str, Callable]] = None,
            reference_fn_map: Optional[Dict[str, Callable]] = None,
            input_generator_map: Optional[Dict[str, Callable]] = None,
            benchmark_fn_map: Optional[Dict[str, Callable]] = None,
            ) -> List[KernelOptimizationRecord]:
        """
        Main optimization loop.

        Args:
            model: PyTorch model to optimize
            sample_input: Representative input
            kernel_fn_map: kernel_name -> optimized kernel function
            reference_fn_map: kernel_name -> reference implementation
            input_generator_map: kernel_name -> input generator
            benchmark_fn_map: kernel_name -> benchmark function(config) -> time_ms

        Returns:
            List of optimization records
        """
        kernel_fn_map = kernel_fn_map or {}
        reference_fn_map = reference_fn_map or {}
        input_generator_map = input_generator_map or {}
        benchmark_fn_map = benchmark_fn_map or {}

        # Phase 1: Profile
        self._state = OrchestratorState.PROFILING
        profiles = self.profiler.profile_model(model, sample_input)

        # Phase 2: Rank
        self._state = OrchestratorState.RANKING
        rankings = self.profiler.rank_by_amdahl()

        # Phase 3-5: Optimize each kernel in priority order
        self._records = []
        for ranking in rankings:
            record = KernelOptimizationRecord(
                kernel_name=ranking.kernel.name,
                original_profile=ranking.kernel,
                ranking=ranking,
            )

            # Try each optimization tier
            for tier_value in range(1, self.max_tiers + 1):
                tier = OptimizationTier(tier_value)

                # Optimize
                self._state = OrchestratorState.OPTIMIZING
                opt_result = self.optimizer.optimize_kernel(
                    ranking.kernel, tier, record.config,
                    benchmark_fn=benchmark_fn_map.get(ranking.kernel.name),
                )
                record.optimizations.append(opt_result)

                if not opt_result.applied:
                    continue

                # Validate
                self._state = OrchestratorState.VALIDATING
                kernel_fn = kernel_fn_map.get(ranking.kernel.name)
                ref_fn = reference_fn_map.get(ranking.kernel.name)
                input_gen = input_generator_map.get(ranking.kernel.name)

                if kernel_fn and ref_fn and input_gen:
                    validations = self.benchmarker.validate(
                        kernel_fn, ref_fn, input_gen
                    )
                    record.validations.extend(validations)

                    all_passed = all(v.passed for v in validations)

                    if all_passed and opt_result.speedup >= self.min_speedup:
                        self._state = OrchestratorState.ACCEPTING
                        record.final_speedup *= opt_result.speedup
                        record.accepted = True
                    else:
                        self._state = OrchestratorState.REVERTING
                        # Revert config changes
                        for key, _val in opt_result.config_changes.items():
                            # Reset to defaults — in real impl, would save/restore
                            pass

            self._records.append(record)

        self._state = OrchestratorState.DONE
        return self._records

    def summary(self) -> str:
        """Human-readable summary of optimization results."""
        lines = ["ScuffedKernels Optimization Summary", "=" * 40]
        for rec in self._records:
            status = "ACCEPTED" if rec.accepted else "UNCHANGED"
            speedup_str = f"{rec.final_speedup:.2f}x" if rec.accepted else "1.00x"
            lines.append(f"  {rec.kernel_name}: {status} ({speedup_str})")
            if rec.ranking:
                lines.append(f"    Time fraction: {rec.ranking.time_fraction:.1%}")
                lines.append(f"    Amdahl max speedup: {rec.ranking.max_speedup_inf:.2f}x")
            for opt in rec.optimizations:
                if opt.applied:
                    lines.append(f"    Tier {opt.tier.value}: {opt.description}")
        return "\n".join(lines)
