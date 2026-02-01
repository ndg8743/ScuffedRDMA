# Adaptive RDMA Optimization for Distributed LLM Workloads

MS Computer Science Thesis Project - SUNY New Paltz

**Author:** Nathan Gopee
**Advisors:** Dr. Wafi Danesh & Dr. Ashley Suchy

## Overview

This repository contains documentation and research materials for developing an adaptive RDMA middleware that optimizes distributed LLM inference. The project introduces runtime tensor classification (hot/cold) and dual-path RDMA routing to reduce Time-To-First-Token (TTFT) latency in frameworks like vLLM.

## Repository Structure

```
ScuffedRDMA/
├── Propsal/                    # Thesis proposal documents
│   ├── prepropasal.tex
│   ├── propsal.tex
│   └── revised_proposal_v2.tex/pdf
│
├── Update1/                    # Week 1: Hardware Setup & Price Analysis
│   ├── update1.tex             # LaTeX source
│   ├── update1.pdf             # Compiled document
│   └── *.png, *.jpg            # Hardware photos, purchase receipts, price comparisons
│
├── Update2/                    # Week 2: Implementation Plan
│   ├── update2.tex             # LaTeX source
│   ├── update2.pdf             # Compiled document
│   └── image.png
│
├── References/                 # Research papers and documentation
│   ├── NIPS-2017-attention-is-all-you-need-Paper.pdf
│   ├── summit_workshop_CUDA-Aware-MPI.pdf
│   ├── WP-Big-Insights-with-Mellanox-Infiniband-RDMA.pdf
│   └── ...
│
└── .gitignore
```

## Hardware Setup

### Lab (SUNY New Paltz)
- **Cerberus:** 2x RTX 5090 (32GB each)
- **Chimera:** 3x RTX 3090 (24GB each)
- **Network:** 10GbE with SoftRoCE

### Home Lab
- **Tower 1 (Windows):** Ryzen 9 7950X, 192GB DDR5, RTX 5070 Ti (16GB)
- **Tower 2 (Proxmox):** Xeon E5-2697A v4, 128GB DDR4, 2x Tesla V100 32GB, 40TB+ storage
- **Network:** 100GbE Mellanox ConnectX-4 with SoftRoCE

## Key Technologies

- **vLLM** - LLM inference engine with PagedAttention
- **NIXL** - NVIDIA's communication abstraction (NVLink/RDMA/TCP)
- **Tesla TTPoe** - Low-latency RDMA over Ethernet (~1-2μs)
- **GPUDirect RDMA** - Direct GPU-NIC communication (V100/5090 supported)
- **SoftRoCE** - Software RDMA over Converged Ethernet

## Building

Requires MiKTeX or TeX Live with standard packages.

```bash
cd Update1 && pdflatex update1.tex
cd Update2 && pdflatex update2.tex
```

## Related Links

- [vLLM Project](https://github.com/vllm-project/vllm)
- [Tesla TTPoe](https://github.com/teslamotors/ttpoe)
- [NVIDIA Dynamo (NIXL)](https://github.com/NVIDIA/Dynamo)
- [Custom X99 BIOS with ReBAR](https://github.com/ndg8743/x99-udp4-rebar)
