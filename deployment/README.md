# Deployment

Docker configs, benchmark harnesses, and deployment notes for the ScuffedRDMA cluster
(Chimera 192.168.1.150, 3x RTX 3090 / Cerberus 192.168.1.242, 2x RTX 5090).

## Subfolders

Each has its own README. See those for details.

| Path | Contents |
|------|----------|
| `chimera/` | Head node compose: OpenWebUI + Ollama + vLLM. |
| `cerberus/` | Worker node compose (single file). |
| `multi-node/` | TCP vs RDMA benchmark for gpt-oss-120b split across both nodes. |
| `vllm/` | Standalone vLLM server compose for OpenWebUI integration. |
| `vllm-gptoss/` | vLLM compose pinned to the `gptoss` image (MXFP4 / FlashInfer). |
| `benchmarks/` | `run_all_benchmarks.sh` and `benchmark_vllm_gptoss.py` (Ollama vs vLLM vs vLLM+RDMA). |
| `patches/` | `vllm-blackwell-fa3.patch` and writeup for vllm#22279 on RTX 5090. |
| `test-results/` | Measured numbers. Currently just Soft-RoCE over 10G and WiFi. |

## Cluster

| Node | IP | GPUs | Primary NIC |
|------|----|------|-------------|
| Chimera | 192.168.1.150 | 3x RTX 3090 (72GB) | Aquantia 10G (`enp71s0`) |
| Cerberus | 192.168.1.242 | 2x RTX 5090 (64GB) | Intel X710 10G (`eno2np1`) |

Neither has Mellanox, so GPUDirect RDMA is not available. Soft-RoCE (`rxe0` over
the 10G link) is the current RDMA path; TCP/NCCL is the baseline.

## Author

Nathan Gopee, SUNY New Paltz MS thesis.
