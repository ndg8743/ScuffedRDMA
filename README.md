# Adaptive RDMA Optimization for Distributed LLM Workloads

MS Computer Science Thesis Project - SUNY New Paltz

**Author:** Nathan Gopee
**Advisors:** Dr. Wafi Danesh & Dr. Ashley Suchy

## Overview

This repository contains documentation, research, middleware prototypes, and deployment configurations for an adaptive RDMA middleware that optimizes distributed LLM inference on consumer and datacenter GPU hardware. The project introduces runtime tensor classification (hot/cold via WFA classifier), dual-path RDMA routing, and lock-free C++/Rust transport to reduce Time-To-First-Token (TTFT) latency in frameworks like vLLM.

**Target:** 30-50% TTFT reduction on distributed 7B+ models.

---

## Hardware

### Lab Cluster (SUNY New Paltz)
| Node | GPUs | VRAM | NIC | RDMA |
|------|------|------|-----|------|
| **Cerberus** | 2x RTX 5090 | 64 GB | Intel X710 10GbE | SoftRoCE, iWARP (SR-IOV) |
| **Chimera** | 3x RTX 3090 | 72 GB | Aquantia AQC107 10GbE | SoftRoCE only |

### Home Lab
| Node | GPUs | VRAM | NIC | RDMA |
|------|------|------|-----|------|
| **Tower 1** (Windows) | RTX 5070 Ti | 16 GB | Mellanox ConnectX-4 100GbE | Hardware RoCEv2 |
| **Tower 2** (Proxmox) | 2x Tesla V100 | 64 GB | Mellanox ConnectX-4 100GbE | Hardware RoCEv2, GPUDirect |

### Total Cluster: 8 GPUs, 216 GB VRAM, mixed 10G/100G networking

---

## Repository Structure

```
ScuffedRDMA/
├── Updates/                         # 15 research updates (LaTeX + PDF)
│   ├── Update1-HardwareSetup/
│   ├── Update2-ImplementationPlan/
│   ├── Update3-InfrastructureRDMATesting/
│   ├── Update4-FlashAttention3Blackwell/
│   ├── Update5-GPToss120bBenchmarks/
│   ├── Update6-TransportMiddleware/
│   ├── Update7-ThesisProposal/
│   ├── Update8-TensorCacheArchitecture/
│   ├── Update9-WFAClassifierValidation/
│   ├── Update10-MechanisticInterpretability/
│   ├── Update11-WorkFirstScheduling/
│   ├── Update12-USB4Investigation/
│   ├── Update13-LockFreeMiddleware/
│   ├── Update14-KokkosRemoteSpaces/
│   └── Update15-ArchitectureComparison/
├── Drafts/                          # Thesis draft
├── Proposal/                        # Thesis proposal
├── References/                      # Research papers
├── middleware/                      # Python middleware prototype
│   ├── transport_base.py            # Abstract transport interface
│   ├── tcp_transport.py             # TCP backend
│   ├── roce_transport.py            # RoCE backend
│   ├── ttpoe_transport.py           # Tesla TTPoe backend
│   ├── selector.py                  # Transport selector
│   ├── nccl_config.py               # NCCL configuration
│   └── rdma_tensor_cache/           # Tensor cache subsystem
│       ├── cache.py                 # KV cache management
│       ├── precision.py             # FP32/FP16/BF16/MXFP4 routing
│       ├── prefetch.py              # Adaptive prefetcher
│       ├── quantization.py          # Precision conversion
│       ├── vllm_connector.py        # vLLM integration
│       └── sae_steering.py          # SAE feature steering
├── deployment/                      # Docker configs & deployment guides
│   ├── vllm/                        # Standard vLLM deployment
│   ├── vllm-gptoss/                 # GPT-oss-120b with MXFP4
│   ├── multi-node/                  # Multi-node head/worker configs
│   ├── chimera/                     # Chimera-specific config
│   ├── cerberus/                    # Cerberus-specific config
│   └── test-results/                # Benchmark results
├── benchmarks/                      # Benchmark scripts
├── scripts/                         # Setup & diagnostic scripts
└── ucx/                             # UCX toolkit (submodule)
```

---

## Progress Tracker

### Tested & Validated

| What | Result | Update | Date |
|------|--------|--------|------|
| Cluster hardware setup | 4 nodes, 8 GPUs operational | 1 | Jan 2026 |
| SoftRoCE RDMA | 0.92 Gb/s BW, 189.6 us latency on 10GbE | 3 | Feb 2026 |
| FlashAttention 3 Blackwell fix | +15.5% throughput, -14.3% latency on RTX 5090 | 4 | Feb 2026 |
| GPT-oss-120b inference | 104.4 tok/s on 3x RTX 3090 (TCP) | 5 | Feb 2026 |
| Python transport middleware | 3 backends (TCP, RoCE, TTPoe), selector working | 6 | Feb 2026 |
| WFA classifier (H100 Colab) | Access patterns instrumented on LLM4Decompile | 9 | Feb 2026 |
| Activation sparsity measurement | 99.3-99.999% sparse across tested models | 10 | Feb 2026 |
| UCX v1.17.0 cross-node | 111.86 MB/s tag_bw over 2.5G SoftRoCE | 13, 14 | Feb 2026 |

### Designed & Documented (Awaiting Implementation)

| What | Status | Update | Blocking On |
|------|--------|--------|-------------|
| Lock-free C++/Rust middleware | Architecture spec complete, 6 crates designed | 13 | Implementation time |
| SPSC ring buffer (Disruptor-style) | Cache-line aligned design, bitmask indexing | 11, 13 | C++ implementation |
| Tensor cache with RDMA | Rust crate structure, 6 modules defined | 8 | C++/Rust migration |
| WFA hot/cold classifier (native) | <100 ns target (vs 10 us Python) | 13 | Rust AtomicU64 impl |
| GPUDirect RDMA (V100 + CX-4) | nvidia-peermem setup documented | 14 | Tower 2 VM config |
| SR-IOV NIC virtualization | ConnectX-4 VF passthrough designed | 14 | Proxmox IOMMU setup |
| Kokkos Remote Spaces integration | NVSHMEM + MPI backends analyzed | 14 | NVSHMEM install on V100 |
| USB4/Thunderbolt RDMA | 8-16x over 2.5G SoftRoCE projected | 12 | TB3 AIC for Chimera |
| PyO3 zero-copy bridge | 200 ns boundary crossing target | 13 | Rust crate completion |

### Planned Benchmarks (Not Yet Run)

| Benchmark | What | Hardware | Update |
|-----------|------|----------|--------|
| MDLM generation sweep | Perplexity vs steps (T=32..1024) | RTX 3090 | 15 |
| SEDD generation sweep | Score-entropy comparison vs MDLM | RTX 3090 | 15 |
| Mamba-2.8B throughput | Constant tok/s at 1K-128K context | V100, RTX 3090 | 15 |
| Granite 4 hybrid | KV cache size vs pure Transformer | V100 | 15 |
| GPT-oss RDMA vs TCP | vLLM tensor-parallel over ConnectX-4 | Tower 1+2 | 5 |
| Kokkos randomaccess/stream | NVSHMEM vs MPI one-sided | V100 pair | 14 |
| ucx_perftest CUDA-aware | gdr_copy vs cuda_copy on V100 | Tower 2 | 14 |
| Three-way architecture | AR vs Diffusion vs SSM full comparison | All nodes | 15 |

---

## Timeline (January 2026 - December 2026)

### Completed: January - February 2026

```
Jan 31  Initial commit, hardware setup, cost analysis (Update 1)
Jan 31  Implementation plan, vLLM ecosystem survey (Update 2)
Feb 01  References library, PDF organization
Feb 02  Infrastructure testing: SoftRoCE 0.92 Gb/s, TTPoe build (Update 3)
Feb 02  FlashAttention 3 Blackwell fix: +15.5% throughput (Update 4)
Feb 02  GPT-oss-120b benchmarks: 104.4 tok/s TCP baseline (Update 5)
Feb 02  Transport middleware: TCP/RoCE/TTPoe selector (Update 6)
Feb 02  vLLM Docker configs for multi-node deployment
Feb 09  Thesis proposal: 7 blocking issues formalized (Update 7)
Feb 09  Tensor cache architecture: precision pipeline designed (Update 8)
Feb 09  WFA classifier: H100 validation on LLM4Decompile (Update 9)
Feb 09  Python middleware prototype + benchmark scripts committed
Feb 10  Mechanistic interpretability: sparsity-aware transport (Update 10)
Feb 13  Work-first scheduling: Cilk-inspired tensor transport (Update 11)
Feb 13  USB4 investigation: Thunderbolt RDMA feasibility (Update 12)
Feb 14  Lock-free C++/Rust migration plan (Update 13)
Feb 14  Kokkos Remote Spaces + GPUDirect + SR-IOV + UCX (Update 14)
Feb 15  Architecture comparison: AR vs Diffusion vs Mamba (Update 15)
```

### In Progress: March - April 2026

```
        Download and benchmark MDLM, SEDD, Mamba-2.8B on cluster GPUs
        GPUDirect RDMA setup on Tower 2 (nvidia-peermem + V100 + CX-4)
        SR-IOV VF passthrough in Proxmox for GPU VM
        Hardware RoCEv2 testing on ConnectX-4 (target: <5 us latency)
        UCX CUDA-aware perftest (gdr_copy on V100)
        Begin C++/Rust lock-free middleware implementation
          - SPSC ring buffer with cache-line alignment
          - ibv_poll_cq busy-poll completion engine
          - DashMap-style sharded WFA classifier
```

### Target: May - July 2026

```
        Complete lock-free middleware core (C++ RDMA + Rust classifier)
        PyO3 bridge: zero-copy Rust<->Python for vLLM integration
        Kokkos Remote Spaces build with NVSHMEM on V100
        Run Kokkos benchmarks: randomaccess, stream, cgsolve
        Three-way architecture benchmark (AR vs Diffusion vs SSM)
        USB4/Thunderbolt RDMA deployment (if TB3 AIC acquired)
        Tensor cache integration with vLLM disaggregated prefill/decode
        Begin thesis draft: merge Updates into coherent chapters
```

### Target: August - October 2026

```
        Full pipeline validation: vLLM + RDMA middleware end-to-end
        TTFT reduction measurement (target: 30-50% on 7B+ models)
        Multi-node elastic scheduling with Mamba state migration
        Comparative analysis: middleware overhead vs throughput gain
        Thesis writing: results, analysis, conclusions
```

### Target: November - December 2026

```
        Thesis defense preparation
        Final benchmarks and reproducibility verification
        Thesis submission
```

---

## Key Results So Far

| Metric | Value | Notes |
|--------|-------|-------|
| SoftRoCE bandwidth | 0.92 Gb/s | 10GbE, 3.3x over WiFi baseline |
| SoftRoCE latency | 189.6 us | Software RDMA, target <5 us with hardware |
| FA3 Blackwell throughput | +15.5% | Lazy import fix for RTX 5090 |
| FA3 Blackwell latency | -14.3% | Same fix |
| FA3 Blackwell memory | -9.7% | Same fix |
| GPT-oss-120b (TCP) | 104.4 tok/s | 3x RTX 3090, MXFP4 quantization |
| UCX cross-node | 111.86 MB/s | tag_bw over 2.5G SoftRoCE |
| Activation sparsity | 99.3-99.999% | Enables sparse tensor transfer |
| KV cache at 128K ctx | 16 GB | 7B Transformer, dominates VRAM |
| Mamba state at 128K ctx | 13 MB | 1,260x smaller than KV cache |

## Key Technologies

| Technology | Role | Status |
|-----------|------|--------|
| **vLLM** | LLM inference engine (PagedAttention) | Deployed, benchmarked |
| **SoftRoCE** | Software RDMA over Ethernet | Tested (189.6 us) |
| **Hardware RoCEv2** | ConnectX-4 kernel-bypass RDMA | Pending deployment |
| **GPUDirect RDMA** | Direct GPU-NIC DMA (nvidia-peermem) | Documented, pending test |
| **UCX v1.17.0** | Transport abstraction (rc_mlx5, tcp, cuda) | Installed, cross-node tested |
| **Kokkos Remote Spaces** | PGAS distributed GPU memory | Analyzed, pending build |
| **Tesla TTPoe** | Low-latency RDMA over Ethernet | Kernel modules built |
| **NVSHMEM** | GPU-initiated RDMA (V100) | Pending install |
| **SR-IOV** | NIC virtualization for Proxmox | Designed, pending config |
| **MDLM / SEDD** | Diffusion LLMs (no KV cache) | Pending download + test |
| **Mamba** | SSM (constant-size state) | Pending download + test |

---

## Building Updates

Requires TeX Live with standard packages.

```bash
cd Updates/Update15-ArchitectureComparison
pdflatex update15.tex && bibtex update15 && pdflatex update15.tex && pdflatex update15.tex
```

## Links

- [vLLM](https://github.com/vllm-project/vllm)
- [Tesla TTPoe](https://github.com/teslamotors/ttpoe)
- [NVIDIA Dynamo (NIXL)](https://github.com/NVIDIA/Dynamo)
- [Kokkos Remote Spaces](https://github.com/kokkos/kokkos-remote-spaces)
- [UCX (OpenUCX)](https://github.com/openucx/ucx)
- [MDLM](https://github.com/kuleshov-group/mdlm)
- [SEDD](https://github.com/louaaron/Score-Entropy-Discrete-Diffusion)
- [Custom X99 BIOS with ReBAR](https://github.com/ndg8743/x99-udp4-rebar)
