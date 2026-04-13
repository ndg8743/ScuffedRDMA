# Deployment

Docker configs, benchmark harnesses, and deployment notes for the ScuffedRDMA cluster
(Chimera 192.168.1.150, 3x RTX 3090 / Cerberus 192.168.1.242, 2x RTX 5090).

Scope is roughly three things: (1) vLLM + OpenWebUI stacks that actually run, (2)
TCP-vs-RDMA benchmark harnesses for multi-node gpt-oss-120b, (3) a survey of RDMA
transport options written during Week 3 to decide what to build against.

## Subfolders

Each has its own README - see those for details, don't duplicate here.

| Path | Contents |
|------|----------|
| `chimera/` | Head node compose: OpenWebUI + Ollama + vLLM. |
| `cerberus/` | Worker node compose. No README, single file, see head node docs. |
| `multi-node/` | TCP vs RDMA benchmark for gpt-oss-120b split across both nodes. |
| `vllm/` | Standalone vLLM server compose for OpenWebUI integration. |
| `vllm-gptoss/` | vLLM compose pinned to the `gptoss` image (MXFP4 / FlashInfer). |
| `benchmarks/` | `run_all_benchmarks.sh` and `benchmark_vllm_gptoss.py` - Ollama vs vLLM vs vLLM+RDMA. |
| `patches/` | `vllm-blackwell-fa3.patch` and writeup for the RTX 5090 FA3 issue (vllm#22279). |
| `test-results/` | Measured numbers. Currently just Soft-RoCE over 10G and WiFi. |

## Top-level files

| File | What it is |
|------|-----------|
| `docker-compose.head.yaml` / `docker-compose.worker.yaml` | Multi-node vLLM over Ray. Duplicated in `multi-node/`; the top-level copies are the canonical ones referenced by older runs. |
| `start-vllm.sh` | One-shot docker-run wrapper for a single-node vLLM on Chimera. Superseded by `vllm/docker-compose.yaml` but still works. |
| `RDMA_TECHNOLOGIES_COMPREHENSIVE_REPORT.md` | Feb 2026 survey of seven RDMA acceleration approaches (TTPoe, UEC, Soft-RoCE, Sideway, rdma-tas, hardware RoCE, NCCL GDR). Source material behind the VERSION_* files. |
| `TRANSPORT_COMPARISON.md` | One-page comparison table distilled from the report. Some "TBD" entries. |
| `VERSION_1_SRIOV_GPUDIRECT.md` | SR-IOV + GPUDirect setup notes. Requires Mellanox - not owned yet. |
| `VERSION_2_SOFTROCE.md` | Soft-RoCE / rxe setup. This is what the cluster actually runs. |
| `VERSION_3_HARDWARE_ROCE.md` | Hardware RoCE on ConnectX. Aspirational. |
| `VERSION_4_TTPOE.md` | Tesla TTPoe kernel modules. Not deployed. |
| `VERSION_5_SIDEWAY_RUST.md` | Rust ibverbs wrapper. Reference only. |
| `VERSION_6_RDMA_TAS.md` | rdma-tas over DPDK. Reference only. |

The VERSION_*.md files are historical design exploration from one Week 3 commit and
haven't been touched since. Only VERSION_2 (Soft-RoCE) reflects what's actually
running. The other five are "what we'd do if we had the hardware / cared enough"
notes. Recommendation below.

## Cluster

| Node | IP | GPUs | Primary NIC |
|------|----|------|-------------|
| Chimera | 192.168.1.150 | 3x RTX 3090 (72GB) | Aquantia 10G (`enp71s0`) |
| Cerberus | 192.168.1.242 | 2x RTX 5090 (64GB) | Intel X710 10G (`eno2np1`) |

Neither has Mellanox, so GPUDirect RDMA is not available. Soft-RoCE (`rxe0` over
the 10G link) is the current RDMA path; TCP/NCCL is the baseline.

## Stale / cleanup candidates

- `VERSION_1`, `VERSION_3`, `VERSION_4`, `VERSION_5`, `VERSION_6` - recommend moving
  these into a `versions/` subfolder (or deleting outright, since the comprehensive
  report already covers the same ground with more context). Keeping them loose at
  the top level makes the directory look busier than it is.
- Top-level `docker-compose.head.yaml` / `docker-compose.worker.yaml` vs the copies
  in `multi-node/` - one pair should win. The `multi-node/` versions are the ones
  the benchmark script actually uses.
- `TRANSPORT_COMPARISON.md` has TBD rows that never got filled in. Either finish it
  or fold its table into the comprehensive report and delete.
- `start-vllm.sh` is functionally replaced by `vllm/docker-compose.yaml`.

## Author

Nathan Gopee, SUNY New Paltz MS thesis.
