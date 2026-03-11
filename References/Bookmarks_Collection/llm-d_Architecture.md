# llm-d Architecture Overview

**Source URL:** https://llm-d.ai/docs/architecture
**Date Accessed:** 2026-03-11

## Title
**llm-d Architecture** - Achieving State-of-the-Art Inference Performance on Any Accelerator

## Key Content Summary

### Primary Purpose
llm-d is described as "a high-performance distributed inference serving stack optimized for production deployments on Kubernetes." The project aims to help organizations deploy large language models efficiently across various hardware accelerators.

### Core Capabilities Offered

The platform provides five primary features for production inference:

1. **Intelligent Scheduling** - Smart load balancing via Envoy with "prefix-cache aware routing, utilization-based load balancing, fairness and prioritization for multi-tenant serving"

2. **Disaggregated Serving** - Separation of prefill and decode operations to reduce time-to-first-token metrics

3. **Expert-Parallelism** - Support for deploying mixture-of-experts models like DeepSeek-R1 with enhanced throughput

4. **Tiered KV Caching** - "Improve prefix cache hit rate by offloading KV-cache entries to CPU memory, local SSD, and remote high-performance filesystem storage"

5. **Multi-Workload Autoscaling** - Dynamic scaling across shared hardware pools while maintaining service objectives

### Latest Release Information
Version 0.5 (February 2026) introduces hierarchical KV offloading, cache-aware LoRA routing, and achieves approximately 3.1k tokens/second per B200 decode GPU in wide-EP configurations.

### Technology Stack
The architecture integrates vLLM, Kubernetes Inference Gateway, and Kubernetes as foundational components, with llm-d providing optimization layers above these systems.
