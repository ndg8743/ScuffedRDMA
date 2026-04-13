# PCI Express I/O Virtualization Howto
**Source URL:** https://docs.kernel.org/PCI/pci-iov-howto.html
**Date Fetched:** 2026-04-12

## Overview

This Linux Kernel documentation explains SR-IOV (Single Root I/O Virtualization), a PCI Express capability that enables one physical device appear as multiple virtual devices. The physical device is called a Physical Function (PF), while the virtual devices are Virtual Functions (VFs).

## Key Concepts

**SR-IOV Basics:**
The technology allows dynamic allocation of VFs through registers within the capability structure. Each VF receives its own PCI configuration space, memory space, and can be accessed via unique Bus, Device, and Function numbers. VF drivers operate on register sets, making them appear as genuine PCI devices.

## Enabling SR-IOV

Two primary methods exist for activation:

1. **Driver-based**: The PF driver controls enablement through API calls. Loading the driver automatically activates SR-IOV capabilities.

2. **Sysfs-based**: Writing to the `sriov_numvfs` file provides per-PF control. This recommended approach allows per-PF, VF enable/disable values.

## API Functions

Developers use these core functions:

- `pci_enable_sriov(struct pci_dev *dev, int nr_virtfn)` – enables VFs
- `pci_disable_sriov(struct pci_dev *dev)` – disables VFs

The documentation includes a complete code example demonstrating how PF drivers implement the `dev_sriov_configure()` callback within the `pci_driver` structure to manage VF lifecycle.

## Virtual Function Usage

VFs function as hot-plugged PCI devices requiring standard PCI device drivers, operating identically to physical devices.
