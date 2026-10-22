# DOCA Software Framework | NVIDIA Developer

- **Source:** https://developer.nvidia.com/networking/doca
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# NVIDIA DOCA Software Platform


# Accelerate application development for NVIDIA BlueField and ConnectX networking devices.

NVIDIA DOCA™ unlocks the potential of the NVIDIA® BlueField® platform. By harnessing the power of BlueField DPUs and SuperNICs, DOCA enables the rapid creation of applications and services that offload, accelerate, and isolate data center workloads. It lets developers create software-defined, cloud-native, DPU- and SuperNIC-accelerated services with zero-trust protection, addressing the performance and security demands of modern data centers. DOCA-Host includes all needed host drivers and tools for your NVIDIA BlueField and NVIDIA® ConnectX® devices.

Together, DOCA and the BlueField platform enable the development of applications that deliver breakthrough networking, security, and storage performance. BlueField isolates the infrastructure service domain from the workload domain to offer significant improvements in application and server performance, security, and efficiency, giving developers all the tools they need to realize optimal, secure, accelerated data centers and AI clouds.

DOCA software consists of an SDK and a runtime environment. The DOCA runtime, included by default with the BlueField platform, has tools for provisioning, deploying, and orchestrating containerized services on hundreds or thousands of DPUs and SuperNICs across the data center. The DOCA SDK provides industry-standard open APIs and software frameworks. The SDK supports a range of operating systems and distributions and includes drivers, libraries, tools, documentation, and example applications. 

DOCA-Host is the DOCA package for host installation and includes several installation profiles to best fit your data center workflows. DOCA-Host provides the needed interfaces for NVIDIA networking platforms, including both BlueField and ConnectX devices.

[Read the DOCA User Manual](https://docs.nvidia.com/doca/sdk/)

## Powering the Agentic AI Factory

Explore enterprise-ready microservices and orchestration frameworks for NVIDIA BlueField and ConnectX to accelerate, secure, and scale production AI workloads.

## Platform and Host Deployments

### DOCA on the BlueField Platform

The NVIDIA BlueField platform, powered by the DOCA software framework, is an advanced computing platform for data center infrastructure, delivering accelerated software-defined networking, storage, security, and management services at massive scale.

[Learn About BlueField](https://www.nvidia.com/en-us/networking/products/data-processing-unit/)

### DOCA on the Host

NVIDIA BlueField and NVIDIA ConnectX are paired with DOCA to deliver Ethernet and InfiniBand connectivity solutions at speeds up to 800 gigabits per second (Gb/s). Built on an open foundation, the DOCA-host package includes essential drivers and tools to enhance networking performance and enable advanced functionality. DOCA software is available on every leading operating system as a standalone package (without a bundled OS) for Arm® and x86 architectures.

[Learn About DOCA-Host Installation and Profiles](https://docs.nvidia.com/doca/sdk/nvidia+doca+profiles/index.html)

## Unpack the Stack

# BlueField Software Bundle

- The BlueField software bundle includes the bootloader, OS kernel, necessary network interface card (NIC) firmware, NVIDIA drivers, sample filesystem, and toolchain—all certified as part of the NVIDIA NGC™ catalog.
- The BlueField bundle includes Ubuntu 22.04 as a commercial-grade Linux distribution with continuous OS and security updates.

# SDK Key Components


- DOCA RDMA (Remote direct-memory access) acceleration SDK: unified communications and collaboration (UCC) and Unified Communication X (UCX), RDMA verbs, GPUDirect®
- Network acceleration SDK: NVIDIA Accelerated Switching and Packet Processing (ASAP2)™ software-defined networking (SDN), emulated VirtIO, Firefly time synchronization
- Security acceleration SDK: inline cryptography, App Shield runtime security
- Storage acceleration SDK: storage emulation and virtualization, crypto and compression
- Data path acceleration (DPA) SDK: accelerate workloads requiring high-performance access to NIC engines
- Management SDK: deployment, provisioning, service orchestration
- Industry-standard APIs: DPDK, SPDK, Linux Netlink
- User space and kernel

### Forward and Backward Compatibility

DOCA provides multi-generational support to ensure that applications developed today will consistently run with added performance benefits on all future generations of BlueField.

### Offload, Accelerate, Isolate Infrastructure


Network, storage, and security services are offloaded, accelerated, and isolated on BlueField while data is securely delivered to workloads at wire speed.

### Open Ecosystem

DOCA offers a software application framework to accelerate ecosystem development.

## DOCA Developer Resources


# DOCA-Host and BlueField Bundle Runtime Downloads

Download DOCA-Host and the BlueField DPU and SuperNIC runtime image.