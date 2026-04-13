# scuffedkernels

RDMA-aware kernel optimization framework. Profiles GPU kernels, ranks
them by Amdahl's Law, runs a tiered optimization playbook, validates
each candidate, and keeps or reverts based on measured speedup.

## Files

- `profiler.py` — `KernelProfiler` and `AmdahlRanking`. Collects
  per-kernel wall time, GPU time, memory, and FLOPs, then ranks by how
  much of total model time each kernel owns. Flags RDMA-bound kernels
  separately since their wait time overlaps with network transfers.
- `optimizer.py` — `KernelOptimizer` with a six-tier playbook applied
  one tier at a time: (1) block and grid dimensions, (2) memory access
  patterns and shared-memory use, (3) reduced precision (TF32/FP16),
  (4) persistent and fused kernels, (5) architecture-specific tuning
  (SM occupancy, warp specialization), (6) overlap compute with RDMA
  transfers.
- `benchmarker.py` — `KernelBenchmarker` with a five-stage validation
  gate: smoke, shape, numerical stability, determinism, edge cases.
  Also runs an RDMA-aware roofline.
- `orchestrator.py` — state machine that drives the
  profile to rank to optimize to validate to accept-or-revert loop.
  Records each `KernelOptimizationRecord` so results are reproducible.

## kernels subpackage

`kernels/` holds baseline Triton implementations for the orchestrator to
optimize. All three fall back to NumPy when Triton is missing.

- `attention.py` — Flash-Attention-style tiled attention.
- `matmul.py` — tiled GEMM with NVSHMEM integration stubs for
  RDMA-aware compute.
- `softmax.py` — online-normalized softmax.

## Stale

None. All files are from a single commit (`a0d82ce`) and are wired
together through `__init__.py`.
