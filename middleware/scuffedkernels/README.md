# ScuffedKernels

GPU kernel profiling, optimization, and benchmarking framework for attention,
matmul, and softmax. Part of the ScuffedRDMA repo but **not** part of the RDMA
transport data path — it sits alongside the thesis core and shares the cluster
hardware.

Referenced from `Updates/Update3-TensorCacheArchitecture/update3.tex`
§ScuffedKernels. The framework uses Amdahl-priority ranking to decide which
kernel to optimize next: the product of potential speedup and absolute time
saved on the inference workload.

## Layout

```
scuffedkernels/
├── profiler.py      # Per-kernel timing + occupancy collection
├── benchmarker.py   # Repeatable micro-benchmark harness
├── optimizer.py     # Tuning loop with guardrails
├── orchestrator.py  # Top-level driver
└── kernels/
    ├── attention.py
    ├── matmul.py
    └── softmax.py
```

## Relationship to the thesis core

ScuffedKernels does not import from `middleware/rdma_tensor_cache/` or from the
transport layer. It produces optimized GPU kernels; the RDMA path consumes
tensors regardless of which kernel produced them. They are independently
runnable.
