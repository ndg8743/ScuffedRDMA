# LMAX Disruptor: High-Performance Concurrency Architecture

**Source URL:** https://lmax-exchange.github.io/disruptor/disruptor.html
**Date Accessed:** 2026-03-11

**Title:** LMAX Disruptor: High performance alternative to bounded queues for exchanging data between concurrent threads

**Authors:** Martin Thompson, Dave Farley, Michael Barker, Patricia Gee, Andrew Stewart

**Version:** 4.0.0-SNAPSHOT (May 2011)

---

## Core Content Summary

### Purpose and Context

The LMAX Disruptor emerged from efforts to build "the world's highest performance financial exchange." Early designs relied on queue-based architectures, but performance testing revealed that queuing between pipeline stages dominated execution costs, introducing significant latency and jitter.

### Key Problems Addressed

**Concurrency Challenges:**
- Lock-based mutual exclusion creates expensive context switches
- CAS (Compare-And-Swap) operations require pipeline locking and memory barriers
- Queue implementations suffer from contention at head/tail positions and typically operate at extremes—either full or empty—rather than balanced states

**Hardware Considerations:**
- Cache line conflicts cause "false sharing" when independent variables occupy the same 64-byte cache line
- Memory barriers coordinate visibility of changes across processor caches
- Garbage collection pauses become problematic under heavy queue-based load

### The Disruptor Design Solution

Rather than embedding storage, producer coordination, and consumer notification within a single queue abstraction, the Disruptor separates these concerns:

1. **Pre-allocated Ring Buffer** – Fixed-size circular array storing data entries, eliminating garbage collection overhead
2. **Producer Barrier** – Manages sequence claiming and write visibility
3. **Consumer Barrier** – Coordinates notification when entries become available

**Sequencing Mechanism:** Each producer and consumer maintains sequence numbers. Producers claim slots, write data, then commit updates by advancing a cursor. Consumers read the cursor with memory barriers—no locks required for single-producer scenarios.

**Batching Advantage:** When consumers detect the cursor has advanced multiple positions, they can process entries without concurrency mechanisms, enabling throughput bursts while maintaining consistent latency.

### Performance Results

**Throughput Comparison (Table 2):**
- Unicast (1P–1C): Disruptor achieves ~26M ops/sec vs. ArrayBlockingQueue's ~5.3M
- Three-stage pipeline (1P–3C): ~16.8M vs. ~2.1M ops/sec
- Diamond topology (1P–3C): ~16.1M vs. ~2.1M ops/sec

**Modern Hardware Results (Table 3 - AMD EPYC):**
- Unicast: 160M ops/sec (Disruptor 4) vs. 20.8M (ArrayBlockingQueue)
- Pipeline: 101M vs. 5.2M ops/sec

**Latency Measurements (3-stage pipeline at 1µs injection intervals):**
- Mean: "52 nanoseconds" (Disruptor) versus "32,757 nanoseconds" (ArrayBlockingQueue)
- 99th percentile: 128ns vs. 2,097,152ns
- Latency remains nearly constant until memory subsystem saturation, contrasting with queues' exponential "J-curve" degradation

### Architectural Advantages

- **Minimal Write Contention:** Single-threaded ownership of mutable data eliminates costly arbitration
- **Cache Efficiency:** Contiguous pre-allocation supports predictable memory access patterns and prefetching
- **Complex Dependency Graphs:** Multiple consumers coordinate through barrier abstractions against one ring buffer, avoiding cascading queue overhead
- **Reduced Garbage Pressure:** Immortal entry objects eliminate young/old generation promotion cycles

### Programming Model

The API emphasizes event-driven patterns. Producers claim entries via `ProducerBarrier`, populate them, then commit. Consumers implement `BatchHandler` interfaces receiving callbacks as entries become available—similar to actor-model semantics.

---

## Significance

The Disruptor represents a fundamental rethinking of concurrent data exchange, prioritizing "mechanical sympathy"—designing with explicit awareness of modern CPU architecture. By achieving "3 orders of magnitude lower" latency and "approximately 8 times more throughput" compared to queue alternatives, it established new performance benchmarks for financial systems, real-time processing, and any scenario demanding high-frequency, low-jitter data exchange between threads.
