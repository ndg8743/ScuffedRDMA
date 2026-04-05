# ScuffedSearch

Autonomous RDMA parameter-search loop. One GPU, one file, one metric.

Referenced from `Updates/Update3-TensorCacheArchitecture/update3.tex`
§ScuffedSearch. See `research_plan.md` in this directory for the full rules.

## Model

- `prepare.py` — **immutable**. Defines the benchmark harness, network topology,
  and the scoring function (geometric mean of throughput efficiency and latency
  factor).
- `optimize.py` — **the only mutable file**. An agent (or a human) edits this
  file to change one tunable parameter at a time.
- `analysis.py` — records each experiment with its commit hash and score,
  builds the keep/discard history.

One change per commit. Keep if the score improves by >1%, else discard. Each
experiment has a 5-minute budget.

## Tunable axes

- Batch size (1–256)
- QP depth (1–128)
- Prefetch depth (0–10)
- Wire format (FP32 / FP16 / BF16 / INT8)

## Relationship to the thesis core

ScuffedSearch is an experiment driver, not part of the runtime RDMA path. It
consumes the same `middleware/` transports as the thesis benchmarks but wraps
them in a search loop with enforced reproducibility discipline.
