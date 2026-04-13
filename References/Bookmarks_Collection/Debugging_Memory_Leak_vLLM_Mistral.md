# Debugging a Memory Leak in vLLM

**Source URL:** https://mistral.ai/news/debugging-memory-leak-in-vllm

**Date Fetched:** 2026-04-12

## Overview

Mistral AI's engineering team investigated a memory leak in vLLM that emerged during production testing of disaggregated serving with their Mistral Medium 3.1 model. The leak caused "400 MB per minute" of memory growth that would lead to out-of-memory failures within hours.

## Investigation Process

**Initial Challenges:**
The team struggled to isolate the issue using standard Python profiling tools (Memray, Guppy 3) and GDB, which either showed nothing or crashed the process entirely.

**Key Breakthrough:**
Using Heaptrack revealed that while heap memory remained stable, resident set size (RSS) continued growing. This indicated the leak existed outside the traditional heap—in anonymous memory mappings allocated via `mmap` system calls.

**Advanced Debugging Tools:**
- **pmap**: Displayed growing anonymous memory regions with changing base addresses
- **BPFtrace**: Traced `mmap`, `munmap`, and `mremap` syscalls, revealing calls originated from glibc's `syscall` wrapper
- **GDB Automation**: Set conditional breakpoints on specific syscall addresses to capture full stack traces during leaking allocations

## Root Cause

The culprit was **UCX (Unified Communication X)**, a high-performance communication library used by NIXL for disaggregated serving. UCX dynamically patches the Global Offset Table (GOT) to intercept all `mmap` calls for managing its Registration Cache—memory pinning for InfiniBand transfers. However, this overly broad interception, combined with an issue where "UCX does not immediately free memory when `munmap` is called," caused memory regions to accumulate indefinitely.

## Solution

Setting the environment variable `UCX_MEM_MMAP_HOOK_MODE=none` successfully resolved the leak without performance impact, since vLLM only requires registering one contiguous memory region.

The team collaborated with vLLM, NIXL, and UCX maintainers to merge a permanent fix into the vLLM repository.
