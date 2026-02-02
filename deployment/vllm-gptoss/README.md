# vLLM with gpt-oss

Run OpenAI's gpt-oss models on vLLM with MXFP4 quantization.

## Models

| Model | Parameters | Size | GPUs Required |
|-------|------------|------|---------------|
| `openai/gpt-oss-20b` | 20.9B | 14GB | 1× RTX 3090 |
| `openai/gpt-oss-120b` | 116.8B | 63GB | 3× RTX 3090 |

## Quick Start

```bash
# Start gpt-oss-120b on all 3 GPUs
docker compose up -d

# Or specify model
MODEL=openai/gpt-oss-20b TP_SIZE=1 docker compose up -d

# Check status
curl http://localhost:8000/v1/models
```

## Features

- **Sparse MoE**: 128 experts (120B) or 32 experts (20B)
- **MXFP4 Quantization**: Efficient memory usage via FlashInfer
- **Integrated Tools**: Web browsing, code execution support
- **Group Query Attention**: Improved inference efficiency

## OpenWebUI Integration

gpt-oss models appear in OpenWebUI via the existing connection:
- **URL**: `http://localhost:8000/v1`

## Requirements

- **Image**: `vllm/vllm-openai:gptoss` (NOT the standard image!)
- **GPUs**: NVIDIA Ampere+ (RTX 3090, 4090, 5090, etc.)
- **VRAM**: 14GB for 20B, 63GB for 120B

## Comparison with Ollama

| Aspect | Ollama (gpt-oss) | vLLM (gpt-oss) |
|--------|------------------|----------------|
| Format | GGUF | HuggingFace |
| Quantization | Q4_K_M, MXFP4 | MXFP4 native |
| Throughput | Good | Better (batching) |
| Tensor Parallel | Limited | Full support |

## Environment Variables

```bash
# Enable FlashInfer MXFP4 MoE optimization
VLLM_USE_FLASHINFER_MXFP4_MOE=1

# Model selection
MODEL=openai/gpt-oss-120b

# Tensor parallelism
TP_SIZE=3
```

## References

- [vLLM gpt-oss Blog Post](https://blog.vllm.ai/2025/08/05/gpt-oss.html)
- [FlashInfer](https://github.com/flashinfer-ai/flashinfer) - MXFP4 kernel optimization
