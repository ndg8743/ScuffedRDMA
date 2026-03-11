# Multi-Core By Default

**Source URL:** https://www.rfleury.com/p/multi-core-by-default
**Date accessed:** 2026-03-11

---

**Author:** Ryan Fleury
**Publication:** Digital Grove
**Date:** October 10, 2025

## Core Thesis

Fleury argues that modern CPU programming should treat multi-core execution as the default architecture rather than a special case. Instead of writing single-threaded code that occasionally "goes wide" through job systems or parallel loops, programmers should structure code where multiple threads execute simultaneously by default, "going narrow" only when necessary.

## Key Problems Identified

**Traditional Approaches:**
- Parallel `for` loops and job systems introduce significant engineering overhead
- Control flow becomes scattered across threads and time, complicating debugging
- Each instance of parallelization requires separate setup, synchronization, and result-combining logic
- "The costs of these problems... are paid every time we use this mechanism"

## Proposed Solution

The article advocates for a "multi-core by default" architecture where:

1. **Execution begins with all cores active** running identical code parameterized by thread index
2. **Barriers synchronize** threads at dependency points
3. **Narrow operations** execute on single threads via conditional checks (`if(thread_idx == 0)`)
4. **Work distribution** uses uniform range calculations across lanes

## Implementation Helpers

Fleury introduces three key abstractions:

- **`LaneIdx()`, `LaneCount()`, `LaneSync()`** - Thread-local access to group membership and synchronization
- **`LaneRange(count)`** - Uniformly distributes iteration ranges across participating threads
- **`LaneSyncU64()`** - Broadcasts small data between threads in same group

## Advantages Over Job Systems

"Code which is multi-core by default feels like normal single-threaded code, just with a few extra constructs." Benefits include:

- **Simplified debugging** - Maintains full call stacks across cores
- **Flexible execution** - Same code runs on 1 core or N cores via parameter adjustment
- **Cleaner resource management** - Stack remains primary storage, avoiding distributed lifetime complexity
- **Reduced boilerplate** - Eliminates machinery needed to hand off work between systems

## Work Distribution Strategies

1. **Uniform inputs** - Pre-calculate divisions when work divides evenly
2. **Dynamic assignment** - Use atomic counters when tasks have variable costs
3. **Algorithm redesign** - Replace serially-dependent approaches (comparison sort) with parallelizable alternatives (radix sort) when necessary

## Notable Insight

"By hunting for tradeoffs, many programmers train themselves to ignore cases when they can both have, and eat, their cake." Fleury argues that high-level utility and low-level performance aren't inherently opposed.
