# ScuffedRDMA

Adaptive RDMA middleware for distributed LLM inference.

MS Computer Science thesis project, SUNY New Paltz.
**Author:** Nathan Gopee &nbsp;&nbsp;•&nbsp;&nbsp; **Advisors:** Dr. Wafi Danesh, Dr. Ashley Suchy

The thesis targets the KV-transfer term in disaggregated prefill/decode serving:
tensor-aware RDMA routing, dual QP pools, a WFA hot/cold classifier, PMP bang-bang
bandwidth control, and scuffedQuant 3-bit KV compression. Goal is 30–50% TTFT
reduction on 7B+ models running over consumer-tier 10GbE/100GbE instead of
datacenter InfiniBand.

---

## What lives in this repo

This repo holds the thesis core plus a sibling full-stack app (RISVLLM) that shares
the cluster hardware. They are not a single codebase. Read the thesis core first.

### 1. Thesis core — `middleware/` + `Updates/` + `benchmarks/` + `deployment/`

The actual RDMA middleware. This is what the thesis defends.

| Piece | Where | What it does |
|---|---|---|
| Transport abstractions | `middleware/transport_base.py`, `tcp_transport.py`, `roce_transport.py`, `ttpoe_transport.py`, `selector.py`, `nccl_config.py` | Common interface over TCP, SoftRoCE, Tesla TTPoe. Used by benchmarks and by the tensor cache. |
| Tensor cache + RDMA data path | `middleware/rdma_tensor_cache/` | Dual QP pool, WFA classifier, PMP controller, scuffedQuant (PolarQuant + QJL), precision router, prefetcher, vLLM connector. This is the Update 4 subject. |
| Research updates | `Updates/Update1-HardwareSetup` → `Updates/Update4-UCX` | LaTeX + PDF for each update. Also `Updates/Proposal/` and `Updates/Drafts/`. |
| Benchmarks | `benchmarks/` | Dual QP, UCX comparison, transport sweep, scuffedQuant (synthetic + real LLM KV + MLX). Results in `benchmarks/results/`. |
| Deployment | `deployment/` | Docker Compose + K8s configs for the lab cluster (cerberus, chimera, multi-node, vllm, vllm-gptoss). Includes the FA3 Blackwell patch for vLLM. |

### 2. `RISVLLM-app/` — Decompilation IDE (separate full-stack app)

A browser-based reverse-engineering IDE (React + Monaco + xterm.js + TinyEMU
WASM) that calls LLM4Decompile-22B running on vLLM on Cerberus. Lives in the
same repo because it shares the hardware, but it has its own Dockerfile, K8s
manifests, and `README.md`. None of the thesis code depends on it.

### Other top-level directories

| Dir | Contents |
|---|---|
| `References/` | Research papers and bookmarks. Referenced by the LaTeX updates. |
| `scripts/` | One-off setup scripts for the cluster (SoftRoCE on Linux, mlxup on Windows, TTPoe load, cluster bring-up). |
| `ucx/` | Submodule pointer to [openucx/ucx](https://github.com/openucx/ucx). Empty until `git submodule update --init`. Only needed for reproducing the Update 4 UCX issue/patch work. |

---

## Hardware

### Lab cluster (SUNY New Paltz)
| Node | GPUs | VRAM | NIC | RDMA |
|------|------|------|-----|------|
| **Cerberus** | 2× RTX 5090 | 64 GB | Intel X710 10GbE | SoftRoCE, iWARP (SR-IOV) |
| **Chimera**  | 3× RTX 3090 | 72 GB | Aquantia AQC107 10GbE | SoftRoCE |

### Home lab
| Node | GPUs | VRAM | NIC | RDMA |
|------|------|------|-----|------|
| **Tower 1** (Windows)  | RTX 5070 Ti   | 16 GB | Mellanox ConnectX-4 100GbE | Hardware RoCEv2 |
| **Tower 2** (Proxmox)  | 2× Tesla V100 | 64 GB | Mellanox ConnectX-4 100GbE | Hardware RoCEv2, GPUDirect |

---

## Research updates

| # | Topic | Dir |
|---|---|---|
| 1 | Hardware setup, cost analysis | `Updates/Update1-HardwareSetup` |
| 2 | Implementation plan, vLLM ecosystem survey | `Updates/Update2-ImplementationPlan` |
| 3 | Tensor cache architecture (precision, prefetch, ScuffedKernels, ScuffedSearch) | `Updates/Update3-TensorCacheArchitecture` |
| 4 | Dual QP + WFA + PMP + scuffedQuant, UCX issue triage, SoftRoCE benchmarks | `Updates/Update4-UCX` |

Each update directory contains `updateN.tex` and the built `updateN.pdf`. Build with:

```bash
cd Updates/Update4-UCX
pdflatex update4.tex && pdflatex update4.tex
```

---

## Key results so far

| Metric | Value | Source |
|---|---|---|
| SoftRoCE bandwidth (Chimera loopback) | 0.92 Gb/s on 10GbE | Update 4 |
| libscuffedrdma single-QP p50 latency (64B) | 12.6 µs | Update 4, `benchmarks/results/ucx_comparison.json` |
| Dual QP overhead vs single QP (p50) | +0.6 µs (SoftRoCE, single-threaded) | Update 4 |
| Cross-node SoftRoCE decode latency (Chimera↔Cerberus) | 8 µs | Update 4 |
| UCX tag_bw cross-node | 111.86 MB/s over 2.5 Gb SoftRoCE | Update 4 |
| scuffedQuant 3-bit top-8 ranking on Granite 3.3-2B (FP32 weights) | 91.1% mean across 40 layers | `benchmarks/results/scuffed_quant_llm.json` |
| scuffedQuant 3-bit top-8 ranking on Granite 3.3-2B (4-bit MLX weights) | 100.0% mean across 40 layers | `benchmarks/results/scuffed_quant_mlx.json` |
| FA3 Blackwell patch on RTX 5090 | +15.5% throughput, −14.3% latency | `deployment/patches/BLACKWELL_FA3_FIX.md` |
| GPT-oss-120b TCP baseline (Chimera, 3× 3090, MXFP4) | 104.4 tok/s | `deployment/benchmarks/` |

---

## Running things

```bash
# RDMA benchmarks (on a node with an RDMA device)
python benchmarks/benchmark_dual_qp.py
python benchmarks/benchmark_ucx_comparison.py

# scuffedQuant on a real LLM (Granite 3.3-2B)
#   Linux/CUDA or Linux/CPU:
python benchmarks/benchmark_scuffed_quant_llm.py --device cpu
#   Apple Silicon (MLX):
pip install mlx mlx-lm numpy
python benchmarks/benchmark_scuffed_quant_mlx.py
```

## Links

- [vLLM](https://github.com/vllm-project/vllm)
- [UCX (OpenUCX)](https://github.com/openucx/ucx)
- [NVIDIA Dynamo / NIXL](https://github.com/NVIDIA/Dynamo)
- [Tesla TTPoe](https://github.com/teslamotors/ttpoe)
- [TurboQuant (PolarQuant + QJL)](https://arxiv.org/abs/2504.19874)
- [LLM4Decompile](https://github.com/albertan017/LLM4Decompile) — driven by RISVLLM-app
- [Custom X99 BIOS with ReBAR](https://github.com/ndg8743/x99-udp4-rebar)
