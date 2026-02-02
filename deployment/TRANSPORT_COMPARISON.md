# Transport Protocol Comparison for Distributed LLM Inference

This document compares different transport options tested for the ScuffedRDMA project.

## Test Environment

| Machine | IP | GPUs | NIC Hardware |
|---------|-----|------|--------------|
| Chimera | 192.168.1.150 | 3× RTX 3090 (72GB) | Aquantia 10G, Realtek 2.5G |
| Cerberus | 192.168.1.242 | 2× RTX 5090 (64GB) | Intel X710 10G |

## Protocol Comparison

| Protocol | Latency | Bandwidth | CPU Overhead | Hardware Required | GPUDirect |
|----------|---------|-----------|--------------|-------------------|-----------|
| Soft-RoCE | ~10μs | TBD | High | Any NIC | No |
| rdma-tas | ~5μs | TBD | Medium | DPDK NIC | No |
| Tesla TTPoe | ~1-2μs | TBD | Near-zero | Any Ethernet | No |
| Hardware RoCE | <2μs | ~100 Gb/s | Near-zero | Mellanox ConnectX | Yes |

## Test Results Summary

### 1. Soft-RoCE (RXE)
- **Status:** Testing in progress
- **Setup:** See `VERSION_2_SOFTROCE.md`
- **Results:** See `test-results/SOFTROCE_TEST_RESULTS.md`

### 2. rdma-tas (DPDK)
- **Status:** Build in progress
- **Setup:** See `test-results/RDMA_TAS_SETUP.md`
- **Results:** TBD

### 3. Tesla TTPoe
- **Status:** Build in progress
- **Setup:** See `test-results/TTPOE_SETUP.md`
- **Results:** TBD

## Recommendations

| Use Case | Recommended Protocol | Reason |
|----------|---------------------|--------|
| Development/Testing | Soft-RoCE | No hardware required |
| Production (no Mellanox) | TTPoe or TCP | Lower CPU overhead |
| Production (with Mellanox) | Hardware RoCE | Best latency + GPUDirect |
| High-throughput bulk transfer | rdma-tas | DPDK optimization |

## Notes

- GPUDirect RDMA requires Mellanox ConnectX NICs + MOFED drivers
- Current cluster lacks Mellanox hardware, limiting to software options
- For vLLM multi-node, NCCL can use any of these transports via configuration
