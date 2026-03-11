# vLLM Benchmarking: GPUDirect RDMA Performance Analysis

**Source URL:** https://discuss.vllm.ai/t/vllm-benchmarking-why-is-gpudirect-rdma-not-outperforming-standard-rdma-in-a-pipeline-parallel-setup/1377
**Date Accessed:** 2026-03-11

**Title:** "vLLM Benchmarking: Why Is GPUDirect RDMA Not Outperforming Standard RDMA in a Pipeline-Parallel Setup?"

**Author:** Zerohertz (posted August 14, 2025 on vLLM Forums)

**Category:** Hardware Support - NVIDIA GPU Support

## Technical Content Summary

### Problem Statement
The user benchmarked multi-node serving with vLLM across two nodes (each with one 40GB A100 GPU) to assess RDMA impact. Despite enabling GPUDirect RDMA via NCCL environment variables, performance improvements were minimal compared to standard RDMA configurations.

### Initial Configuration Challenge
The user encountered an NCCL message indicating GPU Direct RDMA was disabled due to physical distance constraints and resolved this by setting `NCCL_NET_GDR_LEVEL=10`.

### Key Insights from Response
According to RunLLM's analysis, "RDMA benefits are most pronounced in large tensor-parallel deployments where inter-node communication becomes the main bottleneck." The response identifies that pipeline-parallel setups with limited GPUs per node show modest RDMA gains.

### Limiting Factors Identified
- Single GPU per node with TP=1 minimizes network traffic
- Pipeline parallelism creates some communication but insufficient network saturation
- Model size and batch sizes may not trigger network bottlenecks as primary constraints

### Optimization Recommendation
For measurable RDMA benefits, implement larger tensor parallelism configurations, increase batch sizes, or deploy models requiring heavier inter-node communication patterns.
