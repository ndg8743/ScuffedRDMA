# benchmarks

Benchmark scripts for libscuffedrdma (dual QP pool, WFA classifier, PMP controller), scuffedQuant (PolarQuant + QJL KV cache compression), and UCX comparison runs used in the thesis updates.

Most scripts write JSON into `results/`. `aggregate_results.py` reads that directory and emits LaTeX tables for the thesis appendix.

## Dual QP pool

- `benchmark_dual_qp.py` - Loopback on a single rxe0 device, two `DualQPPool`s in-process. Measures head-of-line blocking elimination under mixed 256B/1MB traffic with WFA and PMP enabled.
  ```
  python benchmark_dual_qp.py --iterations 1000 --output results/dual_qp_benchmark.json
  ```
- `benchmark_dual_qp_remote.py` - Cross-node version (chimera <-> cerberus over 10GbE). Simulates a 32-layer KV cache transfer.
  ```
  # cerberus
  python benchmark_dual_qp_remote.py --role server --port 19877
  # chimera
  python benchmark_dual_qp_remote.py --role client --host 192.168.1.242 --port 19877
  ```

## UCX comparison

- `benchmark_ucx_comparison.py` - Drives `ucx_perftest` across eager/RNDV boundaries and compares against the dual QP pool. References UCX issues #10552, #10486, #10532, #11091.
  ```
  python benchmark_ucx_comparison.py --output results/ucx_comparison.json
  ```

## Per-architecture (test_arch/)

- `test_arch/` - per-architecture scuffedQuant benchmarks for Update 5-2 (Transformer, Mamba-3, Granite 4 hybrid, Granite 4 MoE). See [`test_arch/README.md`](test_arch/README.md) for cross-node usage. `aggregate_results.py --results-dir results/test_arch` emits `test_arch_comparison.tex`.

## scuffedQuant

- `benchmark_scuffed_quant.py` - Synthetic KV vectors, measures inner-product preservation and throughput at various bit widths.
  ```
  python benchmark_scuffed_quant.py --bits 3 --heads 32 --dim 128
  ```
- `benchmark_scuffed_quant_llm.py` - Loads Granite 3.3-2B in the ScuffedRDMA venv, runs prefill, compresses the real KV cache, and checks attention score agreement.
  ```
  python benchmarks/benchmark_scuffed_quant_llm.py
  ```
- `benchmark_scuffed_quant_mlx.py` - Same quantizer on Apple Silicon via MLX, loads `mlx-community/granite-3.3-2b-instruct-4bit`.
  ```
  python benchmark_scuffed_quant_mlx.py
  ```

## Aggregation

- `aggregate_results.py` - Reads every JSON in `results/` and emits LaTeX tables (summary, dual QP, UCX) for the thesis updates.
  ```
  python aggregate_results.py --results-dir results --output results/
  ```

## results/

JSON output plus generated `.tex` fragments. Most recent runs are `dual_qp_remote_benchmark.json` (Apr 3), `scuffed_quant_llm.json` (Apr 3), `scuffed_quant_benchmark.json` (Apr 2). The UCX comparison output (`ucx_comparison.json`) and aggregate tables are from Mar 30. `infra_report.json` at the top level is from the same Mar 30 run.

