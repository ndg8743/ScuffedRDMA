# RDMA: Shared, Hostdevice, Legacy SRIOV

**Source URL:** https://schmaustech.blogspot.com/2025/01/rdma-shared-hostdevice-legacy-sriov.html
**Date Accessed:** 2026-03-11

**Author:** Benjamin Schmaus
**Date:** January 15, 2025
**Blog:** SCHMAUSTECH

## Overview

This article addresses how to select among three RDMA configuration methods for OpenShift deployments, expanding on a previous blog discussing implementation details.

## What is RDMA?

Remote Direct Memory Access (RDMA) enables computers to access each other's memory without CPU or OS involvement. NVIDIA's GPUDirect RDMA extends this technology, providing direct data paths between GPU memory across multiple hosts via NVIDIA networking devices. This reduces latency and offloads CPU resources.

## Three Configuration Methods

### RDMA Shared Device

Allows multiple pods on a worker node to share a single RDMA device through user-defined networks using VXLAN or VETH. Configuration occurs in the NicClusterPolicy by specifying physical device names and setting `rdmaHcaMax` parameters.

**Use Case:** "Better suited for developer or application environments where performance and latency are not key but the ability to have RDMA functionality across nodes is important."

**Trade-off:** Pods sharing the device compete for bandwidth and latency resources.

### RDMA SR-IOV Legacy Device

Single Root IO Virtualization segments network devices at the hardware layer, creating Virtual Functions (VFs) from a Physical Function (PF). Each VF behaves as an independent network device.

**Configuration:** Managed through SriovNetworkNodePolicy with vendor IDs, physical function names, and VF counts.

**Advantages:** Each VF provides direct access, making this suitable for latency and bandwidth-sensitive workloads.

**Limitation:** Only shareable among pods equal to the number of supported VFs.

### RDMA Host Device

Moves a network device from the host's network namespace to a pod's namespace, providing direct physical ethernet access. However, once assigned to a pod, the device becomes unavailable to other hosts until that pod is removed.

**Configuration:** Handled through NicClusterPolicy using the SRIOV network device plugin.

**Use Case:** Employed when other options are infeasible—unsupported SR-IOV, insufficient PCI BAR resources, or when specific device capabilities require the physical function driver.

## Conclusion

Selection depends on specific requirements: developer flexibility, performance needs, or hardware constraints determine which configuration method suits each deployment scenario.
