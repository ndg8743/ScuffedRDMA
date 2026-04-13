# scuffedsearch

Autonomous RDMA research automation. One GPU, one file, one metric.
`prepare.py` is the frozen evaluation harness. `optimize.py` is the only
file agents are allowed to change. Every run is a git commit so
attribution of score changes is unambiguous.

## Files

- `prepare.py` — **immutable**. Defines `NetworkTopology` (100 GbE,
  2 μs hardware-RoCE baseline, 190 μs SoftRoCEv2 baseline, ConnectX-4
  1024-QP limit, tower GPU inventory), `RDMAMetrics`, and the
  `BenchmarkHarness` that produces the score. Do not modify.
- `optimize.py` — **mutable**. Holds `TUNABLE_PARAMS`, the `WireFormat`
  and `TransportMode` enums, and the optimization function. Agents edit
  this file and only this file.
- `analysis.py` — `ResultsAnalyzer` and `ExperimentRecord`. Tracks each
  experiment's outcome (KEEP / DISCARD / CRASH) and reports which
  changes contributed to improvements.

## research_plan.md

`research_plan.md` spells out the ground rules and scoring and is still
current. Relevant bits:

- KEEP when the score improves by more than 1%, otherwise DISCARD.
- Each experiment finishes within a 5-minute time budget.
- Optimization axes include batch size, QP depth, prefetch depth, wire
  format, transport mode, buffer pool size, inline threshold, and
  congestion window.
- The experiment log table at the bottom is where outcomes get
  recorded. At time of writing only the baseline row exists.

## Stale

None. The harness, optimizer, and analyzer are all reachable through
`__init__.py` and the research plan matches what the code does.
