# ScuffedRDMA Deployment Guide

Comprehensive documentation for RDMA and low-latency transport options.

## Quick Reference

| Technology | Latency | Production Ready | Hardware Required |
|------------|---------|------------------|-------------------|
| Hardware RoCE | <2μs | ✓ Yes | Mellanox ConnectX |
| Tesla TTPoe | 1-2μs | ✓ Yes | Any Ethernet |
| Soft-RoCE | ~10μs | ✗ Deprecated | Any NIC |
| rdma-tas | ~5μs | ⚠ Research | DPDK NIC |
| Sideway (Rust) | N/A | ⚙ Tooling | Any RDMA NIC |

## Documentation Index

### Transport Protocols

| File | Description |
|------|-------------|
| `VERSION_1_SRIOV_GPUDIRECT.md` | SR-IOV + GPUDirect RDMA (Mellanox) |
| `VERSION_2_SOFTROCE.md` | Soft-RoCE (deprecated, for reference) |
| `VERSION_3_HARDWARE_ROCE.md` | Hardware RoCE with Mellanox NICs |
| `VERSION_4_TTPOE.md` | Tesla TTPoe kernel modules |
| `VERSION_5_SIDEWAY_RUST.md` | Rust RDMA library |
| `VERSION_6_RDMA_TAS.md` | RDMA over TAS/DPDK |

### Analysis

| File | Description |
|------|-------------|
| `RDMA_TECHNOLOGIES_COMPREHENSIVE_REPORT.md` | Full industry analysis (Feb 2026) |
| `TRANSPORT_COMPARISON.md` | Quick comparison matrix |

### Docker Deployment

| File | Description |
|------|-------------|
| `docker-compose.head.yaml` | vLLM head node (Chimera) |
| `docker-compose.worker.yaml` | vLLM worker node (Cerberus) |

## Cluster Configuration

| Machine | IP | GPUs | Primary NIC |
|---------|-----|------|-------------|
| Chimera | 192.168.1.150 | 3× RTX 3090 (72GB) | Aquantia 10G |
| Cerberus | 192.168.1.242 | 2× RTX 5090 (64GB) | Intel X710 10G |

## Recommended Path

### For Development/Testing (Current Hardware)
1. Use standard TCP with NCCL (simplest)
2. Or Soft-RoCE for RDMA semantics (deprecated but works)

### For Production (With Mellanox NICs)
1. Hardware RoCE with GPUDirect RDMA
2. Follow `VERSION_3_HARDWARE_ROCE.md`

### For Custom Low-Latency Clusters
1. Tesla TTPoe kernel modules
2. Follow `VERSION_4_TTPOE.md`

### For Rust Tooling
1. Sideway library for monitoring/orchestration
2. Follow `VERSION_5_SIDEWAY_RUST.md`

## Quick Start

### Option A: Standard NCCL (Recommended for AI)
```bash
# No special setup required
export NCCL_DEBUG=INFO
# vLLM will use TCP or available RDMA automatically
```

### Option B: Hardware RoCE (Mellanox Required)
```bash
# 1. Install MOFED
# 2. Install CUDA (after MOFED!)
# 3. Load nvidia-peermem
# 4. Configure NCCL:
export NCCL_IB_HCA=mlx5_0
export NCCL_DEBUG=INFO
```

### Option C: Tesla TTPoe
```bash
git clone https://github.com/teslamotors/ttpoe.git
cd ttpoe && make all
sudo insmod modttpoe/modttpoe.ko dev=eth0 verbose=2
```

## Repository Links

- **Tesla TTPoe:** https://github.com/teslamotors/ttpoe
- **rdma-tas:** https://github.com/mani-shailesh/rdma-tas
- **Sideway (Rust):** https://github.com/RDMA-Rust/sideway
- **UEC Spec:** https://ultraethernet.org/
- **OCP Falcon:** https://github.com/opencomputeproject/OCP-NET-Falcon

## Author

Nathan Gopee - SUNY New Paltz MS Computer Science Thesis

**Last Updated:** February 2, 2026
