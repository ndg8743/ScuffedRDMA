# Multi-Node vLLM Cluster

Distributed vLLM across Chimera and Cerberus using Ray for pipeline parallelism.

## Cluster Overview

| Node | IP | GPUs | VRAM | Role |
|------|-----|------|------|------|
| Chimera | 192.168.1.150 | 3× RTX 3090 | 72GB | Head (Ray + vLLM) |
| Cerberus | 192.168.1.233 | 2× RTX 5090 | 64GB | Worker (Ray) |
| **Total** | | **5 GPUs** | **136GB** | |

## Parallelism Strategy

- **Tensor Parallel (TP=3)**: Split model layers across 3 GPUs on same node
- **Pipeline Parallel (PP=2)**: Split model stages across 2 nodes

This allows running models up to ~120B parameters.

## Quick Start

**1. Start Cerberus (worker) first:**
```bash
# On Cerberus (192.168.1.233)
cd /home/nathan/ScuffedRDMA/deployment/multi-node
docker compose -f docker-compose.worker.yaml up -d
```

**2. Start Chimera (head):**
```bash
# On Chimera (192.168.1.150)
cd /home/nathan/ScuffedRDMA/deployment/multi-node
docker compose -f docker-compose.head.yaml up -d
```

**3. Verify cluster:**
```bash
# Check Ray dashboard
curl http://192.168.1.150:8265

# Check vLLM
curl http://192.168.1.150:8000/v1/models
```

## Model Options

| Model | Size | TP | PP | Notes |
|-------|------|----|----|-------|
| DeepSeek-R1-70B | 70B | 3 | 2 | Recommended for cluster |
| Llama-3.3-70B | 70B | 3 | 2 | Requires HF token |
| Qwen2.5-72B | 72B | 3 | 2 | Good for code |
| Mixtral-8x22B | 141B | 3 | 2 | MoE, fits in 136GB |

## Environment Variables

```bash
# Required for gated models (Llama, etc.)
export HUGGING_FACE_HUB_TOKEN=hf_xxxxx

# Model selection
export MODEL=deepseek-ai/DeepSeek-R1-Distill-Llama-70B
```

## OpenWebUI Integration

vLLM API is available at `http://192.168.1.150:8000/v1`

In OpenWebUI Admin → Connections → OpenAI API:
- URL: `http://192.168.1.150:8000/v1` (or `http://localhost:8000/v1` from Chimera)

## Why Not gpt-oss on vLLM?

`gpt-oss` is in **GGUF format** (Ollama). vLLM only supports **HuggingFace format**.

| Format | Used By | Extension |
|--------|---------|-----------|
| GGUF | Ollama, llama.cpp | `.gguf` |
| SafeTensors | vLLM, HuggingFace | `.safetensors` |

To use gpt-oss, keep it on Ollama. For vLLM, use HuggingFace models.

## Monitoring

```bash
# Ray dashboard
http://192.168.1.150:8265

# GPU usage on each node
nvidia-smi -l 1

# vLLM logs
docker logs -f vllm-head
```

## Troubleshooting

**Worker not connecting:**
```bash
# Check network connectivity
ping 192.168.1.150

# Check Ray port
nc -zv 192.168.1.150 6379

# Check firewall
sudo ufw allow from 192.168.1.0/24
```

**Out of memory:**
- Reduce `--max-model-len`
- Reduce `--gpu-memory-utilization` to 0.85
- Use smaller model
