# vLLM Server for OpenWebUI

Standalone vLLM deployment providing OpenAI-compatible API.

## Quick Start

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Start vLLM
docker compose up -d

# Check logs
docker compose logs -f

# Test API
curl http://localhost:8000/v1/models
```

## OpenWebUI Integration

vLLM is already configured in OpenWebUI at:
- **API URL**: `http://localhost:8000/v1`

Models will appear automatically in OpenWebUI's model selector.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL` | `meta-llama/Llama-3.1-8B-Instruct` | HuggingFace model ID |
| `TP_SIZE` | `3` | Tensor parallel size (GPUs) |
| `HUGGING_FACE_HUB_TOKEN` | - | Required for gated models |
| `CUDA_VISIBLE_DEVICES` | `0,1,2` | GPU selection |
| `HF_HOME` | `~/.cache/huggingface` | Model cache directory |

## Multi-Node (Chimera + Cerberus)

For pipeline parallelism across nodes, use the separate Ray-based configs:
- `docker-compose.head.yaml` (Chimera)
- `docker-compose.worker.yaml` (Cerberus)

## Common Models

```bash
# Llama 3.1 8B (fits on single 3090)
MODEL=meta-llama/Llama-3.1-8B-Instruct TP_SIZE=1

# Llama 3.1 8B across 3 GPUs
MODEL=meta-llama/Llama-3.1-8B-Instruct TP_SIZE=3

# Qwen 2.5 72B (requires all GPUs)
MODEL=Qwen/Qwen2.5-72B-Instruct TP_SIZE=3
```

## Troubleshooting

```bash
# Check GPU availability
nvidia-smi

# Check container status
docker compose ps

# View logs
docker compose logs vllm

# Restart
docker compose restart
```
