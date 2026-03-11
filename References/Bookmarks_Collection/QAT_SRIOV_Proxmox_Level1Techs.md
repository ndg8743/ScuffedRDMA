# QAT on Linux, SR-IOV, and Proxmox 8

**Source URL:** https://forum.level1techs.com/t/qat-howto-on-linux-and-sriov-and-proxmox-8/205786
**Date Accessed:** 2026-03-11

**Author:** Wendell (Level1Techs Forum)
**Date:** January 14, 2024

## Overview

This forum post provides a technical guide for enabling Intel QuickAssist Technology (QAT) on Proxmox 8 systems. QAT is a hardware accelerator built into certain Intel processors that handles data compression and encryption operations.

## Key Technical Points

**What is QAT:**
QAT accelerates "data transformation operations; mainly compression and encryption" and appears as a PCIe device. The technology has existed for over a decade and is now common on many Xeon processors.

**Important Limitation:**
The guide emphasizes that "Doing this as a boot-from-zfs is not recommended since QAT likely won't be detected properly at boot time" and reloading ZFS afterward becomes problematic.

**Hardware Requirements:**
Modern QAT support requires three components: firmware files (typically in linux-firmware package), kernel drivers, and userspace libraries (qatlib).

**SR-IOV Capability:**
Starting with Sapphire Rapids processors, QAT supports SR-IOV virtualization. This requires enabling IOMMU and SR-IOV in BIOS, plus kernel boot parameter `intel_iommu=on`.

## Verification Commands

Users can verify QAT detection with commands like `lspci -d :4940 -k` and check module loading via `lsmod | grep qat`.

## Notable Discussion Points

Forum participants reported mixed results attempting QAT implementation across TrueNAS, pfSense, and ESXi environments, with performance improvements varying significantly by use case and configuration.
