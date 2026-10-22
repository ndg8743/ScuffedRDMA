# Mastering CUDA and High-Performance Computing, Part III

- **Source:** https://softwarefrontier.substack.com/p/mastering-cuda-and-high-performance-204?r=3c7w5a&utm_campaign=post&utm_medium=web&triedRedirect=true
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > NVIDIA & CUDA)
- **Retrieved:** 2026-10-22


---

## The system contract beneath the kernel

In **Part I**, we descended from C++ into **LLVM IR**, tracing each loop, phi node, and virtual register.

In **Part II**, we dissolved PTX into warps, registers, and latency-hiding strategies, exploring how threads collide and cooperate in the Streaming Multiprocessor pipelines.

While I was studying all of this, a few months ago, I genuinely thought I understood the **atomic unit** of performance. I was totally wrong.

The atomic unit is not the kernel. A kernel is not computation. It is a **submission**: a meticulously packaged descriptor, assembled by the driver, serialized over the PCIe or NVLink bus, and handed to a firmware-managed command processor.

This processor does not execute “*kernels*” the way you imagine. It schedules thread blocks onto independently clocked **Streaming Multiprocessors**, arbitrates shared registers and memory banks, manages multiple **DMA engines**, and interleaves thousands of warps to hide latency.

Every instruction, every **FMA**, every predicated branch in your kernel is meaningless until the submission reaches the scheduler. Until you reason at this level, you are tuning the wrong layer.

Optimizing PTX, unrolling loops, or **balancing registers** matters only after the submission has carved a feasible execution plan through firmware, SM resources, and memory subsystems.

This is where performance truly lives:

at the intersection of host, bus, firmware, and microarchitecture, where the **invisible choreography** of scheduling, arbitration, and allocation transforms a static descriptor into teraflops of actual computation.

## The atomic unit of GPU execution

When you write a kernel with the triple-chevron syntax, you are not “*launching computation*”. You are calling into the **CUDA Runtime API**, specifically `cudaLaunchKernel`.

Consider what that call site looks like after the compiler lowers it:

```
// Source-level kernel invocation
myKernel<<<gridDim, blockDim, sharedMemBytes, stream>>>(arg0, arg1, arg2);
// What the compiler actually emits (simplified)
void* args[] = { &arg0, &arg1, &arg2 };
cudaLaunchKernel(
    (const void*)&myKernel,  // fat binary function handle
    gridDim,                 // dim3
    blockDim,                // dim3
    args,                    // pointer to argument array
    sharedMemBytes,          // dynamic shared memory in bytes
    stream                   // cudaStream_t
);
```
That call is deceptively simple. Beneath it lies a cascade of complex, orchestrated operations that transform your high-level kernel into a **GPU-executable submission.**

The runtime layer, `libcudart`, performs several critical tasks before the GPU ever sees a single instruction. First, it resolves the **function pointer** for your kernel. This pointer does not point to machine code directly.

It points into a **fat binary** (`fatbin`) section embedded in the host ELF executable under the `.nv_fatbin` section, a container that may hold multiple artifacts. You can inspect this directly:

```
# Dump all ELF sections to verify the fat binary is embedded
readelf -S ./my_binary | grep nv_fatbin
# Or use cuobjdump to list all embedded architectures
cuobjdump --list-elf ./my_binary
# Output example:
# ELF file    1: my_kernel.sm_80.cubin
# ELF file    2: my_kernel.sm_86.cubin
# Disassemble the SASS for a specific architecture
cuobjdump --dump-sass --gpu-architecture sm_80 ./my_binary
```
The fat binary container holds one or more **cubin** objects, each containing **SASS** (Shader ASSembly, the actual machine-level ISA) for a specific compute capability, and possibly **PTX** (Parallel Thread Execution, a stable virtual ISA) for forward compatibility.

**SASS** is versioned by SM architecture: `sm_80` targets Ampere A100, `sm_86` targets Ampere RTX 30-series, `sm_90` targets Hopper H100.

If a cubin matches the active device’s compute capability, the driver loads it directly into device memory.

Otherwise, the embedded **JIT compiler** in the driver compiles PTX into SASS tailored to the exact SM microarchitecture, applying instruction scheduling, register allocation, and latency-hiding optimizations on-the-fly, then caches the result.

The cache lives at:

```
# Default JIT cache location on Linux
~/.cache/nvidia/ComputeCache/
# Inspect the cache
ls -lh ~/.cache/nvidia/ComputeCache/
# Force JIT recompilation by clearing the cache
rm -rf ~/.cache/nvidia/ComputeCache/
# Disable the cache entirely (forces JIT on every launch)
export CUDA_CACHE_DISABLE=1
# Inspect PTX embedded in the binary (requires PTX to have been included)
cuobjdump --dump-ptx ./my_binary
```
Next, the runtime constructs the **parameter buffer**. All kernel arguments are serialized into a contiguous memory region, respecting ABI alignment and padding rules.

The **CUDA ABI** mandates that arguments are packed in declaration order, each aligned to its own size, up to a maximum natural alignment of 8 bytes. This buffer is critical: it decouples the host representation of arguments from the GPU’s execution context.

The parameter buffer, along with metadata about grid dimensions, block dimensions, shared memory allocation, and the kernel entry point, forms the **launch descriptor**.

Control now transitions from `libcudart` into the **CUDA Driver API**, `libcuda`. At this point, you leave the comfort of user-space abstractions. The driver constructs a command packet fully describing the submission.

You can see the **Driver API** equivalents directly, bypassing the Runtime API entirely:

```
// Equivalent kernel launch using the Driver API directly
CUfunction kernel;
CUmodule module;
// Load a cubin directly, skipping the fat binary resolution step
cuModuleLoad(&module, "my_kernel.sm_80.cubin");
cuModuleGetFunction(&kernel, module, "myKernel");
// Pack arguments manually
void* kernelArgs[] = { &arg0, &arg1, &arg2 };
// Launch via Driver API
cuLaunchKernel(
    kernel,
    gridDim.x,  gridDim.y,  gridDim.z,   // grid dimensions
    blockDim.x, blockDim.y, blockDim.z,   // block dimensions
    sharedMemBytes,                        // dynamic shared memory
    stream,                                // CUstream
    kernelArgs,                            // argument array
    NULL                                   // extra options (NULL = unused)
);
```
The driver then executes a **system call** into kernel mode, a user-to-kernel **privilege transition**. This step is measurable. You can observe it with `strace` on Linux:

```
# Trace system calls during a CUDA kernel launch
strace -e trace=ioctl ./my_cuda_binary 2>&1 | grep -A2 "ioctl.*NVOS"
# You will see a sequence of ioctl() calls into /dev/nvidia0
# Each call corresponds to a driver operation: context management,
# command buffer allocation, or doorbell signaling
# Profile the full launch overhead including driver roundtrip
nvprof --print-gpu-trace ./my_cuda_binary
# Or with Nsight Systems (preferred for modern CUDA)
nsys profile --trace=cuda,nvtx ./my_cuda_binary
nsys stats report.nsys-rep
```
Inside the kernel-mode driver (`nvidia.ko` on Linux), the GPU submission is materialized. A GPU **command buffer** entry is created, encapsulating all launch metadata.

This entry is written into a memory region visible to the GPU, either pinned host memory accessible via PCIe DMA or device **BAR (Base Address Register) mapped space**, a CPU-accessible window into device memory through MMIO.

A **memory-mapped I/O (MMIO) write** to the GPU’s doorbell register signals that new work is ready.

This write traverses the interconnect, typically PCI Express or NVLink, crossing from CPU memory controllers to the GPU’s front-end hardware queue manager.

From this moment, the **CPU** relinquishes control. The GPU’s front-end processor fetches the command packet from the submission queue, decodes it, and begins orchestrating thread blocks across SMs.

**Launch latency**, typically 5 to 15 microseconds on a modern discrete GPU, is dominated not by grid size but by runtime and driver overhead, mode switch cost, command serialization, and **MMIO signaling**. You can verify this invariance empirically:

```
// Microbenchmark: measure launch latency vs. grid size
cudaEvent_t start, stop;
cudaEventCreate(&start);
cudaEventCreate(&stop);
// Launch a trivially empty kernel
__global__ void emptyKernel() {}
for (int blocks : {1, 256, 65535}) {
    cudaEventRecord(start);
    emptyKernel<<<blocks, 256>>>();
    cudaEventRecord(stop);
    cudaEventSynchronize(stop);
    float ms;
    cudaEventElapsedTime(&ms, start, stop);
    printf("blocks=%d  latency=%.3f ms\n", blocks, ms);
    // You will observe near-constant latency across all grid sizes
    // The dominant cost is the submission path, not the computation
}
```
This fact fundamentally shifts how you reason about **GPU performance**: kernels are not units of computation. They are descriptors.

Your optimization focus must move away from the code inside the kernel and toward the **orchestration** of submissions, streams, and resource contention at the firmware and microarchitectural level.

## Inside the GPU front-end

GPUs are not passive execution units. They are orchestrators of massive parallelism, with hardware designed to manage, schedule, and feed thousands of threads simultaneously.

At the apex of this architecture lies the **front-end command processor** (sometimes called the **FECS**, Front-End Command Streamer on Ampere and later architectures), a microarchitectural state machine tasked with transforming host-submitted work into actionable instructions for **Streaming Multiprocessors.**

When the CPU writes to the doorbell register via **MMIO**, the signal propagates across the PCIe interconnect into the GPU’s front-end.

The command processor wakes, fetches the command packet from its **pushbuffer** (the ring buffer used for command submission, a concept originating in GPU architecture from the early 2000s and still present in modern CUDA), and begins parsing the launch descriptor.

This descriptor is more than metadata. It encodes the grid dimensions, block dimensions, parameter buffer pointers, **kernel entry points**, shared memory allocation sizes, and stream association.

Crucially, the front-end does not immediately partition work across SMs. There is no pre-distribution.

Instead, the **GigaThread Engine** (NVIDIA’s term for the global thread block scheduler present since Fermi) maintains internal hardware work queues, constantly tracking SM occupancy, shared memory usage, register pressure, and warp slot availability.

Thread blocks are dynamically dispatched to **SMs** only when resources allow. This is why occupancy and resource usage matter at launch: *a block cannot begin execution until the SM has enough free registers, shared memory bytes, and warp slots.*

You can query the resource limits of any SM directly:

```
# Query device properties relevant to block scheduling
nvidia-smi --query-gpu=name,compute_cap --format=csv
# Or from CUDA code
cudaDeviceProp prop;
cudaGetDeviceProperties(&prop, 0);
printf("Max threads per SM:       %d\n", prop.maxThreadsPerMultiProcessor);
printf("Max blocks per SM:        %d\n", prop.maxBlocksPerMultiProcessor);
printf("Shared memory per SM:     %zu bytes\n", prop.sharedMemPerMultiprocessor);
printf("Registers per SM:         %d\n", prop.regsPerMultiprocessor);
printf("Warp size:                %d\n", prop.warpSize);
printf("Number of SMs:            %d\n", prop.multiProcessorCount);
// On an A100 (sm_80):
// Max threads per SM:       2048
// Max blocks per SM:        32
// Shared memory per SM:     167936 bytes (with carveout config)
// Registers per SM:         65536
// Warp size:                32
// Number of SMs:            108
```
This **dynamic dispatch** has profound architectural implications. Each block must be fully independent: it cannot rely on any global synchronization that spans other blocks.

If it did, the **GigaThread Engine** would risk deadlock whenever the number of dispatched-but-not-yet-scheduled blocks exceeded the number of concurrently resident blocks across all SMs. CUDA eliminates this hazard by design.

Blocks are the unit of forward progress, and cross-block synchronization is limited to device-wide barriers using **Cooperative Groups** with `grid.sync()`, which requires explicit opt-in via `cudaLaunchCooperativeKernel` and hardware support (Pascal and later):

```
#include <cooperative_groups.h>
namespace cg = cooperative_groups;
__global__ void cooperativeKernel(float* data) {
    cg::grid_group grid = cg::this_grid();
    // Phase 1: every block writes
    data[blockIdx.x * blockDim.x + threadIdx.x] = threadIdx.x;
    // Device-wide barrier: ALL blocks must reach this point
    // Only safe when the kernel is launched with cudaLaunchCooperativeKernel
    // and grid size <= number of SMs * max resident blocks per SM
    grid.sync();
    // Phase 2: every block reads from another block's data
    float val = data[(blockIdx.x + 1) % gridDim.x * blockDim.x + threadIdx.x];
}
// Launch must use cudaLaunchCooperativeKernel, not the chevron syntax
void* args[] = { &data };
cudaLaunchCooperativeKernel(
    (void*)cooperativeKernel,
    gridDim, blockDim,
    args, 0, stream
);
```
Within the front-end, multiple execution engines work in parallel.

One engine fetches blocks from the queue, another evaluates resource availability per SM, a third schedules warps to the SM **instruction dispatch units** (each SM on Ampere has four warp schedulers, each capable of issuing one instruction per clock to its assigned warp pool).

All of this happens in tens of nanoseconds, invisible to the CPU but essential to sustaining throughput.

## Where kernels meet silicon

I used to think a kernel was the atomic unit of performance. I was wrong.

A kernel is not computation. It is a descriptor, a carefully structured packet, handed from the CPU, through a driver, across a bus, and into a firmware-managed execution engine that schedules thread blocks onto independently clocked **Streaming Multiprocessors** sharing a memory subsystem with multiple DMA engines.

That sentence is not dramatic. It is mechanically accurate. And until you reason at that level, you are optimizing the wrong layer.

The interconnect is the immutable physical boundary that every kernel submission must cross. Most discrete GPUs connect over **PCI Express**, a packetized, credit-based, arbitrated serial fabric.

PCIe 4.0 x16 (the most common configuration as of Ada Lovelace) provides approximately 32 GB/s bidirectional bandwidth with roughly 1 to 3 microseconds of round-trip latency per transaction.

PCIe 5.0 x16 doubles the bandwidth to 64 GB/s while keeping similar latency characteristics. You can observe the actual topology and bandwidth on your system:

```
# Inspect PCIe topology and bandwidth
nvidia-smi topo --matrix
# Output shows P2P access type between GPUs and CPU:
# NV# = NVLink (higher bandwidth), PIX = PCIe same switch, etc.
# Benchmark PCIe bandwidth directly
# (from CUDA samples: bandwidthTest)
./bandwidthTest --mode=shmoo --memory=pinned
# Example output on PCIe 4.0 x16:
# Host to Device: ~25 GB/s
# Device to Host: ~26 GB/s
# (theoretical max 32 GB/s; overhead from protocol reduces effective bandwidth)
```
Systems with **NVLink** (A100 uses NVLink 3.0, H100 uses NVLink 4.0) fundamentally change this picture.

NVLink 3.0 provides 600 GB/s total bidirectional GPU-to-GPU bandwidth across 12 links on the A100, with sub-microsecond latency. NVLink 4.0 on H100 scales to 900 GB/s.

The principle remains the same: data movement occurs over a finite physical fabric. Move 20 GB per iteration over a 25 GB/s effective PCIe bandwidth, and the lower bound is 0.8 seconds regardless of what your kernels compute.

No amount of register blocking or shared memory tiling can bypass that limit. Physics dominates.

To address this, GPUs expose dedicated **asynchronous copy engines**, entirely separate from the SM compute pipelines.

On the A100, there are two copy engines capable of overlapping host-to-device (H2D) and device-to-host (D2H) transfers simultaneously with kernel execution.

On the H100, the copy engine count increases to three. When you call `cudaMemcpyAsync` with pinned memory in a non-default stream, the driver programs a **DMA descriptor** and the copy engine pulls data directly from **host memory** using bus-mastering DMA while SMs continue executing kernels on a separate stream:

```
// Correct pattern for overlapping compute and transfer
// Requires: pinned memory, separate streams, no implicit sync
float *h_input, *h_output, *d_input, *d_output;
const size_t N = 1 << 24;
const size_t bytes = N * sizeof(float);
// Allocate pinned (page-locked) host memory
cudaMallocHost(&h_input,  bytes);  // pinned
cudaMallocHost(&h_output, bytes);  // pinned
cudaMalloc(&d_input,  bytes);
cudaMalloc(&d_output, bytes);
cudaStream_t computeStream, transferStream;
cudaStreamCreate(&computeStream);
cudaStreamCreate(&transferStream);
// Issue H2D copy on transferStream (handled by copy engine)
cudaMemcpyAsync(d_input, h_input, bytes, cudaMemcpyHostToDevice, transferStream);
// Issue kernel on computeStream (handled by SMs, independently)
processKernel<<<N/256, 256, 0, computeStream>>>(d_output, previousData);
// Insert event-based dependency: computeStream waits for transferStream
cudaEvent_t transferDone;
cudaEventCreate(&transferDone);
cudaEventRecord(transferDone, transferStream);
cudaStreamWaitEvent(computeStream, transferDone, 0);
// Now safe to launch the kernel that depends on d_input
dependentKernel<<<N/256, 256, 0, computeStream>>>(d_input, d_output);
// DO NOT call cudaDeviceSynchronize() here unless absolutely necessary.
// It drains ALL streams and ALL engines, collapsing the pipeline to serial.
```
The distinction between `cudaMalloc` for device memory and `cudaMallocHost` for pinned host memory is not stylistic. It is architectural.

The copy engine requires **physically contiguous, page-locked pages** to issue DMA transfers without CPU intervention.

Pageable memory allocated with standard `malloc` forces the driver to stage through a temporary pinned **bounce buffer first**, adding one full extra copy and destroying any possibility of true overlap.

## Pageable vs. page-locked memory and the orchestration of streams

I used to think memory transfers were trivial: just a `cudaMemcpy` and the GPU would magically have the data. That is not the case.

At the hardware level, not all host memory is created equal. **Pageable memory**, the default for every allocation from `malloc`, `new`, or `std::vector`, cannot be accessed directly by a GPU DMA engine.

The OS may migrate, swap, or remap pageable pages at any moment. The DMA engine requires a **physically stable**, contiguous range of pages with a fixed physical address to issue a transaction, because the DMA controller programs the physical address into the PCIe packet directly.

There is no page table walk on the GPU side during a DMA transfer.

When you pass a pointer to pageable memory to any `cudaMemcpy` variant, the driver silently performs a **three-step process**: it first allocates a temporary pinned staging buffer in driver-managed memory.

Second, it performs a CPU-side `memcpy` from your pageable buffer into the pinned staging buffer, then programs the **DMA engine** to transfer from the pinned staging buffer to device memory.

Two copies of the **entire dataset**, two chances for latency to accumulate, two pressure events on the CPU’s memory subsystem, multiplied by every transfer in your pipeline.

**Pinning host memory** eliminates this staging copy entirely. You can pin memory in several ways:

```
// Method 1: allocate pinned memory from the start (preferred)
float* h_data;
cudaMallocHost(&h_data, bytes);          // pinned, CUDA-managed
// or equivalently:
cudaHostAlloc(&h_data, bytes, cudaHostAllocDefault);
// Method 2: pin an existing pageable allocation (useful for legacy code)
float* existing_ptr = (float*)malloc(bytes);
cudaHostRegister(existing_ptr, bytes, cudaHostRegisterDefault);
// ... use existing_ptr in cudaMemcpyAsync ...
cudaHostUnregister(existing_ptr);        // must unpin before free
free(existing_ptr);
// Method 3: write-combined memory (good for H2D only, uncached on CPU side)
float* h_wc;
cudaHostAlloc(&h_wc, bytes, cudaHostAllocWriteCombined);
// Write-combined memory bypasses the CPU cache hierarchy,
// reducing cache pollution on the host but making CPU reads very slow.
// Only use when the CPU writes sequentially and the GPU reads.
// Verify a pointer is pinned and get the device-mapped address
cudaPointerAttributes attr;
cudaPointerGetAttributes(&attr, h_data);
printf("Memory type: %d (2 = cudaMemoryTypeHost/pinned)\n", attr.type);
```
But pinning comes at a real **OS-level** cost. Each pinned page is **wired**: the OS cannot reclaim it for paging, cannot map it to another physical address, and cannot swap it to disk.

On **Linux**, wired pages count against the locked memory limit (`RLIMIT_MEMLOCK`). High-performance systems typically raise this limit:

```
# Check current locked memory limit
ulimit -l
# Default is often 64 KB (far too low for GPU workloads)
# Raise the limit for the current session
ulimit -l unlimited
# Or permanently via /etc/security/limits.conf
echo "* hard memlock unlimited" >> /etc/security/limits.conf
echo "* soft memlock unlimited" >> /etc/security/limits.conf
# Verify pinned memory usage on the system
cat /proc/meminfo | grep -i locked
# Mlocked: shows currently wired pages in KB
```
Even with pinned buffers, transferring data efficiently requires orchestrated submission. **Streams** are the mechanism.

A CUDA stream is an ordered sequence of operations: kernel launches, memory copies, or event markers. Within a stream, operations execute in issue order, serialized by the hardware.

Across streams, no ordering is guaranteed unless the programmer explicitly inserts synchronization via `cudaEvent` or `cudaStreamWaitEvent`.

Internally, each stream maps to a logical command queue in the driver, which maps to a **hardware channel** on the GPU front-end.

The GPU scheduler interprets these queues at the hardware front-end, deciding dynamically which operation to issue to which engine.

The **concurrency decisions** depend on SM capacity (how many blocks can reside simultaneously on each SM given register and shared memory consumption), warp slot availability (each SM on Ampere supports up to **64 resident warps** regardless of block count).

After that, it copy **engine availability** (two engines on A100, three on H100, each capable of one direction of transfer at a time), and memory bandwidth headroom (HBM2e on A100 provides 2 TB/s; GDDR6X on RTX 4090 provides 1 TB/s).

Streams are not independent parallel lanes. They represent **potential parallelism**, a promise the hardware can choose to fulfill when resources allow.

You can use **Nsight Systems** to visualize whether your multi-stream design is actually achieving overlap:

```
# Profile with stream-level visibility
nsys profile \
    --trace=cuda \
    --cuda-memory-usage=true \
    --output=timeline \
    ./my_application
# Open the report
nsys-ui timeline.nsys-rep
# The timeline view will show whether kernels and memcpy operations
# from different streams truly overlap, or serialize due to resource contention
```
## Resource-constrained block residency

I used to think that once a block is launched, it simply executes. That is not how the hardware sees it. The Streaming Multiprocessor treats blocks as units of **resource allocation**, not just threads to execute.

When a block is assigned to an SM, its **residency**, the number of blocks and warps that can coexist, is determined by the most constrained of four interlocking resources.

- First, register consumption: each SM has 65,536 registers on Ampere (the register file is physically 32-bit wide). If your kernel uses 64 registers per thread and launches 256-thread blocks, that block consumes 256 × 64 = 16,384 registers, allowing at most 65,536 / 16,384 = 4 blocks to reside simultaneously.
- Second, static and dynamic shared memory: an Ampere SM has up to 164 KB of configurable shared memory (in a combined L1/shared memory array of 192 KB).
- Third, the hardware-imposed maximum of 2,048 resident threads per SM.
- Fourth, the architectural maximum of 32 resident blocks per SM on Ampere.

The CUDA **Occupancy Calculator** (available as both a spreadsheet and as API calls) computes the binding constraint:

```
// Query theoretical occupancy from the runtime
int minGridSize, blockSize;
// Let the runtime choose an optimal block size to maximize occupancy
cudaOccupancyMaxPotentialBlockSize(
    &minGridSize,
    &blockSize,
    myKernel,
    0,        // dynamic shared memory per block
    0         // block size limit (0 = no limit)
);
printf("Suggested block size: %d, min grid size: %d\n", blockSize, minGridSize);
// Compute occupancy for a specific configuration
int numBlocks;
cudaOccupancyMaxActiveBlocksPerMultiprocessor(
    &numBlocks,
    myKernel,
    256,   // threads per block
    0      // dynamic shared memory per block
);
printf("Max active blocks per SM: %d\n", numBlocks);
// occupancy = numBlocks * threadsPerBlock / maxThreadsPerSM
// Inspect register and shared memory usage of a compiled kernel
// (from command line)
// nvcc --ptxas-options=-v mykernel.cu
// Output:
// ptxas info: Used 32 registers, 4096 bytes smem, 400 bytes cmem[0]
```
You can also inspect **register usage** directly in the compiled binary:

```
# Check register usage per thread in a compiled cubin
cuobjdump --dump-sass ./my_binary | grep -A5 "Function : myKernel"
# Look for the .regcount field or count the register usage in SASS
# Alternatively, pass verbose flags to ptxas at compile time
nvcc -Xptxas -v -arch=sm_80 mykernel.cu -o mykernel
# ptxas info: compiling entry function 'myKernel' for 'sm_80'
# ptxas info: Function properties for myKernel:
#     0 bytes stack frame, 0 bytes spill stores, 0 bytes spill loads
# ptxas info: Used 48 registers, 8192 bytes smem, 400 bytes cmem[0]
```
**Register spilling**, when the compiler cannot fit all live variables into the 65,536 register file and must evict some to **local memory** (a per-thread region in global DRAM), is one of the most expensive occupancy failures because local memory accesses are cached in **L1/L2** but still require **DRAM** bandwidth when they miss.

You can force a register cap and observe the effect:

```
// Annotate a kernel to cap its register usage
// Forces the compiler to spill anything above the cap into local memory
__global__ void __launch_bounds__(256, 4) myKernel(float* data) {
    // 256 = max threads per block (helps compiler optimize)
    // 4   = minimum blocks per SM (compiler will spill registers to meet this)
    ...
}
// Or via nvcc flag (applies globally to all kernels in the translation unit)
// nvcc --maxrregcount=32 mykernel.cu
```
Residency is not just about thread count. It directly determines the SM’s ability to hide memory latency via **warp-level latency hiding**. An Ampere SM has four warp schedulers. Each scheduler selects a ready warp every clock cycle.

If a warp issues a global memory load (with a latency of roughly 290 clock cycles to HBM on A100), the warp scheduler immediately switches to another ready warp. To fully hide that 290-cycle latency, you need enough resident warps to keep all four schedulers busy during the wait.

With too few resident warps due to register or **shared memory pressure,** stalls become visible in the instruction pipeline, and throughput collapses.

Low residency at the block level also reduces system-level concurrency. A single **resource-heavy kernel** can monopolize SMs, eliminating the scheduler’s ability to overlap operations from multiple streams.

Kernel design cascades upward through the entire submission pipeline.

## The anatomy of GPU execution

Looking back across this journey, from kernel launches to PTX, from SM occupancy to DMA engines, from streams to page migration, the lesson is clear: the GPU is a tightly orchestrated ecosystem, not a black box that executes kernels on demand.

A kernel is not pure computation. It is a descriptor, a submission packet traveling from `cudaLaunchKernel` through `libcudart`, across the Driver API privilege boundary, into `nvidia.ko`, across the **PCIe fabric** or NVLink interconnect, into the GigaThread Engine’s pushbuffer, through the front-end command processor, and only then into the SM warp schedulers.

Execution is layered: submission queues, DMA engines, front-end command processors, **SM schedulers**, warp instruction buffers, and physical register files all contribute to the effective performance of even a trivially simple operation.

Hardware constraints propagate upward across the entire stack. **Register pressure** on a single kernel reduces SM residency, which reduces warp count, which reduces latency-hiding capability, which reduces SM throughput, which reduces the scheduler’s ability to overlap streams, which reduces system-level concurrency.

Memory is not homogeneous: pageable versus pinned allocation, Unified Memory page fault overhead, DMA copy engine count, and **HBM bandwidth** all determine whether your kernels can achieve real parallel throughput.

Every microsecond is measurable. Mode switches, MMIO signaling, **JIT compilation**, and page migrations all introduce latency invisible in source code but entirely observable with `nsys`, `nvprof`, `cuobjdump`, and `/proc/driver/nvidia-uvm/stats`.

Optimizing a GPU is not a matter of loop unrolling, warp-level FMA scheduling, or shared memory bank conflict elimination in isolation.

It is engineering at **multiple layers** simultaneously, understanding how software abstractions translate to hardware realities at every level of the submission path.

Only by reasoning across the entire execution path, from host-side memory allocation strategy to SM warp scheduler residency, can one design systems that realize the full potential of GPU hardware.

The **atomic unit of GPU performance is submission**. Everything else, threads, blocks, warps, registers, is consequence, not cause.

Every optimization, every kernel redesign, every memory allocation decision must respect the architecture-wide **resource constraints**, the interconnect physics, and the hardware scheduler’s discretion.