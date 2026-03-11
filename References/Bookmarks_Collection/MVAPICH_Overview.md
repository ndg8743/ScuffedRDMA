# MVAPICH: A High Performance MPI Implementation - Overview

**Source URL:** https://mvapich.cse.ohio-state.edu/overview/
**Date Accessed:** 2026-03-11

## Overview

MVAPICH is an MPI implementation developed by the Network-Based Computing Laboratory at Ohio State University. The project provides "MPI over InfiniBand, Omni-Path, Ethernet/iWARP, RoCE, and Slingshot" with multiple specialized variants.

## Main Variants

### MVAPICH2
The core implementation, currently at version 2.3.7 based on MPICH-3.2.1 under BSD licensing. It delivers "MPI-3.1 compliance" and supports ten transport interfaces including OFA-IB-CH3, iWARP, RoCE, PSM/PSM2, shared memory, and TCP/IP options.

### MVAPICH2-X
Extends the core with unified support for "hybrid MPI+PGAS programming models" including UPC, UPC++, OpenSHMEM, and Coarray Fortran, enabling developers to write applications using these models with a single communication runtime.

### MVAPICH2-GDR
Incorporates GPUDirect RDMA technology for NVIDIA GPU clusters with Mellanox InfiniBand, providing accelerated GPU-to-GPU communication by bypassing host memory.

### MVAPICH2-J
Provides Java bindings for the MVAPICH2 library through JNI, supporting basic Java datatypes and NIO direct ByteBuffers with point-to-point and collective operations.

### MVAPICH2-MIC
Optimizes communication on Xeon Phi (MIC) clusters using hybrid shared memory and SCIF designs to overcome bandwidth limitations.

### MVAPICH2-Virt
Addresses virtualization through SR-IOV support and inter-VM shared memory for both virtual machines and container environments.

### MVAPICH2-EA
Focuses on energy-aware optimization, reducing power consumption while maintaining performance through intelligent algorithmic designs.

## Key Features

The implementations emphasize high-performance communication through RDMA capabilities, multi-core optimization, fault tolerance mechanisms, and scalable job startup procedures suitable for exascale computing environments.
