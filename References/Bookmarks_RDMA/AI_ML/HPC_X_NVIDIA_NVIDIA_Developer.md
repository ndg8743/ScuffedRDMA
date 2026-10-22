# HPC-X | NVIDIA | NVIDIA Developer

- **Source:** https://developer.nvidia.com/networking/hpc-x
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# NVIDIA HPC-X

## Increase scalability and performance of messaging communications.

NVIDIA<sup>®</sup> HPC-X<sup>®</sup> is a comprehensive software package that includes Message Passing Interface (MPI), Symmetrical Hierarchical Memory (SHMEM) and Partitioned Global Address Space (PGAS) communications libraries, and various acceleration packages. This full-featured, tested, and packaged toolkit enables MPI and SHMEM/PGAS programming languages to achieve high performance, scalability, and efficiency and ensures that communication libraries are fully optimized by NVIDIA Quantum InfiniBand networking solutions.

### Performance at Any Scale

HPC-X takes advantage of NVIDIA Quantum InfiniBand hardware-based networking acceleration engines to maximize application performance. It dramatically reduces MPI operation time, freeing up valuable CPU resources, and decreases the amount of data traversing the network, allowing unprecedented scale to reach evolving performance demands.

## Software and Acceleration Packages

### HPC-X MPI

MPI is a standardized, language-independent specification for writing message-passing programs. NVIDIA HPC-X MPI is a high-performance, optimized implementation of Open MPI that takes advantage of NVIDIA’s additional acceleration capabilities, while providing seamless integration with industry-leading commercial and open-source application software packages.


### HPC-X OpenSHMEM

The HPC-X OpenSHMEM programming library is a one-side communications library that supports a unique set of parallel programming features, including point-to-point and collective routines, synchronizations, atomic operations, and a shared memory paradigm used between the processes of a parallel programming application.


### In-Network Computing

NVIDIA Scalable Hierarchical Aggregation and Reduction Protocol (SHARP™) improves the performance of MPI operations by offloading them from the CPU to the switch network and eliminating the need to send data multiple times, decreasing the amount of data traversing the network and dramatically reducing MPI operation time.


### NCCL/SHARP and UCX Support

NCCL-RDMA plug-ins enable remote direct-memory access (RDMA) and switch-based collectives (SHARP) with the NVIDIA Collective Communication Library (NCCL). The NCCL UCX plug-in replaces the default NCCL verbs-based inter-node communication routines with UCX-based communication routines for enhanced performance.


### Key Features

- Offloads collectives communications from MPI onto NVIDIA Quantum InfiniBand networking hardware
- Multiple transport support, including Reliable Connection (RC), Dynamic Connected (DC), and Unreliable Datagram (UD)
- Intra-node shared memory communication
- Receive-side tag matching
- Native support for MPI-3
- Multi-rail support with message striping
- NVIDIA GPUDirect<sup>®</sup> with CUDA<sup>®</sup> support
- NCCL-RDMA-SHARP plug-in support

### Benefits

- Increases CPU availability, application scalability, and system efficiency for improved application performance
- Ensures node-level and system-level health and performance
- Maximizes application performance with underlying hardware architecture
- Fully optimized for NVIDIA Quantum InfiniBand networking solutions
- Supports any interconnect based on InfiniBand or Ethernet standards

## Resources

**Note:**If you are using HPC-X as part of the Spectrum-X reference architecture, please refer to the

[NVIDIA Spectrum-X Validated Solution Stack](https://docs.nvidia.com/networking/software/spectrumx-solution-stack/index.html)page for the list of approved product releases and versions.