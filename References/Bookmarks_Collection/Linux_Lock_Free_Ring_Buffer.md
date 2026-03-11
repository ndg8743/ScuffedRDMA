# Lock-Free Multi-Producer Multi-Consumer Queue on Ring Buffer

**Source URL:** https://www.linuxjournal.com/content/lock-free-multi-producer-multi-consumer-queue-ring-buffer
**Date Accessed:** 2026-03-11

**Author:** Alexander Krizhanovsky
**Publication:** Linux Journal
**Date:** June 12, 2013

## Overview

This article addresses high-performance queue implementations for multicore systems. The author argues that traditional mutex-based queues create bottlenecks in highly concurrent environments where "lock contention sometimes hurts overall system performance."

## Problem Statement

Work queues handling hundreds of thousands of operations per second across multiple CPU cores suffer from mutex overhead. A naive synchronized implementation using mutexes and condition variables showed performance testing taking nearly seven minutes on a 16-core system, with 99.98% of execution time spent in futex system calls.

## Technical Solution

The author presents a lock-free ring buffer implementation using:

- **Atomic operations** via GCC intrinsics (`__sync_fetch_and_add`)
- **Per-thread position tracking** through `ThrPos` structures maintaining each thread's head and tail positions
- **Global helpers** (`last_head_`, `last_tail_`) to prevent overwrites while avoiding expensive CAS operations

### Key Innovation

Rather than using Compare-And-Swap operations to update global bounds, the implementation scans per-thread positions only when necessary (during wait conditions), reducing atomic operation overhead.

## Performance Results

The lock-free implementation achieved **3.7x speedup** compared to the mutex-based approach, completing the same test in approximately 1 minute 53 seconds versus nearly 7 minutes.

## Source Code

Complete implementations are available at the author's GitHub repository for comparison and testing.
