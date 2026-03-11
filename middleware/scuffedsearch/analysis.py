"""
Experiment tracking, contribution analysis, and visualization.

Records experiment outcomes (KEEP/DISCARD/CRASH) and provides
analysis of what optimizations contributed to improvements.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import json


class ExperimentOutcome(Enum):
    KEEP = "keep"       # Improvement over baseline
    DISCARD = "discard" # No improvement or regression
    CRASH = "crash"     # Experiment failed to complete


@dataclass
class ExperimentRecord:
    """Record of a single optimization experiment."""
    experiment_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""
    outcome: ExperimentOutcome = ExperimentOutcome.DISCARD

    # What was changed
    param_changes: Dict[str, str] = field(default_factory=dict)
    git_commit: str = ""

    # Results
    score_before: float = 0.0
    score_after: float = 0.0
    throughput_gbps: float = 0.0
    latency_us: float = 0.0

    # Timing
    duration_seconds: float = 0.0

    @property
    def improvement(self) -> float:
        """Fractional improvement (positive = better)."""
        if self.score_before == 0:
            return 0.0
        return (self.score_after - self.score_before) / self.score_before

    def to_dict(self) -> Dict:
        return {
            "id": self.experiment_id,
            "timestamp": self.timestamp,
            "description": self.description,
            "outcome": self.outcome.value,
            "param_changes": self.param_changes,
            "git_commit": self.git_commit,
            "score_before": self.score_before,
            "score_after": self.score_after,
            "improvement": f"{self.improvement:+.1%}",
            "throughput_gbps": self.throughput_gbps,
            "latency_us": self.latency_us,
            "duration_seconds": self.duration_seconds,
        }


class ResultsAnalyzer:
    """
    Analyzes experiment history to identify successful strategies.
    """

    def __init__(self):
        self._records: List[ExperimentRecord] = []

    @property
    def records(self) -> List[ExperimentRecord]:
        return list(self._records)

    def add_record(self, record: ExperimentRecord) -> None:
        """Add an experiment record."""
        self._records.append(record)

    def kept_experiments(self) -> List[ExperimentRecord]:
        """Return only experiments that were kept (improvements)."""
        return [r for r in self._records if r.outcome == ExperimentOutcome.KEEP]

    def best_experiment(self) -> Optional[ExperimentRecord]:
        """Return the experiment with highest score_after."""
        if not self._records:
            return None
        kept = self.kept_experiments()
        if not kept:
            return None
        return max(kept, key=lambda r: r.score_after)

    def param_contribution(self) -> Dict[str, Dict[str, float]]:
        """
        Analyze which parameter changes contributed to improvements.

        Returns:
            Dict mapping param_name -> {value -> avg_improvement}
        """
        contributions: Dict[str, Dict[str, List[float]]] = {}

        for record in self._records:
            if record.outcome == ExperimentOutcome.CRASH:
                continue
            for param, value in record.param_changes.items():
                if param not in contributions:
                    contributions[param] = {}
                if value not in contributions[param]:
                    contributions[param][value] = []
                contributions[param][value].append(record.improvement)

        # Average improvements
        result: Dict[str, Dict[str, float]] = {}
        for param, values in contributions.items():
            result[param] = {}
            for value, improvements in values.items():
                result[param][value] = sum(improvements) / len(improvements) if improvements else 0.0

        return result

    def progress_summary(self) -> str:
        """Human-readable progress summary."""
        total = len(self._records)
        kept = len(self.kept_experiments())
        crashed = len([r for r in self._records if r.outcome == ExperimentOutcome.CRASH])
        discarded = total - kept - crashed

        lines = [
            "ScuffedSearch Progress Summary",
            "=" * 35,
            f"Total experiments: {total}",
            f"  Kept: {kept}",
            f"  Discarded: {discarded}",
            f"  Crashed: {crashed}",
        ]

        best = self.best_experiment()
        if best:
            lines.extend([
                f"",
                f"Best score: {best.score_after:.4f}",
                f"  Throughput: {best.throughput_gbps:.2f} Gbps",
                f"  Latency: {best.latency_us:.1f} us",
                f"  Experiment: {best.experiment_id}",
            ])

        # Top contributing params
        contribs = self.param_contribution()
        if contribs:
            lines.append(f"")
            lines.append("Parameter contributions:")
            for param, values in contribs.items():
                best_val = max(values.items(), key=lambda x: x[1]) if values else None
                if best_val and best_val[1] > 0:
                    lines.append(f"  {param}: best={best_val[0]} ({best_val[1]:+.1%})")

        return "\n".join(lines)

    def save(self, path: str) -> None:
        """Save experiment history to JSON."""
        data = [r.to_dict() for r in self._records]
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self, path: str) -> None:
        """Load experiment history from JSON."""
        with open(path, 'r') as f:
            data = json.load(f)

        for entry in data:
            record = ExperimentRecord(
                experiment_id=entry["id"],
                timestamp=entry.get("timestamp", ""),
                description=entry.get("description", ""),
                outcome=ExperimentOutcome(entry.get("outcome", "discard")),
                param_changes=entry.get("param_changes", {}),
                git_commit=entry.get("git_commit", ""),
                score_before=entry.get("score_before", 0.0),
                score_after=entry.get("score_after", 0.0),
                throughput_gbps=entry.get("throughput_gbps", 0.0),
                latency_us=entry.get("latency_us", 0.0),
                duration_seconds=entry.get("duration_seconds", 0.0),
            )
            self._records.append(record)
