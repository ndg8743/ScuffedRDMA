# Planning for 100 Gbps Adapter

**Source URL:** https://www.ibm.com/docs/en/storage-scale-system/5141-AF8?topic=network-planning-100-gbps-adapter
**Date Accessed:** 2026-03-11

## Title
Planning for 100 Gbps adapter

## Content Summary

This IBM technical documentation covers deployment considerations for 100 Gbps network adapters.

### Key Concepts

**Remote Direct Memory Access (RDMA):** The guide explains that RDMA is "a networking standard that allows the adapters to transfer data directly to or from the endpoints in a connection without using CPU resources." This technology enables simultaneous data transfers alongside other system operations while reducing latency.

### Available Adapter Options

Two adapter types are offered:
- 2-port 100 Gbps Ethernet adapter
- 2-port 100 Gbps InfiniBand adapter

### System Configuration Details

The documentation notes that each canister includes "a four-port 10 Gbps interface" with Port 1 designated for management. Additionally, there is "an additional port, the SSR service port - 1Gbps, which is used by the SSR to check hardware and set the IP address."

During operational deployment, customers utilize high-speed network connections (100 Gbps Ethernet or InfiniBand) to support IBM Spectrum® Scale cluster file system connectivity.

### Document Type
Technical planning guide for enterprise network infrastructure deployment
