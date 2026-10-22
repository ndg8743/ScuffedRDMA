# Mastering CUDA and High-Performance Computing, Part IV

- **Source:** https://softwarefrontier.substack.com/p/mastering-cuda-and-high-performance-de3?utm_campaign=post-expanded-share&utm_medium=web&triedRedirect=true&_src_ref=linkedin.com
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > NVIDIA & CUDA)
- **Retrieved:** 2026-10-22


---

## The moment arithmetic stops mattering

Every **CUDA program** eventually reaches the same reckoning.

You’ve written the kernel. You’ve structured the grid. The launch configuration looks reasonable. The **arithmetic is correct**. You submit it, measure wall time, and feel like a competent engineer.

Then you open a profiler.

**Nsight Compute** loads the metrics. You look at the first column: SM utilization. You expect something respectable: 70%, 80%, maybe more. What you see instead is a number that doesn’t make sense.

12%. Sometimes a little lower.

The tensor cores are almost entirely idle. The floating-point pipelines are stalled. A chip whose transistor count would have represented the entire **global semiconductor output** of the mid-1990s is sitting mostly quiet, doing almost nothing, waiting.

Waiting for data.

This is the first real lesson of GPU programming, and it is one of the most counterintuitive in all of systems engineering: **modern GPUs are not, in practice, compute-limited. They are memory-limited.** The bottleneck isn’t the arithmetic: it’s the infrastructure that feeds the arithmetic.

And that infrastructure is governed **not by logic design**, not by clock frequency, but by the literal physics of moving electric signals through metal on a substrate the width of a few dozen silicon atoms.

The GPU was designed to compute at enormous scale. But before it can compute anything, it needs data. And moving that data, from **DRAM**, through cache hierarchies, across the chip, into registers, costs time. Often far more time than the computation itself.

Understanding why, and what to do about it, is the **entire subject** of this article.

## The physics of moving bits through silicon

Let’s start with something that almost never appears in **CUDA tutorials** but underpins everything else: the actual physical constraints on data movement inside a chip.

An electric signal traveling through a metal interconnect on silicon propagates at **roughly two-thirds** the speed of light in vacuum. That sounds fast. It is fast. But it’s not the bottleneck.

The bottleneck is capacitance.

Every wire connecting two points on a chip behaves as a **tiny capacitor**. Moving a signal through that wire requires charging or discharging that capacitance. That costs energy, and more importantly for our purposes, it takes time.

The longer and wider the wire, the greater the capacitance, the slower the signal edges, the more time the **receiving circuit** spends waiting for the voltage to settle.

At **1 GHz**, one clock cycle is 1 nanosecond. Light travels about 30 cm in that time, which is longer than most GPU dies. Signal propagation across the chip isn’t the problem.

The problem is the full pipeline required to actually deliver data: address generation, routing through the memory subsystem, cache tag lookup, **DRAM row activation**, column access, data return bus, write to register file. Each of these steps adds cycles. Latencies compound.

When you add them all up, reaching off-chip DRAM from an execution unit costs **between 400 and 800 clock cycles** on a modern GPU.

That number is worth sitting with.

At 1.5 GHz, **600 cycles is 400 nanoseconds**. In that same window, a modern NVIDIA SM could theoretically issue hundreds of independent arithmetic instructions.

Instead, if it’s waiting for DRAM, it issues zero. The arithmetic units sit idle. The watt-hours tick over. Nothing useful happens.

This gap (*the chasm between compute speed and memory latency*) is the central engineering problem of **GPU design**. Everything else in GPU architecture exists to paper over this gap.

The warp scheduler, the cache hierarchy, shared memory, asynchronous pipelines, tensor cores: all of it is infrastructure built around one uncomfortable physical fact: **moving data costs time, and that time is long**.

DRAM hasn’t gotten meaningfully faster in latency terms for decades. It has gotten wider, more parallel, higher bandwidth.

But the fundamental latency of a DRAM access (row activation, **column select**, sense amplifiers settling) is governed by the same physics it always was.

**HBM2e** has extraordinary bandwidth. Its latency is still measured in hundreds of nanoseconds.

You cannot optimize your way out of physics.

## Inside the Streaming Multiprocessor

Modern GPUs solve this problem through a specific architectural pattern: massive parallelism layered over a **deep memory hierarchy**, orchestrated by a scheduling engine designed to hide latency rather than eliminate it.

To understand how, we need to look at the machine’s basic unit of execution. The **SM** is, in fact, the atom of GPU execution. Every thread you launch lands in one, executes inside one, and exits from one.

Everything else (*grid geometry, block dimensions, global memory layout*) is scaffolding around the SM.

Understanding what’s **physically inside** is the prerequisite for reasoning about performance. Here is a schematic of an Ampere SM:

```
┌──────────────────────────────────────────────────────────────────┐
│                     Streaming Multiprocessor (SM)                │
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────┐  │
│   │ Warp Sched 0 │  │ Warp Sched 1 │  │ Warp Sched 2 │  │ W3 │  │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─┬──┘  │
│          │                 │                 │             │      │
│   ┌──────▼─────────────────▼─────────────────▼─────────────▼──┐  │
│   │                   Dispatch / Issue Logic                    │  │
│   └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│   ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐ │
│   │  FP32 Cores     │  │  INT32 Units    │  │  Tensor Cores    │ │
│   │  (128 per SM)   │  │  (128 per SM)   │  │  (4 per SM)      │ │
│   └─────────────────┘  └─────────────────┘  └──────────────────┘ │
│                                                                  │
│   ┌─────────────────┐  ┌─────────────────┐                       │
│   │  FP64 Cores     │  │  Special Func.  │                       │
│   │  (64 per SM)    │  │  Units (SFU)    │                       │
│   └─────────────────┘  └─────────────────┘                       │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │              Load / Store Units (32 LSU)                  │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │              Register File (~256 KB)                      │   │
│   │              (65,536 × 32-bit registers)                  │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │       L1 Cache / Shared Memory (192 KB unified)          │   │
│   └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```
The arithmetic units (*FP32 cores, INT32 units, tensor cores*) get all the attention in marketing materials. They are not where performance is determined.

Performance is determined by the four warp schedulers at the top.

### The warp scheduler’s decision tree

Every cycle, each of the four warp schedulers examines its pool of eligible warps and must select one to issue. A warp is eligible if it satisfies four conditions simultaneously:

1. *It has a valid next instruction*
2. *All source operands for that instruction are available (no outstanding data dependency)*
3. *The required execution unit is not occupied by another instruction*
4. *No synchronization barrier is blocking it*

If a warp fails any condition, it is **ineligible**. The scheduler ignores it and checks the next one. The scheduler doesn’t understand priority, criticality, or deadlines. It is a simple priority-free selector: find the first **eligible warp**, issue it, repeat.

If **no** warp is eligible (*all are waiting for memory, or all have unresolved register dependencies*) the SM stalls. Not one warp stalls. The entire SM stalls. All four schedulers sit idle.

The execution pipelines emit nothing. Every watt powering the chip produces zero useful work. This is the stall you see in the profiler as “*no eligible warp selected.*”

On Ampere, the **theoretical maximum** is 64 resident warps per SM, 4 schedulers each issuing 1 warp per cycle. In the best case, the SM issues 4 independent instructions simultaneously from 4 different warps. In the worst case, when **all 64 warps** are blocked on DRAM, it issues zero.

The entire architecture of **GPU programming** is a battle to keep this scheduler fed. Everything else (*tiles, pipelines, occupancy tuning, coalescing*) is in service of that one goal.

## The memory hierarchy

Each layer of the GPU memory hierarchy represents a different **engineering tradeoff** between latency, bandwidth, capacity, and programmer control.

Understanding each layer’s character (*not just its numbers*) determines whether you can make intelligent decisions about where data should live at any moment during execution.

### Registers: the fastest storage on the chip

Registers are physically distributed across the SM register file — on Ampere, a 256 KB SRAM array containing **65,536 32-bit registers** per SM.

Access latency is **1 clock cycle.** Bandwidth between the register file and execution units is effectively unlimited for the purposes of performance analysis.

Registers are not a cache. They do not hold data that might be needed. They hold data that is *actively being computed on*.

The compiler allocates registers **deterministically** at compile time. Every local variable, intermediate computation, and loop accumulator that doesn’t get spilled lives in the register file.

But registers introduce the most important constraint in **CUDA performance engineering**: their consumption directly limits occupancy.

The register file must be divided among all threads resident on the SM simultaneously. If each thread requires **64 registers**, the 65,536 available registers accommodate at most **1,024 threads**: 32 warps, half the Ampere maximum.

With 32 warps instead of 64, the scheduler has half as **many options** when a warp stalls. Latency hiding degrades.

This is why `--maxrregcount` exists in the CUDA compiler toolchain. Capping register usage forces spilling to **local memory** which is DRAM, cached through L1/L2, with all the attendant latency.

The tradeoff is: more concurrent warps (*better latency hiding*) at the cost of some extra memory traffic (*more memory pressure*). Whether it helps depends entirely on the kernel’s specific balance of compute and memory.

The profiler metric to monitor is `sm__warps_active.avg.pct_of_peak_sustained_active`: the fraction of cycles during which at least one warp was active on the SM.

Values below 50% on **memory-bound kernels** usually indicate occupancy is limiting performance. Values above 75% suggest you’re probably fine.

### Shared memory: the programmable cache

Shared memory is physically the same SRAM as **L1 cache**; on Ampere, a unified 192 KB block that software partitions between the two.

Typical configurations: 128 KB shared / 64 KB L1, or 64 KB shared / 128 KB L1, selectable per kernel.

The critical property that distinguishes shared memory from every other memory type on the GPU: **it is explicitly managed by software.** L1 is automatic. L2 is automatic. HBM is automatic.

Shared memory requires the programmer to decide what to load, when to load it, and when to **synchronize threads** after loading. The hardware does exactly what the programmer specifies and nothing more.

This explicitness is simultaneously the source of its power and its most common source of subtle bugs.

Latency is roughly **20 clock cycles**, an order of magnitude faster than L2, 20–40× faster than DRAM. Intra-SM bandwidth reaches several terabytes per second.

For workloads with structured access patterns and significant data reuse within a thread block, shared memory is the **most important performance** tool available.

#### Bank conflicts: the hidden serialization

Shared memory is internally divided into 32 banks, each 4 bytes wide. In a single clock cycle, the hardware can service 32 simultaneous **4-byte accesses** (*one per bank*) as long as no two accesses target the same bank.

This design provides very high bandwidth when accesses are distributed. The bank index for a 32-bit word at byte address `addr` is:

`bank = (addr / 4) % 32`
If two or more threads in the same warp access different addresses mapping to the same bank, those accesses serialize. This is a **bank conflict**. The hardware issues them sequentially, one per cycle, multiplying the effective latency by the conflict degree.

A **32-way bank conflict**, 32 threads hitting the same bank simultaneously, effectively transforms a 20-cycle operation into a **640-cycle one**. On shared memory.

The canonical example is column access in a row-major 2D shared memory array:

```
__shared__ float tile[32][32];
float val = tile[threadIdx.x][threadIdx.y];  // accessing column threadIdx.y
```
In a row-major layout, `tile[row][col]` is stored at byte offset `(row * 32 + col) * 4`. For a fixed column `c`, the elements `tile[0][c]`, `tile[1][c]`, `tile[2][c]`... are stored at offsets `c*4`, `(32+c)*4`, `(64+c)*4`...

The bank index for `tile[i][c]` is `(i*32 + c) % 32 = c`. Every row has the same bank for column `c`.

If 32 threads **simultaneously** access column `c`, all 32 accesses hit bank `c`. Complete serialization. 32× slowdown. The fix is padding by one element:

`__shared__ float tile[32][33];  // one extra float per row`
Now `tile[i][j]` is at byte offset `(i*33 + j) * 4`. Bank index is `(i*33 + j) % 32`. For column `j`, bank = `(i*33 + j) % 32`. Since 33 is coprime to 32, incrementing `i` by 1 increments the bank by `33 % 32 = 1`. The 32 threads access 32 different banks. No conflicts.

One unused float per row, 128 bytes of wasted SRAM, eliminates a **32× serialization penalty.** This is one of the cheapest performance wins in CUDA.

### L1 cache: automatic but controllable

The portion of the unified SRAM not allocated to shared memory functions as an automatic L1 data cache for global memory accesses. Access latency is **28–33 cycles** on Ampere.

Unlike shared memory, L1 is not explicitly managed. The hardware decides what to cache based on access patterns. For streaming workloads with **no temporal reuse**, L1 caching is **actively harmful**; it evicts potentially useful data to cache data that will never be accessed again.

**CUDA** provides tools to limit this damage. The `__ldg()` intrinsic routes loads through the read-only texture cache, bypassing L1 entirely and preserving it for data with genuine reuse.

Cache-bypass load modifiers (`.cs` for streaming, `.cg` for L2-only) are available in PTX and accessible via `__builtin_nontemporal_load` variants. Using them correctly on **streaming data** can meaningfully improve L1 hit rates for other kernel data.

L1 is most valuable for **irregular access patterns** with temporal reuse: hash table lookups, graph traversals, sparse matrix operations, embedding lookups.

For structured **compute kernels** with predictable access patterns, explicit shared memory almost always dominates.

### L2 cache: the shared reservoir

L2 is a resource shared across all SMs: on the A100, a 40 MB unified L2 with approximately 4 TB/s aggregate read bandwidth. **Access latency** is roughly 200 cycles.

The bandwidth matters more than the latency for **most workloads.** If data fits in L2 and is accessed repeatedly across different thread blocks, L2 reuse can dramatically reduce **DRAM traffic** without any explicit shared memory management.

This is the main performance lever for workloads with inter-block reuse: embedding tables, **small lookup matrices**, bias vectors applied to many thread blocks.

**CUDA 11.1** and Ampere introduced explicit L2 residency controls via `cudaStreamSetAttribute` with `cudaStreamAttrAccessPolicyWindow`.

This allows developers to mark a specific memory region as **high-priority** for L2 retention: the hardware will attempt to keep it resident across thread block launches.

For embedding lookups or frequently-accessed **read-only tables,** this can reduce DRAM bandwidth consumption by an order of magnitude.

### HBM: the distant reservoir

High Bandwidth Memory sits physically separate from the **SM die**, stacked on the **GPU package** via silicon interposer.

Access requires leaving the SM die entirely, traversing the memory controller, and accessing **DRAM cells** across the interposer.

Current numbers:

- V100 HBM2, 32 GB, 900 GB/s
- A100 HBM2e, 80 GB, 2.0 TB/s
- H100 SXM HBM3, 80 GB, 3.35 TB/s
- H100 NVL HBM3e, 188 GB, 3.9 TB/s

These bandwidth numbers are genuinely impressive. They are still not enough.

The A100’s peak **FP16 tensor core** throughput is 312 TFLOPS. A typical deep learning layer performs approximately 2 FLOPs per weight element loaded (one multiply, one accumulate).

To keep tensor cores saturated, you’d need to deliver 156 TB/s of weight data; it’s 78× more than HBM2e can provide.

This isn’t a design failure. It’s physics. The solution is arithmetic intensity: load each weight once, perform **many operations** on it before the data expires from registers or shared memory.

The entire science of GPU kernel optimization is the science of achieving sufficient arithmetic intensity to bridge this **78× gap**.

## Warps and coalescing

Everything we’ve discussed about the memory hierarchy becomes concrete in the behavior of individual memory instructions.

### The anatomy of a memory transaction

When a warp executes a load instruction:

`float x = data[idx];`
The hardware doesn’t see 32 independent loads. It sees 32 addresses simultaneously, one per thread, and must service them with as **few memory transactions** as possible.

The memory controller coalesces these **32 addresses** into the minimum set of cache line requests that covers all of them.

DRAM is accessed in 128-byte cache lines on current NVIDIA GPUs. L2 sector granularity is 32 bytes. The hardware merges **warp addresses** into the minimum number of 128-byte requests covering all requested bytes.

### Coalesced access: ideal

Thirty-two threads accessing consecutive floats:

```
Thread  0 → data[base + 0]
Thread  1 → data[base + 1]
...
Thread 31 → data[base + 31]
```
Total footprint: 128 bytes, exactly one cache line. One transaction. Every byte fetched is used. Memory efficiency: 100%.

This is exactly the access pattern the hardware was designed for.

### Strided access: degraded

Stride-2 access:

```
Thread  0 → data[base + 0]
Thread  1 → data[base + 2]
...
Thread 31 → data[base + 62]
```
Address range: 252 bytes, spanning two 128-byte cache lines. Two transactions. 256 bytes transferred, 128 bytes used. Memory efficiency: 50%.

Stride 4: four cache lines, 25% efficiency. With stride 32, each thread’s access can fall in a different cache line, up to 32 transactions, 3% efficiency. The kernel is now burning 32× the memory bandwidth for the same amount of useful data delivered.

### Random access

**Scatter/gather**, hash lookups, pointer chasing, patterns where 32 thread addresses bear no spatial relationship to each other.

The worst case: one transaction per thread. 32 transactions, each returning 128 bytes to deliver 4 bytes.

Bytes-transferred-to-bytes-used ratio: 32:1. The kernel consumes **97% of its memory bandwidth** fetching data it will immediately discard.

This doesn’t just hurt the kernel itself. It saturates the **L2** and memory controllers, degrading bandwidth for every other kernel running concurrently on the chip.

The profiler metric to inspect is the ratio of `l1tex__t_sectors_pipe_lsu_mem_global_op_ld.sum` to `l1tex__t_requests_pipe_lsu_mem_global_op_ld.sum`, sectors per request.

Perfectly coalesced: 1. Mild inefficiency: 2–4. Significant inefficiency: 4–16. “*Please reconsider your life choices*”: above 16.

## Occupancy: the arithmetic of latency hiding

The GPU hides memory latency by switching between warps when one stalls. This only works if there are enough warps to switch to. If every warp is stalled waiting for DRAM, the scheduler has nothing to do. The **SM stalls**. Occupancy is the metric that captures this.

**Occupancy** is the ratio of active warps on an SM to the architectural maximum. On Ampere: maximum 64 warps, 2,048 threads. At 50% occupancy: 32 warps. At 25%: 16 warps.

Occupancy is constrained by three physical resources, all of which must simultaneously fit on the SM:

**1. Registers.** If each thread uses `R` registers, maximum concurrent threads = `65,536 / R`. For full occupancy (2,048 threads), each thread can use at most 32 registers. Kernels routinely use 64–128. At 64 registers: 50% occupancy. At 128: 25%.

**2. Shared memory.** If a kernel uses `S` bytes of shared memory per block with `T` threads per block, maximum concurrent blocks = `floor(192 KB / S)`. Maximum warps = `floor(192 KB / S) × (T / 32)`. A kernel using 96 KB per block with 256 threads per block: 2 concurrent blocks × 8 warps = 16 warps. 25% occupancy.

**3. Block limits.** Ampere supports at most 32 concurrent blocks per SM. A kernel with 32-thread blocks (1 warp per block) hits this limit at 32 warps, 50% occupancy, regardless of register or shared memory pressure.

### The occupancy-performance relationship

High occupancy is not synonymous with high performance. A compute-bound kernel with very few memory instructions doesn’t need **64 warps** to keep the scheduler busy; 4 ready warps might be sufficient if they never stall on memory.

**Chasing occupancy** for its own sake can force the compiler to spill registers to DRAM, adding memory traffic that makes performance worse.

The right mental model: occupancy matters proportionally to **memory latency exposure**. The more frequently your kernel stalls on DRAM, the more warps you need to hide that latency. If your kernel rarely touches memory, occupancy barely matters.

`cudaOccupancyMaxActiveBlocksPerMultiprocessor` gives you the theoretical maximum for a given kernel. The gap between that theoretical maximum and **what you observe** in the profiler (`sm__warps_active`) tells you how much the hardware can actually hide.

A kernel at 25% theoretical occupancy but 24% active occupancy is fine. A kernel at 75% theoretical occupancy but 20% active occupancy has a structural stall problem.

## Putting hard numbers on constraints

The roofline model is the most **useful analytical tool** in GPU performance engineering, and it is underused.

It doesn’t tell you *how* to optimize. It tells you *what* optimization is even possible, which is more valuable.

The central quantity is **arithmetic intensity**: floating-point operations performed per byte transferred from main memory.

`Arithmetic Intensity (I) = FLOPs / bytes_transferred`
Performance is bounded by the minimum of two constraints:

`Attainable Performance = min(Peak_FLOPs, Peak_Bandwidth × I)`
For the A100 FP16:

- Peak tensor throughput: 312 TFLOPS
- Peak HBM bandwidth: 2 TB/s

The **ridge point**, minimum arithmetic intensity required to be compute-bound rather than memory-bound:

`I_ridge = 312 × 10¹² / 2 × 10¹² = 156 FLOPs/byte`
To be compute-bound on the A100, every byte you load from HBM must be used for at least 156 floating-point operations. Most **CUDA kernels** don’t come close.

Consider a naive vector addition:

```
FLOPs:        1 (one addition)
Bytes moved:  12 (two float32 reads + one write)
I =           1/12 ≈ 0.08 FLOPs/byte
```
This kernel sits roughly 1,875× below the ridge point. Not 10% below. Not 50% below. **Nearly 2,000× below**. No amount of launch configuration tuning, thread count adjustment, or arithmetic reorganization will move the needle.

The kernel is physically limited by how fast you can move **12 bytes per FLOP** through the memory hierarchy. That’s a fundamental property of the algorithm.

Dense matrix multiplication is different. A square matrix multiply of dimension N performs `2N³` FLOPs and reads `3N²` elements (A, B, and C matrices). Arithmetic intensity grows as `2N³ / (3N² × 4 bytes) ≈ N/6`.

For N=1,024: roughly 170 FLOPs/byte, above the A100 ridge point. **Large matrix multiply** on Ampere is compute-bound. This is why it saturates tensor cores; there’s enough arithmetic per byte to keep them fed.

The roofline tells you which side of the ridge your kernel sits on, and therefore which type of optimization is worth pursuing. **Memory-bound kernels** benefit from better coalescing, data reuse, and smaller datatypes.

Compute-bound kernels benefit from better instruction throughput, occupancy, and **reduced arithmetic latency**.

Applying compute-bound optimizations to a memory-bound kernel is how engineers spend weeks achieving nothing.

## The architecture’s logic, finally visible

After tracing the memory hierarchy from physics to **TMA**, a coherent picture emerges.

The GPU is not a calculator that operates on data. It is a machine for orchestrating the movement of data at **massive scale**.

It is just fast enough, and in just the right form, for computation to occur at the rate the arithmetic units can sustain. Everything in the architecture, the four warp schedulers, the unified 192 KB SRAM, `cp.async`, TMA, WGMMA, exists in service of that orchestration.

The fastest **GPU programs** are not the ones that perform the most arithmetic per line of code. They are the ones that most efficiently move data through the hierarchy:

```
HBM (2 TB/s, ~600 ns)
  ↓  [TMA or cp.async]
Shared Memory (several TB/s, ~20 ns)
  ↓  [warp-level loads]
Register File (~1 ns)
  ↓  [tensor core instructions]
Accumulators
  ↓  [store]
HBM
```
Each arrow is a potential bottleneck. Each transition must be managed so that the layer above never waits for the layer below.

There is a **mental model shift** that separates engineers who write fast GPU code from those who don’t. It isn’t knowledge of specific APIs or familiarity with PTX. It’s the habit of thinking about data location.

At every point during **kernel execution**:

*where is this data right now?* 

*Where does it need to be in three instructions?* 

*How many cycles will it cost to move it there?* 

*Is there computation I can usefully perform in the meantime?*


This is how the **FlashAttention team** found their key insight: the bottleneck in naive attention wasn’t the matrix multiplies, it was repeated HBM round-trips for the attention matrix.

The arithmetic didn’t change. The **data choreography** did. That’s the entire optimization.

Once the hardware model is **genuinely internalized**, the techniques follow naturally. The padding that eliminates bank conflicts isn’t a trick you memorize, it falls directly out of understanding how the banking hardware works.

The `cp.async` pipeline isn’t a template you copy; it’s the obvious solution once you understand that **synchronous loads** are serializing your kernel for no reason.

That’s the real skill. Not writing **fast arithmetic**. Writing fast data movement, and just enough arithmetic to justify it.