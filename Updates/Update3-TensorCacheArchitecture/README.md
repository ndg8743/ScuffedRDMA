# Update 3: RDMA Tensor Cache Architecture

Dated February 2026 in the tex. The folder was swapped with the old "Update 8" during the 2026-03-12 reorganization (`1c4aba2`), which is why the bibliography is still named `update8.bib`. The tex was edited across `7841ac0`, `e313564` (2026-02-14, Neumann replaced by the tensor database) and `a0d82ce` (2026-03-11, ScuffedKernels added).

This update is about the home towers, not the lab pair. It argues that a V100 (FP16 Tensor Cores, GPUDirect RDMA, no BF16) and a 5070 Ti (BF16, no RDMA stack on Windows) need a centralized FP32 master-weight cache with stochastic rounding per device, and that MLA/MQA models duplicate the KV cache on every tensor-parallel rank, so the KV cache should live in an external tensor database reached over one-sided RDMA reads through a vLLM V1 KV connector. It also surveys the NVIDIA communication stack, TP vs PP for the two-tower cluster, Amdahl and Gustafson applied to kernel work, CUDA vs Triton, NVSHMEM, AMD IRIS, the vLLM Semantic Router, and sketches two side projects (ScuffedKernels, ScuffedSearch) and SAE feature steering. All experiments are marked planned and untested in the tex.

## Research

Communication stack
- NCCL, UCX, UCC, HPC-X, GDRCopy, NIXL, NVSHMEM documentation: roles and limits of each library (Table 2 of the tex). Local: [NCCL_Documentation.md](../../References/Bookmarks_RDMA/thesis_refs/NCCL_Documentation.md), [UCX_Unified_Communication_X_Introduction.md](../../References/Bookmarks_Collection/UCX_Unified_Communication_X_Introduction.md), [UCX_Framework_Library_HPC-X.md](../../References/Bookmarks_Collection/UCX_Framework_Library_HPC-X.md), [ucc.pdf](../../References/ucc.pdf), [GitHub_NIXL_NVIDIA_Inference_Xfer.md](../../References/Bookmarks_Collection/GitHub_NIXL_NVIDIA_Inference_Xfer.md)
- GPUDirect RDMA on OpenShift AI (Red Hat). [GPUDirect_RDMA_OpenShift_AI_-_Red_Hat.md](../../References/Bookmarks_Collection/GPUDirect_RDMA_OpenShift_AI_-_Red_Hat.md)
- vLLM RFC for UCC as an NCCL alternative (PR #30930). No local copy.
- Ultra Ethernet Consortium 1.0. [UEC_1.0_Overview_Ultra_Ethernet_Consortium.pdf](../../References/Bookmarks_Collection/UEC_1.0_Overview_Ultra_Ethernet_Consortium.pdf)

Parallelism, KV cache and precision
- Megatron-LM: canonical TP/PP/DP and the FP32 master-weight pattern.
- DeepSeek-V2: MLA, the reason the KV cache cannot shard across TP ranks.
- Mixed Precision Training (Micikevicius et al.): FP16 range limits and master weights.
- Microscaling (MX) data formats: MXFP4 for Pillar 3. [Microscaling_Data_Formats_for_Deep_Learning_2310.10537.pdf](../../References/Bookmarks_Collection/Microscaling_Data_Formats_for_Deep_Learning_2310.10537.pdf)
- Hetis: heterogeneous-GPU fine-tuning schedule, mirrored by the V100/5070 Ti role split.
- Mooncake and the vLLM KV pool guide: HBM prefix cache plus external KV pool, the model for the connector flow.

Kernels
- Amdahl (1967), Gustafson (1988): the prioritization argument.
- Triton (MAPL 2019), Triton compiler tips. [Triton_Compiler_Development_Tips.md](../../References/Bookmarks_Collection/Triton_Compiler_Development_Tips.md)
- FlashAttention and FlashAttention-4. [FlashAttention_IO-Aware_2205.14135.pdf](../../References/Bookmarks_Collection/FlashAttention_IO-Aware_2205.14135.pdf), [TriDao_FlashAttention-4_Kernel_Pipelining_MLSys2026.pdf](../../References/Bookmarks_Collection/TriDao_FlashAttention-4_Kernel_Pipelining_MLSys2026.pdf)
- Reimplementing FlashAttention in Triton (AmineDiro): the 4.9x bank-conflict walkthrough. [Reimplementing_FlashAttention_-_AmineDiro.md](../../References/Bookmarks_Collection/Reimplementing_FlashAttention_-_AmineDiro.md)
- AMD IRIS (SHMEM-like RMA in Triton), AutoKernel, AutoResearch: inspiration for ScuffedKernels / ScuffedSearch.

Routing and interpretability
- vLLM Semantic Router. [When_to_Reason_Semantic_Router_vLLM_2510.08731.pdf](../../References/Bookmarks_Collection/When_to_Reason_Semantic_Router_vLLM_2510.08731.pdf)
- Sparse autoencoders (Cunningham et al. 2023; OpenAI SAE scaling), Eiffel Tower Llama steering demo: the SAE steering section.

## Work done

The tex maps concepts to a Rust `tensor_rdma` crate (`precision.rs`, `rounding.rs`, `prefetch.rs`, `transport.rs`, `rdma_cache.rs`, `config.rs`) inside the Neumann tensor database. That crate is not in this repo: Neumann was replaced by a Python `databases/` package in `e313564` (2026-02-14), and `databases/` was deleted as a duplicate of `middleware/rdma_tensor_cache/` in `029ca62` (2026-02-15). What exists today:

| Concept | Python module today |
|---|---|
| Precision management, stochastic rounding | `middleware/rdma_tensor_cache/precision.py` |
| Predictive prefetch engine | `middleware/rdma_tensor_cache/prefetch.py` |
| Tensor cache | `middleware/rdma_tensor_cache/cache.py` |
| Adaptive quantization | `middleware/rdma_tensor_cache/quantization.py` |
| SAE steering, sparse vectors | `middleware/rdma_tensor_cache/sae_steering.py` |
| KV connector | `middleware/rdma_tensor_cache/vllm_connector.py` (standalone) |
| Transport abstraction | `middleware/transport_base.py`, `tcp_transport.py`, `roce_transport.py`, `ttpoe_transport.py`, `selector.py` |

ScuffedKernels (`middleware/scuffedkernels/`, `a0d82ce`) and ScuffedSearch (`middleware/scuffedsearch/`) were deleted as unused scaffolding in `022b895` (2026-04-12).

## Next steps as written, status today

Update 3 has no Next Steps list. The experimental pillars and side projects are the commitments:

| Item | Status | Evidence |
|---|---|---|
| Pillar 1: precision switching overhead (stochastic vs deterministic rounding) | open | Code in `precision.py`; no benchmark or result. The precision benchmark `benchmarks/benchmark_precision.py` was deleted in `022b895`. |
| Pillar 2: prefetch effectiveness (hit rate, wasted prefetch) | open | Code in `prefetch.py`; no result. |
| Pillar 3: MXFP4 adaptive quantization | dropped | Superseded by scuffedQuant (Update 4). |
| Centralized KV cache via vLLM V1 connector | partial | `ScuffedRdmaConnector` in `middleware/vllm_plugin/` (built Oct 2026); cluster run pending. |
| SoftRoCEv2 vs hardware RoCE baseline on Tower 2 | partial | Table 6 is published specs, flagged "not our measurements". Hardware RoCEv2 was measured later (50.62 Gb/s, 0.71 us loopback on ConnectX-4) in backlog draft `Update8-InfrastructureRDMATesting`. |
| UCX/UCC integration path | dropped | Updates 4 and 7 moved the data path off UCX. |
| ScuffedKernels, ScuffedSearch | dropped | Deleted in `022b895`. The fused gather-Hadamard-rescale kernel idea resurfaces in Update 5-2. |
| SAE feature steering | partial | `sae_steering.py` exists and was hardened in Update 5; no steering results. |
| Proxmox GPU passthrough tuning | open | |

## Run it

- [`notebooks/05_scuffedquant.ipynb`](../../notebooks/05_scuffedquant.ipynb) covers what replaced Pillar 3.
- [`notebooks/03_libfabric_vs_libibverbs.ipynb`](../../notebooks/03_libfabric_vs_libibverbs.ipynb) on Tower 2 gives the measured SoftRoCE vs hardware RoCE comparison Table 6 projected.
- Pillars 1 and 2 have no notebook. If they stay in the thesis they need one; otherwise move them to future work.

## Corrections

- Table 6 lists SoftRoCE latency as ~190 us "typical". That number is the testbed's own `ib_write_lat` RTT between Chimera and Cerberus (backlog draft `Update8-InfrastructureRDMATesting`), not a published typical value.
- The RTX 5070 Ti is listed as compute capability 12.0 (correct, SM_120). Note SM_120 lacks `tcgen05` and `wgmma`, so Blackwell-datacenter kernels (SM_100) do not apply to it.
- The module-mapping table points at Rust files that are not in this repo; cite the Python modules above instead.
- "GPUDirect RDMA: V100 GPU memory via `cuda_copy,gdr_copy`": in UCX those are the CUDA copy transports; GPUDirect RDMA itself goes through the RC transport with `nvidia-peermem`, which is still blocked on Tower 2's kernel.
