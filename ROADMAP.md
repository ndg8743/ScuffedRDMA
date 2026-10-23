# Roadmap

Status of every next step from the proposal through Update 8, checked against the code, results and tests in this repo (22 Oct 2026). Per-update detail and evidence: `Updates/*/README.md`.

**Legend.** built: code and tests in the repo, runs here. cluster: built, needs a run on Cerberus / Chimera (or the towers) to produce thesis numbers. gpu: built, needs one machine with an NVIDIA GPU (notebook 08). open: not built. deferred / dropped: out of the current plan.

## Critical path to the defense

1. **Cluster runs of notebooks 00 to 03** (Cerberus client, Chimera server, SoftRoCE; then Tower 1 and Tower 2 over ConnectX-4). Fills Update 8 E1 to E5 and replaces the withdrawn 8 µs figure. *cluster*
2. **Single-GPU end-to-end run** (notebook 08 on the desktop GPU after `scripts/local_gpu/setup_gpu_env.sh`): vLLM prefill + decode with the connector on one card, greedy match, TTFT / ITL. Fills Update 8 E7. *gpu*
3. **vLLM disaggregated serving with ScuffedRdmaConnector over FabricBlobChannel, TTFT / ITL against NIXL on UCX and on its LIBFABRIC backend** (notebook 06). Update 8 E8. *cluster*
4. **Update 8 tables** from the JSON (draft text done), then the related-work chapter in `Updates/Drafts/draft1.tex` (RDT, eRNIC, SoL, the libfabric / UCX / DOCA taxonomy, NIXL's libfabric backend, fabric-lib, and the libfabric results). *open*
5. **NIXL + Ray RDT view-count sweep with competing hot traffic** (Update 7, step 2). *open*

## Transport

| Item | From | Status | Where |
|---|---|---|---|
| Dual QP pool, Python / pyverbs | U2, U4 | built; completion status now checked | `middleware/rdma_tensor_cache/dual_qp_pool.py` |
| Dual pool on libfabric (MSG / RDM per class, cntr vs CQ, wait objects) | U7 step 4 | built, tested on tcp / tcp;ofi_rxm / shm | `middleware/libscuffedfabric/` |
| Native libibverbs pool, same API and bench | U4 step 3, U7 step 4 | built (compile-checked here) | `middleware/libscuffedverbs/` |
| Mixed hot/cold head-of-line benchmark | U4 step 1, U5 | cluster | `sf_bench -m hol`, notebook 01 |
| Completion-signaling microbenchmark, instructions per post | U7 step 3 | cluster | `sf_bench -m sig`, notebook 02 |
| libfabric vs libibverbs comparison | U7 step 4, U8 | cluster | notebook 03 |
| Per-class telemetry, QP error / reconnect / TCP fallback, Prometheus | U2, U7 step 5 | built | `middleware/telemetry.py` |
| NCCL net plugin | U5-2 | builds; NCCL + vLLM run open | `middleware/nccl_plugin/` |
| UCCL vs ScuffedRDMA mixed-traffic p99 | U5-2 | open | `benchmarks/test_arch/stack-draft/bench_uccl_p2p.py` |
| NVSHMEM + OpenMPI GPU-initiated puts | U5-2 | open | |
| NUMA-aware buffer pool | U2 | open (both lab nodes are single-socket) | |
| perftest / sockperf baseline | U2 | open | |
| GPUDirect RDMA on Tower 2 | U1 | open (PVE kernel lacks `CONFIG_INFINIBAND_PEER_MEM`) | |

## Routing and control

| Item | From | Status | Where |
|---|---|---|---|
| WFA classifier, static thresholds + phase detection | U2 | built | `wfa_classifier.py` |
| WFA with learned transition weights, synthetic validation | U2, proposal | built; real-trace training is cluster | `wfa_learner.py`, notebook 04 |
| Rule-Node Expression Tree policy engine | proposal | built | `middleware/policy/` |
| PMP bang-bang controller | U4 | built | `pmp_controller.py` |
| PMP storage-pressure arm | U6 step 3 | built | `pmp_controller.py`, notebook 07 |

## Compression and storage

| Item | From | Status | Where |
|---|---|---|---|
| scuffedQuant (Hadamard + Lloyd-Max + 256-bit QJL), bit-packed wire format | U4 | built | `scuffed_quant.py`, notebook 05 |
| Per-architecture scuffedQuant (Transformer, Mamba, Granite 4 hybrid, MoE) | U5-2 | built, results on both nodes | `benchmarks/test_arch/` |
| NVMe spill / retrieve with coalescing, WFA-gated | U6 steps 1-2 | built; NVMe sweep is cluster | `storage_tier.py`, notebook 07 |
| sandook on the cluster; GPFS tier on Hydra | U5-2, U6 | open | |

## Serving integration

| Item | From | Status | Where |
|---|---|---|---|
| ScuffedRdmaConnector on vLLM V1 KV connector API | U2, U4 step 2 | built, 32 tests; signatures, import and an end-to-end run through vLLM's own base class pass against vLLM 620e8924 and 0.24.0 | `middleware/vllm_plugin/` |
| Connector with KV caches on the GPU; vLLM prefill + decode on one card | U8 E7 | gpu (`pytest -m gpu`, notebook 08) | `tests/test_gpu.py`, `scripts/local_gpu/` |
| TTFT / ITL vs NIXL (UCX and LIBFABRIC backends) and single node | U2, U8 E8 | cluster | notebook 06, `benchmarks/vllm_disagg/launch.sh` (`CONNECTOR=nixl-libfabric`) |
| 7B / 13B / 70B sweep and ablations | U2 phase 5 | partly cluster (WFA vs static: nb 04; dual vs single: nb 01); model-size sweep open | |

## Deferred or dropped

Training-side all-reduce and FSDP (U2 phase 4), RISC-V assembly LLM (U2), ScuffedKernels / ScuffedSearch (U3), MXFP4 adaptive quantization (U3 pillar 3, superseded by scuffedQuant), precision and prefetch pillars (U3, code kept, not run), KV migration protocol and joint scheduler (proposal). The six UCX pull requests (#11304 closed, #11305 to #11309 open, review required) were not merged and are no longer part of the contribution.

## Withdrawn numbers

- 8 µs cross-node latency: pyverbs pool did not check `wc.status`. Re-run in notebook 01.
- 4x vs FP16 compression: was vs FP32; 2x vs FP16 at head_dim 64.
- SoftRoCE bandwidth, single-QP p50, dual-QP overhead, FA3 speedup, gpt-oss tok/s: README rows pointed at sources that do not hold them. Re-measured by notebooks 01 to 03 where they matter.
