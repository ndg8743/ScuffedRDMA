# vLLM Now Supports gpt-oss

**Source URL:** https://vllm.ai/blog/gpt-oss
**Date accessed:** 2026-03-11

**Published:** August 5, 2025
**Author:** The vLLM Team
**Tags:** #model-support #performance

## Overview

vLLM announced support for gpt-oss across NVIDIA Blackwell and Hopper GPUs, as well as AMD MI300x and MI355x GPUs. The announcement details three major technical contributions enabling efficient inference of this sparse mixture-of-experts model.

## Key Technical Features

### MXFP4 MoE Implementation

gpt-oss employs a sparse MoE architecture with either 128 experts (120B variant) or 32 experts (20B variant), routing each token to 4 experts. The model uses "MXFP4, a novel group-quantized floating-point format" for MoE weights while maintaining bfloat16 precision for attention layers. This approach reduces model sizes to 63GB and 14GB respectively.

vLLM integrated two specialized GPU kernels:
- **Blackwell GPUs:** FlashInfer kernel leveraging native MXFP4 tensor cores
- **Hopper GPUs:** Triton matmul_ogs kernel with swizzling optimization

### Efficient Attention Mechanism

The model uses Group Query Attention with 64 query heads and 8 KV heads, interleaving full attention with sliding-window attention (window size 128). vLLM enhanced its Triton kernel for AMD compatibility and integrated the hybrid KV cache allocator, "dynamically shar[ing] the KV cache space between the full attention layers and sliding window" layers.

### Built-in Tool Support

gpt-oss includes native tool capabilities for web browsing and Python code execution. vLLM implements agent loops via the OpenAI Responses API and supports external MCP-compliant tool servers for modular architecture.

## Future Roadmap

- Hardening the Responses API
- Enhanced attention and MoE distributed parallelism
- Reduced CPU overhead for throughput optimization
