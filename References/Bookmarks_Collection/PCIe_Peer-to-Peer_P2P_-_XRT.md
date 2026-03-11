# PCIe Peer-to-Peer (P2P) - XRT Master Documentation

**Source URL:** https://xilinx.github.io/XRT/master/html/p2p.html
**Date accessed:** 2026-03-11

---

## Overview

This documentation page explains PCIe peer-to-peer communication capabilities within the XRT (Xilinx Runtime) software stack for Alveo PCIe platforms.

## Key Concepts

PCIe P2P enables direct data transfer between two PCIe devices without requiring host RAM as intermediate storage. The feature supports two primary use cases:

1. **Device-to-Device Transfer**: Direct data movement between DDR/HBM memory on two separate Alveo PCIe cards
2. **Device-to-External Transfer**: NVMe or other peer devices can read/write directly from Alveo card memory

## System Requirements

The documentation notes that "64-bit IO is enabled and the maximium host supported IO memory space is greater than total size of DDRs on Alveo PCIe platform." Additionally, users should "Enable large BAR support in BIOS," which may be labeled as "Above 4G decoding" or similar terminology depending on motherboard vendor.

## Critical Warnings

The documentation includes important caveats: motherboard BIOS implementations vary significantly, and "the host could stop responding after P2P is enabled." A power cycle—not a warm reboot—may be necessary for recovery.

## Management Tools

The `xrt-smi` utility manages P2P configuration, displaying status as enabled, disabled, or "no iomem" (requiring warm reboot). Configuration persists across warm reboots but requires root privileges.

## Performance Considerations

Optimal performance requires peer devices under the same PCIe switch. IOMMU enablement degrades performance significantly by routing transfers through the root complex.
