# Proposal

Three versions of the thesis proposal live here, all titled "Adaptive RDMA Optimization for Distributed LLM Training and Inference on Consumer Hardware". `prepropasal.tex` is the first pass (it still has a self-training demo and a "why I need your expertise" section for the advisors), `propsal.tex` adds the security section, and `revised_proposal_v2.tex` / `.pdf` is the version that went to Dr. Danesh and Dr. Suchy. Git history starts 2026-01-31 (`b2ca1fe`); the folder was reorganized in `2b8a5a3` and `7841ac0` (2026-02-09, 2026-02-14). `Hydra_Lab_Test.md` is the SoftRoCE / SR-IOV / DOCA / GPUDirect setup guide for the Hydra lab cluster.

The argument: a 4 KB hot tensor waits behind a 10 MB cold layer on the same link, so classify tensors hot/cold at runtime and route them onto separate RDMA paths. The proposal frames this as a joint training + inference problem on commodity Ethernet, with a phase-aware Weighted Finite Automaton (states Cold/Warm/Hot, alphabet phase x accessed, transition weights learned online by EMA), UD queue pairs for hot traffic and batched, Top-K-compressed RC traffic for cold, a three-state KV migration protocol (RESIDENT, MIGRATING, MIGRATED), and a joint training/inference scheduler with weighted fair queuing.

## Research

RDMA security
- Bedrock (Xing et al., USENIX Security 2022): programmable-switch defenses for RDMA; cited as the multi-tenant answer the thesis does not attempt. No local copy.
- ReDMArk (Rothenberger et al., USENIX Security 2021): predictable QPN/rkey/PSN attacks; motivates the credential-rotation and QP-limit mitigations. No local copy.

RDMA for ML training
- Gangidi et al., RDMA over Ethernet for Distributed AI Training at Meta Scale (SIGCOMM 2024): receiver-driven congestion control on RoCE at scale.
- BytePS (OSDI 2020): separating communication from computation; local copy [USENIX_OSDI20_Jiang.pdf](../../References/Bookmarks_Collection/USENIX_OSDI20_Jiang.pdf).
- P3 (MLSys 2019), PowerSGD (NeurIPS 2019), Accordion (MLSys 2021): prioritizing and compressing gradients by importance; the training half of the hot/cold idea.
- ZeRO (SC 2020): the gradient sync pattern the scheduler would sit under.

Inference serving
- PagedAttention / vLLM (SOSP 2023): the KV cache manager everything plugs into. [PagedAttention_Efficient_LLM_Serving_2309.06180.pdf](../../References/Bookmarks_Collection/PagedAttention_Efficient_LLM_Serving_2309.06180.pdf)
- SGLang (2023) and DistServe (2024): inference-only systems, cited as the "optimizes one side only" baseline.
- NVIDIA NIM benchmarking docs: TTFT/ITL metric definitions. https://docs.nvidia.com/nim/benchmarking/llm/latest/metrics.html
- rdma-core: the userspace stack. [rdma_core_Documentation.md](../../References/Bookmarks_RDMA/thesis_refs/rdma_core_Documentation.md)

## Work done

The proposal itself produced no code. What came after it, by component:

| Proposal component | Where it ended up |
|---|---|
| Telemetry monitor with Prometheus export | `middleware/telemetry.py` (signal vectors, per-class p50/p95/p99, QP error/reconnect counters, `/metrics` exporter), tested in `tests/test_telemetry.py`. Built Oct 2026, not wired into vLLM. |
| Phase-aware WFA with learned weights | `middleware/rdma_tensor_cache/wfa_classifier.py` (thresholds + phase detection, `8e01509`, 2026-03-31); learned weights in `middleware/rdma_tensor_cache/wfa_learner.py` (Oct 2026). |
| Hot UD QPs / cold batched RC QPs | Became a dual RC QP pool (hot busy-poll, cold sleep-poll): `middleware/rdma_tensor_cache/dual_qp_pool.py`. Hot traffic moved to RC because WRITE_WITH_IMM needs RC (UD supports SEND only). |
| Top-K compression of cold traffic | Replaced by scuffedQuant (Hadamard rotation + Lloyd-Max + QJL), `middleware/rdma_tensor_cache/scuffed_quant.py`. |
| KV migration protocol | Not built. Deferred. |
| Joint training/inference scheduler | Not built. Deferred; the main focus is the inference transport. |
| Security mitigations | Bounded-length parsing and the fixed-size QP bootstrap from Update 5. SR-IOV isolation and rkey rotation not built. |

## Next steps as written, status today

| Proposed deliverable | Status | Evidence |
|---|---|---|
| RoCE/iWARP config, vLLM distributed setup, baselines | partial | SoftRoCE runs on Chimera/Cerberus; hardware RoCEv2 on the ConnectX-4 towers (backlog draft `Update8-InfrastructureRDMATesting`). iWARP never configured: the X710 has no iWARP. |
| Zero-copy library, CUDA Top-K kernels, multi-QP | partial | Multi-QP pool exists (Python, then C in `middleware/libscuffedverbs/` and `middleware/libscuffedfabric/`). Top-K kernels dropped for scuffedQuant. |
| Access tracking, classifier, monitoring | partial | Classifier and telemetry exist; access tracking inside vLLM does not. |
| Multi-queue scheduler, end-to-end vLLM integration | partial | PMP controller exists; vLLM connector in `middleware/vllm_plugin/` is new and not yet measured end to end. |
| Benchmarks, ablations, stress tests | open | |
| Joint training/inference, KV migration, continuous self-training | deferred | Main focus is the inference transport (Aug 2026). |

## Run it

- [`notebooks/00_environment_check.ipynb`](../../notebooks/00_environment_check.ipynb): verifies rxe0 / ConnectX, libfabric providers, pyverbs, builds the native libs, runs pytest.
- [`notebooks/01_hol_blocking.ipynb`](../../notebooks/01_hol_blocking.ipynb): the head-of-line blocking claim the proposal opens with.
- [`notebooks/04_wfa_and_policy.ipynb`](../../notebooks/04_wfa_and_policy.ipynb): the WFA classifier with learned weights.
- [`notebooks/06_vllm_disagg_ttft.ipynb`](../../notebooks/06_vllm_disagg_ttft.ipynb): end-to-end TTFT.

## Corrections

- "Cerberus: Intel X710 10GbE with hardware iWARP": the X710 does not support iWARP (only the X722 does). Cerberus runs SoftRoCE.
- "Chimera: potential Mellanox ConnectX-6 100GbE upgrade": never happened. Chimera runs SoftRoCE on the Aquantia AQC107.
- "Hot tensors send via dedicated UD queue pairs": UD supports only SEND up to path MTU, no RDMA WRITE or WRITE_WITH_IMM. The built design uses RC for both classes.
- "sub-10 microsecond latency versus 50-100 microseconds with TCP": a hardware RoCE figure. SoftRoCE on this testbed measured about 190 us round trip with `ib_write_lat` (backlog draft `Update8-InfrastructureRDMATesting`).
