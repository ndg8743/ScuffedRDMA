# MPI at Warp Speed: EESSI Meets Slingshot-11 - European Environment for Scientific Software Installations (EESSI)

- **Source:** https://www.eessi.io/docs/blog/2025/11/14/EESSI-on-Cray-Slingshot/
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > HPC)
- **Retrieved:** 2026-10-22


---

# MPI at Warp Speed: EESSI Meets Slingshot-11[¶](#mpi-at-warp-speed-eessi-meets-slingshot-11)

High-performance computing environments are constantly evolving, and keeping pace with the latest interconnect technologies is crucial for maximising application performance. However, we cannot rebuild all the software in EESSI that depends on improvements to communication libraries. So how do we take advantage of new technological developments?

Specifically we look at taking benefit of the HPE/Cray Slingshot-11. Slingshot-11 promises to offer a significant advancement in HPC networking, offering improved bandwidth, lower latency, and better scalability for exascale computing workloads ... so this should be worth the effort!

In this blog post, we present the requirements for building OpenMPI 5.x with Slingshot-11 support on HPE/Cray systems and its integration with EESSI using the [host\_injections](../../../../../site_specific_config/host_injections/)
mechanism of EESSI to inject custom-built OpenMPI libraries. This approach enables overriding EESSI’s default MPI library with an ABI-compatible, Slingshot-optimized version which should give us optimal performance.

## The Challenge[¶](#the-challenge)

EESSI provides a comprehensive software stack, but specialized interconnect support like Slingshot-11 can sometimes require custom-built libraries that aren't yet available in the standard EESSI distribution. Our goal is to:

1. Build OpenMPI 5.x with native Slingshot-11 support
2. Create ABI-compatible replacements for EESSI's OpenMPI libraries
3. Place the libraries somewhere where EESSI automatically picks them up
4. Support both x86\_64 AMD CPU partitions and NVIDIA Grace CPU partitions with Hopper accelerators

The main task is to build the required dependencies on top of EESSI, since many of the libraries needed for libfabric with CXI support are not yet available in the current EESSI stack.

### System Architecture[¶](#system-architecture)

Our target system is [Olivia](https://documentation.sigma2.no/hpc_machines/olivia.html#olivia) which is based on HPE Cray EX platforms for compute and accelerator nodes, and HPE Cray ClusterStor for global storage, all
connected via HPE Slingshot high-speed interconnect.
It consists of two main distinct partitions:

- **Partition 1**: x86\_64 AMD CPUs without accelerators
- **Partition 2**: NVIDIA Grace CPUs with Hopper accelerators

For the Grace/Hopper partition we also need to enable CUDA support in libfabric.

## Building the Dependency Chain[¶](#building-the-dependency-chain)

### Building Strategy[¶](#building-strategy)

Rather than relying on Cray-provided system packages, we opted to build all dependencies from source [on top of EESSI](../../../../../using_eessi/building_on_eessi/). This approach provides several advantages:

- **Consistency**: All libraries built with the same compiler toolchain
- **Compatibility**: Ensures ABI compatibility with EESSI libraries
- **Control**: Full control over build configurations and optimizations

### Required Dependencies[¶](#required-dependencies)

To build OpenMPI 5.x with libfabric and CXI support, we needed the following missing dependencies:

1. **libuv** - Asynchronous I/O library
2. **libnl** - Netlink library for network configuration
3. **libconfig** - Library designed for processing structured configuration files
4. **libfuse** - Filesystem in Userspace library
5. **libpdap** - Performance Data Access Protocol library
6. **shs-libcxi** - Slingshot CXI library
7. **lm-sensors** - Monitoring tools and drivers
8. **libfabric 2.x** - OpenFabrics Interfaces library with CXI provider
9. **OpenMPI 5.x** - The final MPI implementation

## EESSI Integration via `host_injections`[¶](#eessi-integration-via-host_injections)

EESSI's `host_injections` mechanism allows us to override EESSI's MPI library with an ABI compatible host MPI while maintaining compatibility with the rest of the software stack. We just need to make sure that the libraries are in the right
location to be automatically picked up by the software shipped with EESSI. This location is EESSI-version specific, for `2023.06`, with the NVIDIA Grace architecture, that location is:

**OpenMPI/5.0.7 on ARM nodes built with:**

### Testing[¶](#testing)

We plan to provide more comprehensive test results in the future. In this blog post we want to report that the approach works in principle, and that the EESSI stack can pick up and use the custom OpenMPI build and extract
performance from the host interconnect **without the need to rebuild any software packages**.

The following tests were conducted on Olivia accel partition (Grace nodes with Hopper GPUs), using two-node, two-GPU configuration with one MPI task per node.

We evaluated two OSU Micro-Benchmark builds:

1- OSU-Micro-Benchmarks/7.5-gompi-2023b-CUDA-12.4.0 from EESSI

2- OSU-Micro-Benchmarks/7.5 compiled with PrgEnv-cray.

The following commands were used to run the benchmarks:

`mpirun -np 2 osu_bibw D D`

`mpirun -np 2 osu_latency D D`


## See details

**Test using OSU-Micro-Benchmarks/7.5-gompi-2023b-CUDA-12.4.0 from EESSI**:

**Test using OSU-Micro-Benchmarks/7.5 with PrgEnv-cray**:

## Conclusion[¶](#conclusion)

The approach demonstrates EESSI's flexibility in accommodating specialized hardware requirements while preserving the benefits of a standardized software stack! There is plenty of more testing to do, but the signs at this stage are very good!