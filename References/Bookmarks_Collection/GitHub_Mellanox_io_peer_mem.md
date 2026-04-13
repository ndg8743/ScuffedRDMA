# io_peer_mem - RDMA Peer Memory Module

**Source URL:** https://github.com/Artemy-Mellanox/io_peer_mem  
**Date Fetched:** 2026-04-12

## Project Overview

The **io_peer_mem** kernel module enables Remote Direct Memory Access (RDMA) transfers with specialized memory types. It functions as a client for Yishai Hadas's IB Peer Memory patch set.

## Key Capabilities

This module supports RDMA operations with:
- Memory-mapped devices (PFN mappings)
- Memory-mapped files from DAX filesystems
- NVRAM-resident storage (with appropriate kernel patches)

## Supported Use Cases

The documentation provides several command examples:

**DAX filesystem testing:**
```
donard_rdma_server -m /mnt/dax_fs/test.dat
```

**Device mapping:**
```
ib_read_bw -n 20 -R -a --mmap=/dev/pfn_mmapable_char_dev
```

**PCI resource access:**
```
ib_read_bw -n 20 -R -a --mmap=/sys/bus/pci/devices/0000:03:00.0/resource4_wc
```

## Testing Tools

The module can be validated using:
- donard_rdma utility
- Modified IB perftest toolset

## Technical Details

- **Language composition**: 94.3% C, 5.7% Makefile
- **Repository status**: Fork of sbates130272/io_peer_mem
- **Commits**: 21 total
