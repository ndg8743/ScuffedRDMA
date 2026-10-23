# Update 4: Implementation, PMP, WFA, and the RDMA-Compute Interface

Dated 2026-03-31. The code landed first (`8e01509`, 2026-03-31: libscuffedrdma MVP with dual QP pools, WFA classifier, PMP controller, benchmarks), then a week of tex revisions (`f69f942` through `e51e2ee`, 2026-04-02 to 2026-04-05), with scuffedQuant added in `075cdc6` / `63da0b5` / `4bc79ff` and the cross-node run in `09946e6` (2026-04-03). A one-line footnote pointing at Update 5-2 was added in `4cc8a1f`.

The update makes the thesis concrete. libscuffedrdma is middleware between vLLM's KV connector interface and raw libibverbs: a WFA classifier labels each transfer, a PMP bang-bang controller allocates the link between a hot RC QP pool (inline data, busy-poll CQ) and a cold RC QP pool (deep SQ, event-driven CQ). The theory section uses the Scaling Book decode-latency model and Pontryagin's Maximum Principle: with a Hamiltonian linear in the control and fixed link capacity, the optimal allocation is bang-bang, driven by a switching function `S = a*q_H*C*mu_H - b*q_C*C*mu_C`. It maps five deployment configurations (one user one GPU, through multi-model multi-machine) to QP and verbs usage, catalogs UCX issues that motivate bypassing UCX, describes the KV compression pipeline (LoRC, KVTC, TurboQuant) and scuffedQuant, and reports the first benchmarks on Chimera's SoftRoCE.

## Research

Theory
- Austin et al., How to Scale Your Model (Scaling Book): roofline and decode step-time model. [How_To_Scale_Your_Model_JAX.md](../../References/Bookmarks_Collection/How_To_Scale_Your_Model_JAX.md)
- Pontryagin, Mathematical Theory of Optimal Processes; Bellman, Glicksberg and Gross on bang-bang control; Liberzon, Calculus of Variations and Optimal Control: the PMP argument. [Pontryagin_Maximum_Principle_PMP.pdf](../../References/Bookmarks_Collection/Pontryagin_Maximum_Principle_PMP.pdf)
- Zhang, Cheng and Li, An optimal control view of LoRA and binary controller design (ICML 2024): a binary controller derived the same way. [An_Optimal_Control_View_of_LoRA_...pdf](../../References/Bookmarks_RDMA/Papers_Papers/An_Optimal_Control_View_of_LoRA_and_Binary_Controller_Design_for_Vision_Transfor.pdf)
- Is PMP all you need? (arXiv:2410.06277). [Pontryagin_Maximum_Principle_NN_2410.06277.pdf](../../References/Bookmarks_Collection/Pontryagin_Maximum_Principle_NN_2410.06277.pdf)
- Shazeer (MQA), Ainslie et al. (GQA), AiEdge on decoding latency: KV size per request.

KV compression
- LoRC (arXiv:2410.03111): low-rank K/V projection. [LoRC_...2410.03111.pdf](../../References/Bookmarks_RDMA/Papers_Papers/LoRC_Low_Rank_Compression_for_LLMs_KV_Cache_with_a_Progressive_Compression_Strat_2410.03111.pdf)
- KVTC, KV cache transform coding (arXiv:2511.01815). [KV_Cache_Transform_Coding_2511.01815.pdf](../../References/Bookmarks_Collection/KV_Cache_Transform_Coding_2511.01815.pdf)
- TurboQuant (Zandieh et al., arXiv:2504.19874): random rotation plus scalar quantization plus a QJL residual sketch. No local PDF; the Pure Storage write-up is at [TurboQuant_KV_Cache_FlashBlade.md](../../References/Bookmarks_Collection/TurboQuant_KV_Cache_FlashBlade.md). QJL (arXiv:2406.03482) and PolarQuant (arXiv:2502.02617) have no local copies.

Production systems and transport
- TransferEngine (arXiv:2510.27656): one-sided WriteImm across multiple NICs; the closest system-level comparison. [fabric_lib_RDMA_Point_to_Point_...2510.27656.pdf](../../References/Bookmarks_RDMA/Papers_Papers/fabric_lib_RDMA_Point_to_Point_Communication_for_LLM_Systems_2510.27656.pdf)
- Mistral, Heaps do lie: the UCX mmap GOT-patching leak (~400 MB/min) in production vLLM; the reason the data path bypasses UCX. [Debugging_Memory_Leak_vLLM_Mistral.md](../../References/Bookmarks_Collection/Debugging_Memory_Leak_vLLM_Mistral.md)
- llm-d v0.5: UCCL's software transport over UCX. [llm-d_v0.5_Performance.md](../../References/Bookmarks_Collection/llm-d_v0.5_Performance.md)
- NVIDIA Dynamo / NIXL. [GitHub_NIXL_NVIDIA_Inference_Xfer.md](../../References/Bookmarks_Collection/GitHub_NIXL_NVIDIA_Inference_Xfer.md)
- Lequn Chen, Harnessing 3200 Gbps network: libfabric on EFA. [RDMA_EFA_3200Gbps_Network.md](../../References/Bookmarks_Collection/RDMA_EFA_3200Gbps_Network.md)
- HPC-X UCX framework docs. [UCX_Framework_Library_HPC-X.md](../../References/Bookmarks_Collection/UCX_Framework_Library_HPC-X.md)
- UCX issue tracker (#10552, #10486, #10532, #4430, #11091, #11004, #11034, #1319, #10652, #6511, #9364, #10608, #9520, #10669, #10420, #6721, #10568, #7989, #7880, #10325): the size-only routing, shared QP and opaque selection problems. GitHub only.
- Context and side reading: SemiAnalysis Blackwell TCO ([pdf](../../References/Bookmarks_Collection/Nvidia_Blackwell_Perf_TCO_Analysis_SemiAnalysis.pdf)), PTX optimization intro ([md](../../References/Bookmarks_Collection/Intro_PTX_Optimization.md)), K-Search ([pdf](../../References/Bookmarks_Collection/K-Search_LLM_Kernel_Generation_2602.19128.pdf)), MaxText-Slurm on ROCm ([md](../../References/Bookmarks_Collection/MaxText-Slurm_LLM_Training_ROCm.md)), vLLM TPU backend ([md](../../References/Bookmarks_Collection/vLLM_TPU_Backend.md)), Paxos vs Raft vs ZAB (heartbeats as a hot-path example).

## Work done

Code (all `8e01509` unless noted):
- `middleware/rdma_tensor_cache/dual_qp_pool.py`: hot/cold RC QP pools on one PD, busy-poll vs 50 us sleep-poll.
- `middleware/rdma_tensor_cache/wfa_classifier.py`: size thresholds (4 KB / 256 KB), access counts, layer-sweep phase detection.
- `middleware/rdma_tensor_cache/pmp_controller.py`: switching function with deadband.
- `middleware/rdma_tensor_cache/scuffed_quant.py` (`075cdc6`, QJL scaling fix `4bc79ff`).
- `benchmarks/benchmark_dual_qp.py`, `benchmark_dual_qp_remote.py`, `benchmark_ucx_comparison.py`, `benchmark_scuffed_quant_llm.py`, `benchmark_scuffed_quant_mlx.py`, `aggregate_results.py`.

Results, Chimera, SoftRoCE (rxe0 on the AQC107), pyverbs 50.0:

| Measurement | Value | Source |
|---|---|---|
| 256 B write under a 256 B + 1 MB mix, loopback, single QP | p50 13.6 / p95 15.9 / p99 17.7 us | `benchmarks/results/aggregate_results.json` (loopback, scenario_A, n=500) |
| same, dual QP + WFA | p50 14.2 / p95 17.7 / p99 21.4 us | same file, scenario_B |
| same, dual QP + PMP | p50 14.5 / p95 18.5 / p99 23.2 us | same file, scenario_C |
| 64 B write completion, loopback | p50 12.6 us, p99 48.1 us | `benchmarks/results/ucx_comparison.json` |
| 1 MB write completion, loopback | p50 2822.6 us | `benchmarks/results/ucx_comparison.json` |
| scuffedQuant 3-bit + QJL (qjl_dim 256), Granite 3.3-2B FP32, mean top-8 overlap | 91.1% over 40 layers (min 82.8%, std about 3.3%) | `benchmarks/results/scuffed_quant_llm.json` |
| same, MLX 4-bit weights | 100.0% | `benchmarks/results/scuffed_quant_mlx.json` |
| scuffedQuant compression | 4.0x vs FP32 KV (about 2.0x vs FP16) | `compression_ratio()` in `scuffed_quant.py`; tex, scuffedQuant results |

The loopback dual-QP numbers are slower than single QP, and the tex explains why: SoftRoCE processes one operation at a time in a single-threaded benchmark, so there is no head-of-line blocking to remove, only the cost of two pools.

## Next steps as written, status today

| Next step | Status | Evidence |
|---|---|---|
| 1. Multi-threaded concurrent workload to show HOL blocking removed | built (Oct 2026), cluster run pending | Carried into Update 5 unchanged. Now built as concurrent mixed-traffic benchmarks in C: `middleware/libscuffedverbs/` and `middleware/libscuffedfabric/`, driven by notebook 01. No testbed result yet. |
| 2. vLLM KvConnector integration, prefill on Cerberus, decode on Chimera, scuffedQuant in the path | built (Oct 2026), cluster run pending | `middleware/vllm_plugin/` (ScuffedRdmaConnector), notebook 06. No TTFT result yet. |
| 3. Port the data path from pyverbs to Rust or C++ | partial | C, not C++/Rust: NCCL net plugin `middleware/nccl_plugin/` (`4bc0a38`, 2026-04-16, built Oct 2026), libibverbs and libfabric pools in `middleware/libscuffedverbs/` and `middleware/libscuffedfabric/` (Oct 2026). |

Upstream UCX pull requests: the tex says "I submitted six pull requests ... that fix the underlying issues directly" and Table 3 is titled "Upstream UCX Contributions". None were merged. As of 2026-10-22, #11305, #11306, #11307, #11308 and #11309 are open with review required, and #11304 is closed. They are submissions, not contributions, and the thesis should not count them as results.

## Run it

- [`notebooks/01_hol_blocking.ipynb`](../../notebooks/01_hol_blocking.ipynb): Next step 1. Concurrent hot and cold producers, single QP vs dual QP, verbs and libfabric, hot p50/p99 under cold load.
- [`notebooks/04_wfa_and_policy.ipynb`](../../notebooks/04_wfa_and_policy.ipynb): WFA classification accuracy, including the decode-as-prefill misclassification noted below.
- [`notebooks/05_scuffedquant.ipynb`](../../notebooks/05_scuffedquant.ipynb): reruns the Granite 3.3-2B overlap and reports bit-packed sizes.
- [`notebooks/06_vllm_disagg_ttft.ipynb`](../../notebooks/06_vllm_disagg_ttft.ipynb): Next step 2.
- Tests: `tests/test_pmp_controller.py`, `tests/test_scuffed_quant.py`, `tests/test_wfa_learner.py`.

## Corrections

- **Cross-node results should not be cited as they stand.** `benchmarks/results/dual_qp_remote_benchmark.json` (`09946e6`, "8us decode latency") reports 8 MB prefill writes completing in 8.3 us p50 on the single-QP path. 8 MB over 10GbE takes about 6.7 ms at line rate, so those completions cannot be successful transfers. `DualQPPool._poll_busy` / `_poll_sleep` return on any completion without checking `wc.status`, so flushed or errored work requests count as fast completions. In the dual-QP scenarios the WFA sent all 64 transfers to the cold pool (hot_count 0, phase detected as prefill for the decode sweep too), so the run never exercised the hot path. Rerun with status checks before quoting a cross-node latency; the top-level README's "8 us cross-node decode latency" and Update 5-2's "Update 4 measured 8 us" inherit this.
- **Compression ratio.** `compression_ratio()` is relative to FP32. `benchmark_scuffed_quant_llm.py` computes `kv_compressed_bytes = kv_bytes_fp16 / compression_ratio`, which understates the compressed size by 2x (the JSON's 1,187,840 bytes should be about 2,375,680). Versus the FP16 wire format the ratio is about 2.0x, as the tex says. Update 5-2's "10x compression ratio vs FP16" recap is wrong.
- **QJL width.** The tex calls the residual a "1-bit sketch". The benchmarks use `qjl_dim = 256`: a 256-bit sign sketch per vector (one sign bit per projected coordinate). State it as a 256-bit QJL sketch.
- **PolarQuant vs TurboQuant.** The tex (and the `scuffed_quant.py` docstring) call stage 1 "PolarQuant". TurboQuant's stage 1 is a random rotation followed by per-coordinate Lloyd-Max quantization; PolarQuant (arXiv:2502.02617) is a separate method that quantizes in polar coordinates. scuffedQuant implements the TurboQuant recipe (randomized Walsh-Hadamard rotation, Lloyd-Max codebook, QJL residual sketch). Cite TurboQuant for the pipeline and QJL (Zandieh, Daliri, Han, arXiv:2406.03482) for the sketch.
- The UCX section says libscuffedrdma "addresses" those UCX issues and that the PRs "fix the underlying issues directly". It bypasses UCX; the issues remain open upstream.
- The latency table marks UCX protocol boundaries but `ucx_comparison.json` has an empty `ucx_results` list: no UCX latency was measured in this run, so there is no side-by-side.
