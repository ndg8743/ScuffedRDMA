# RDMA, ROCE Test in Network with MPI Tools

**Source URL:** https://tech.pansolusi.com/2024/10/31/rdma-roce-test-in-network-with-mpi-tools/
**Date Accessed:** 2026-03-11

**Published:** October 31, 2024
**Source:** Tech Blog Pansolusi

## Overview

This technical guide demonstrates how to test ROCE (RDMA over Converged Ethernet) networks within Kubernetes clusters to ensure low-latency, high-bandwidth performance for AI infrastructure.

## Three-Step Testing Process

### 1. Build a Tool Container Image

The approach requires compiling several components:

- **RDMA perftest tools** providing bandwidth and latency measurement utilities (ib_write_bw, ib_read_bw, ib_send_bw, etc.)
- **Mellanox HCA driver utilities** including network diagnostic tools
- **MPI-enabled NCCL tests** for multi-node GPU communication validation

The Dockerfile performs three critical functions: installing Mellanox packages containing RDMA tools, compiling NCCL tests with MPI support using "/opt/hpcx/ompi/" as the MPI home directory, and configuring SSH for the MPI operator framework.

### 2. Deploy MPIOperator

The MPIOperator orchestrates distributed testing by creating launcher and worker pods that communicate via MPI, enabling coordinated performance measurements across cluster nodes.

### 3. Execute Performance Tests

**ROCE Write Bandwidth Test Results:**
- Server-side peak bandwidth: 11,531.98 Gb/sec
- Client-side average: 107.84 Gb/sec

**Multi-node NCCL AllReduce Test (8 GPUs across 2 nodes):**
The testing framework successfully validated GPU communication, demonstrating 11.96 GB/s aggregate bandwidth at maximum message sizes (134MB).

## Key Technical Details

The implementation uses the NVidia NeMo base container, integrates OpenMPI 4.1.5, and leverages Mellanox OFED packages (version 23.07). Testing infrastructure spans NVIDIA A40 GPUs across distributed worker nodes.

## References

- NVIDIA DeepOps Kubernetes ROCE documentation
- NCCL-tests GitHub repository
- Linux RDMA perftest project
