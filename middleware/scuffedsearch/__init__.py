"""
ScuffedSearch: Autonomous RDMA Research Automation.

One GPU, one file, one metric. prepare.py is immutable (defines the
evaluation harness), optimize.py is mutable (the only file agents modify).

Exports:
    BenchmarkHarness - Evaluation harness (from prepare.py)
    RDMAOptimizer - Tunable optimization (from optimize.py)
    ResultsAnalyzer - Experiment tracking (from analysis.py)
"""

from .prepare import BenchmarkHarness, NetworkTopology, RDMAMetrics
from .optimize import RDMAOptimizer, TUNABLE_PARAMS
from .analysis import ResultsAnalyzer, ExperimentRecord

__all__ = [
    'BenchmarkHarness',
    'NetworkTopology',
    'RDMAMetrics',
    'RDMAOptimizer',
    'TUNABLE_PARAMS',
    'ResultsAnalyzer',
    'ExperimentRecord',
]
