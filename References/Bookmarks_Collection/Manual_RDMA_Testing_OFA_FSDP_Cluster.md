# Manual RDMA Testing Using the OFA FSDP Cluster

**Source URL:** https://www.iol.unh.edu/blog/2024/09/17/manual-rdma-testing-using-ofa-fsdp-cluster
**Date Accessed:** 2026-03-11

**Author:** Jeremy Spewock
**Date:** Tuesday, September 17, 2024

## Overview

This article discusses how the OpenFabrics Alliance (OFA) Fabric Software Development Platform (FSDP) cluster addresses a significant barrier for RDMA developers: limited access to diverse hardware for testing.

## Key Problem

Developers working with Remote Direct Memory Access (RDMA) software face substantial obstacles. As the author notes, "A common roadblock RDMA developers face is the need for access to required hardware." With multiple RDMA fabric types—each requiring specific Network Interface Cards—developers struggle to test across diverse environments, creating what amounts to a financial barrier to entry.

## FSDP Cluster Solution

The cluster provides:

- **10 compute nodes** with root access for temporary testing environments
- **Multiple RDMA fabrics:** RoCE, iWARP, Infiniband, and Omni-Path
- **Build server** with persistent home directories for creating reusable binaries
- **Beaker management system** enabling both automated and manual testing via SSH

## Real-World Impact: Redis Example

The article illustrates this challenge through Redis, an in-memory database. A developer proposed adding RDMA support in 2021, submitted functional code in 2022, but the pull request remains unmerged nearly two years later. The primary blockers include lack of RDMA expertise among maintainers and insufficient diverse testing across hardware platforms.

The author demonstrates testing Redis's RDMA features on the FSDP cluster by rebuilding RPM packages with RDMA support and testing across different fabrics.

## Conclusion

The FSDP cluster democratizes RDMA development by eliminating hardware access barriers, enabling broader adoption and innovation.
