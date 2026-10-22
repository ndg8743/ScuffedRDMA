# libfabric - CSCS Documentation

- **Source:** https://docs.cscs.ch/software/communication/libfabric/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA)
- **Retrieved:** 2026-10-22


---

# Libfabric[¶](#libfabric)

[Libfabric](https://ofiwg.github.io/libfabric/), or Open Fabrics Interfaces (OFI), is a low-level networking library that provides an abstract interface for networks.
Libfabric has backends for different network types, and is the interface chosen by HPE for the [Slingshot network on Alps](../../../alps/hardware/#alps-high-speed-network), and by AWS for their [EFA network interface](https://aws.amazon.com/hpc/efa/).

To fully take advantage of the network on Alps:

- libfabric and its dependencies must be available in your environment (uenv or container);
- and, communication libraries in your environment like Cray MPICH, OpenMPI, NCCL, and NVSHMEM have to be built or configured to use libfabric.

What about UCX?

[Unified Communication X (UCX)](https://openucx.org/) is a low level library that targets the same layer as libfabric.
Specifically, it provides an open, standards-based, networking API.
By targeting UCX and libfabric, MPI and NCCL do not need to implement low-level support for each network hardware.

**There is no UCX back end for the Slingshot network on Alps**, and pre-built software (for example conda packages and containers) often provides versions of MPI built for UCX only.
Running these images and packages on Alps will lead to very poor network performance or errors.

## Using libfabric[¶](#using-libfabric)

### uenv[¶](#uenv)

If you are using a uenv provided by CSCS, such as [prgenv-gnu](../../prgenv/prgenv-gnu/#prgenv-gnu), [Cray MPICH](../cray-mpich/#cray-mpich) is linked to libfabric and the high speed network will be used.
No changes are required in applications.

### Containers[¶](#containers)

The approach is to install libfabric inside the container, along with MPI and NCCL implementations linked against it.
At runtime, the [container engine](../../container-engine/#container-engine) [CXI hook](../../container-engine/resource-hook/#hpe-slingshot-interconnect) will replace the libfabric libraries inside the container with the corresponding libraries on the host system.
This will ensure access to the Slingshot interconnect.

Use NVIDIA containers for the gh200 nodes

Container images provided by NVIDIA, which come with CUDA, NCCL and other commonly used libraries are recommended as the base layer for building a container environment on the [gh200](../../../alps/hardware/#nvidia-gh200-gpu-nodes) and [a100](../../../alps/hardware/#nvidia-a100-gpu-nodes) nodes.

The version of CUDA, NCCL and compilers in the container can be used once libfabric has been installed. Other communication libraries, like MPI and NVSHMEM, provided in the containers can’t be used directly. Instead, they have to be installed in the container and linked against libfabric.

Installing libfabric in a container for NVIDIA nodes

The following lines demonstrate how to configure and install libfabric in a Containerfile. Communication frameworks are built with explicit support for CUDA and GDRCopy.

Some additional features are enabled to increase the portability of the container to non-Alps systems:

- The libfabric [EFA](https://aws.amazon.com/hpc/efa/) provider is configured with the `--enable-efa` flag, for compatibility with AWS infrastructure.
- The UCX communication framework is added to facilitate building a broader set of software (e.g. some OpenSHMEM implementations) and for optimized infiniband network support.

Note that it is assumed that CUDA has already been installed on the system.

An example Containerfile that installs libfabric in an NVIDIA container can be expanded below:

## The full Containerfile for GH200

The Containerfile below is based on an NVIDIA CUDA image, which provides a complete CUDA installation and NCCL.

## Tuning libfabric[¶](#tuning-libfabric)

Tuning libfabric (particularly together with [Cray MPICH](../cray-mpich/#cray-mpich), [OpenMPI](../openmpi/#openmpi), and [NCCL](../nccl/#nccl)) depends on many factors, including the application, workload, and system.
For a comprehensive overview libfabric options for the CXI provider (the provider for the Slingshot network), see the [`fi_cxi` man pages](https://ofiwg.github.io/libfabric/v2.1.0/man/fi_cxi.7.html).
Note that the exact version deployed on Alps may differ, and not all options may be applicable on Alps.

See the [Cray MPICH known issues page](../cray-mpich/#known-issues) for issues when using Cray MPICH together with libfabric.