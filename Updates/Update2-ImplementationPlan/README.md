# Update 2: Implementation Plan

Dated January 2026 in the tex. First written 2026-01-31 (`b2ca1fe`, `3936662`), then cleaned up on 2026-02-20 (`9b3cf25` removed unsubstantiated percentage claims, `f00b6fb` fixed charts, added the bibliography and removed false claims). This is the plan that the rest of the thesis is measured against. It names the problem as head-of-line blocking that shows up as TTFT, lists what vLLM already provides (PagedAttention, NCCL, NIXL connectors, LMCache, llm-d) so the contribution is "builds on, not replaces", and defines three components: a unified telemetry layer, a three-state WFA classifier (Cold/Warm/Hot with frequency thresholds and idle timeouts, plus prefill/decode phase detection), and a dual-path RDMA router (hot: polled CQ, WRITE_WITH_IMM; cold: batched, event-driven CQ; NUMA-aware MRs via libnuma). Five phases follow: foundation, telemetry and classification, routing integration with an `AdaptiveRDMAConnector`, a training extension, and validation with ablations.

## Research

vLLM and disaggregated serving
- vLLM / PagedAttention: the KV manager and `KVConnectorBase` hook. [PagedAttention_Efficient_LLM_Serving_2309.06180.pdf](../../References/Bookmarks_Collection/PagedAttention_Efficient_LLM_Serving_2309.06180.pdf)
- vLLM disaggregated prefilling docs: where the connector plugs in. [Disaggregated_Prefill_vLLM.md](../../References/Bookmarks_Collection/Disaggregated_Prefill_vLLM.md)
- Anatomy of vLLM. [Anatomy_of_vLLM.md](../../References/Bookmarks_Collection/Anatomy_of_vLLM.md)
- NIXL (NVIDIA Dynamo): the existing KV transfer path the thesis connector sits beside. [GitHub_NIXL_NVIDIA_Inference_Xfer.md](../../References/Bookmarks_Collection/GitHub_NIXL_NVIDIA_Inference_Xfer.md)
- LMCache and the LMCache + vLLM v1 + NIXL integration. [LMCache_vLLM_NIXL.md](../../References/Bookmarks_Collection/LMCache_vLLM_NIXL.md)
- llm-d architecture and v0.4 results. [llm-d_Architecture.md](../../References/Bookmarks_Collection/llm-d_Architecture.md)
- vLLM Semantic Router v0.1 Iris: signal-decision routing; later the model for the Rule-Node Expression Tree policy engine. [vLLM_SR-IRIS.md](../../References/Bookmarks_Collection/vLLM_SR-IRIS.md)
- NCCL: the static, bulk-tuned baseline. [NCCL_Documentation.md](../../References/Bookmarks_RDMA/thesis_refs/NCCL_Documentation.md)

Transports
- rdma-core and pyverbs: the prototype stack. [rdma_core_Documentation.md](../../References/Bookmarks_RDMA/thesis_refs/rdma_core_Documentation.md)
- perftest: `ib_write_lat` / `ib_write_bw` baselines. [perftest_RDMA_Performance_Tests.md](../../References/Bookmarks_RDMA/thesis_refs/perftest_RDMA_Performance_Tests.md)
- Tesla TTPoe (repo, Hot Chips 2024, Chips and Cheese analysis): lossy transport without PFC. [Tesla_TTPoE_Hot_Chips_2024.pdf](../../References/Bookmarks_Collection/Tesla_TTPoE_Hot_Chips_2024.pdf), [Tesla_TTPoe_Chips_and_Cheese.md](../../References/Bookmarks_Collection/Tesla_TTPoe_Chips_and_Cheese.md)
- NVIDIA GPUDirect RDMA docs: nvidia-peermem, same PCIe root complex. [GPUDirect_RDMA_Documentation_-_NVIDIA.md](../../References/Bookmarks_Collection/GPUDirect_RDMA_Documentation_-_NVIDIA.md)
- Arch Wiki InfiniBand. [InfiniBand_Setup_Guide.md](../../References/Bookmarks_RDMA/thesis_refs/InfiniBand_Setup_Guide.md)

Future-work section (RISC-V assembly LLM)
- Hossain et al., Can ChatGPT assist in the development of a RISC processor? (arXiv:2401.10364). [arxiv_2401.10364.pdf](../../References/Bookmarks_Collection/arxiv_2401.10364.pdf)
- NVIDIA mixed-precision guide and GPU performance background. [Train_With_Mixed_Precision_-_NVIDIA.md](../../References/Bookmarks_Collection/Train_With_Mixed_Precision_-_NVIDIA.md)

## Work done

The plan itself has no code. Its components ended up as:

- WFA classifier: `middleware/rdma_tensor_cache/wfa_classifier.py` (size thresholds, access counts, layer-sweep phase detection), first committed in the MVP `8e01509` (2026-03-31). The original three-state `TensorClassifier` with `theta1`/`theta2`/`t_idle` lives on in `middleware/rdma_tensor_cache/vllm_connector.py`.
- Dual-path QP pool: `middleware/rdma_tensor_cache/dual_qp_pool.py` (`8e01509`).
- pyverbs buffer pool: `RegisteredBuffer` in the same file. Not NUMA-aware.
- Connector: `RDMAKVCacheConnector` in `vllm_connector.py` is standalone, not registered with vLLM. The vLLM-facing connector is `ScuffedRdmaConnector` in `middleware/vllm_plugin/` (built Oct 2026).

## Next steps as written, status today

Update 2's plan is phased rather than a Next Steps list. Each deliverable:

| Phase / deliverable | Status | Evidence |
|---|---|---|
| 1. RDMA ping-pong under 10 us RTT on SoftRoCE | partial | Best evidence is a one-way write completion, not an RTT: 12.6 us p50 for 64 B, loopback (`benchmarks/results/ucx_comparison.json`). `ib_write_lat` between Chimera and Cerberus measured about 190 us (backlog draft `Update8-InfrastructureRDMATesting`). The 8 us cross-node figure in `dual_qp_remote_benchmark.json` is suspect, see Update 4 README. |
| 1. sockperf TCP baseline | open | No sockperf results in the repo. |
| 1. NUMA-aware buffer pool (libnuma) | open | No NUMA code. Chimera and Cerberus are single-socket, so this has low value for the thesis. |
| 2. Instrument vLLM `KVCacheManager` | open | |
| 2. Unified telemetry (frequency, size distribution, queue depth, p50/p95/p99) | done (Oct 2026), not integrated | `middleware/telemetry.py`, `tests/test_telemetry.py`. Not yet fed from vLLM. |
| 2. WFA classifier + phase detection | done | `wfa_classifier.py`. |
| 2. Classifier accuracy on synthetic patterns | built (Oct 2026), cluster run pending | `middleware/rdma_tensor_cache/wfa_learner.py`, `tests/test_wfa_learner.py`, notebook 04. Backlog draft Update 9 only had expected results. |
| 3. Dual-path QP pool | done | `dual_qp_pool.py`; C versions in `middleware/libscuffedverbs/` and `middleware/libscuffedfabric/` (Oct 2026). |
| 3. `AdaptiveRDMAConnector` in vLLM | partial | Standalone prototype superseded by `ScuffedRdmaConnector` in `middleware/vllm_plugin/` (built Oct 2026); TTFT run pending (notebook 06). |
| 3. TTFT vs NCCL baseline on a 7B model | open | Notebook 06 is the harness; no results yet. |
| 4. Adaptive all-reduce, FSDP integration, Nsight profiling | deferred | Main focus moved to the inference transport (Aug 2026). |
| 5. 7B/13B/70B sweep, TP 2/4/8 | open | |
| 5. Ablations: WFA vs static, hot-only vs dual-path, NUMA vs not, threshold sensitivity | open | Notebooks 01 and 04 cover the first, second and fourth. |
| Future work: RISC-V assembly LLM | dropped | `RISVLLM-app` removed from main in `45f3414` (2026-04-16). |

## Run it

- [`notebooks/00_environment_check.ipynb`](../../notebooks/00_environment_check.ipynb): Phase 1 checks (devices, providers, perftest if installed).
- [`notebooks/01_hol_blocking.ipynb`](../../notebooks/01_hol_blocking.ipynb): the hot-only vs dual-path ablation.
- [`notebooks/04_wfa_and_policy.ipynb`](../../notebooks/04_wfa_and_policy.ipynb): Phase 2 classifier accuracy and threshold sensitivity.
- [`notebooks/06_vllm_disagg_ttft.ipynb`](../../notebooks/06_vllm_disagg_ttft.ipynb): Phase 3 TTFT.
- Tests: `tests/test_telemetry.py`, `tests/test_wfa_learner.py`, `middleware/tests/`.

## Corrections

- "The V100s and RTX 5090s support GPUDirect RDMA": GeForce cards (5090, 5070 Ti, 3090) do not. Only the V100s on Tower 2 do.
- "Home lab: 100GbE Mellanox ConnectX-4 with SoftRoCE": the ConnectX-4 does hardware RoCEv2; SoftRoCE is only needed on the X710 and AQC107.
- Transport table latencies (SoftRoCE ~10 us, RoCEv2 ~4-5 us, TTPoe ~1-2 us) are typical figures, not testbed measurements. Measured SoftRoCE between Chimera and Cerberus was about 190 us RTT with `ib_write_lat`.
- The tensor-parallel integration point (replace NCCL all-reduce in `parallel_state.py`) was never pursued; the thesis stayed on the KV connector path.
