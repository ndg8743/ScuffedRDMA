# Shaping NIXL-based PD Disaggregation in vLLM V1

**Source URL:** https://blog.lmcache.ai/2025-04-11-lmcache-vllmv1-nixl/
**Date Accessed:** 2026-03-11

**Author:** LMCache Team
**Date:** April 11, 2025
**Category:** Tutorial

## Overview

LMCache has introduced two significant infrastructure developments for large language model serving:

1. **First PD disaggregation support for vLLM V1** - A new KV cache layer integration enabling external systems to extract and inject KV cache entries from vLLM's paged memory
2. **NVIDIA NIXL support** - Integration with NVIDIA's communication abstraction for ultra-fast KV cache transfers across GPUs and nodes

## Key Technical Advances

### vLLM V1 KV Cache Integration

The integration addresses a notable gap in vLLM V1's architecture. While the earlier V0 version featured KV connector capabilities, these were absent from the V1 redesign. This new implementation restores critical functionality including KV reuse and memory-efficient context handling, with interfaces allowing direct access to vLLM's internal paged KV memory.

### Two Operational Modes

**Storage Mode:** Implements database-style KV cache persistence, enabling offloading from GPU to CPU memory or disk. This approach supports long-term cache reuse across user sessions and conversation histories.

**Transport Mode:** Enables real-time peer-to-peer KV transfers between remote nodes, eliminating redundant computation in disaggregated prefill scenarios. The NIXL integration leverages NVLink, RDMA-capable NICs, and GPU Direct Storage for optimal data movement across diverse hardware configurations.

## Integration Benefits

The architecture enables multi-user state sharing, fast context switching across sessions, and cross-node cache reuse without requiring local recomputation. Performance benchmarking details will be shared in forthcoming articles.

**Resources:** [GitHub repository](https://github.com/LMCache/LMCache) | [vLLM PR](https://github.com/vllm-project/vllm/pull/15960/)
