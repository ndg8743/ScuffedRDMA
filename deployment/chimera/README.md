# Chimera Node Configuration

OpenWebUI + Ollama + vLLM deployment for Chimera (192.168.1.150).

## Services

| Service | Port | Description |
|---------|------|-------------|
| OpenWebUI | 3000 | Chat interface (gpt.hydra.newpaltz.edu) |
| Ollama | 11434 | Local LLM inference |
| vLLM | 8000 | OpenAI-compatible API (optional) |
| Middleman | 7070 | Account management API |

## Quick Start

```bash
# Start Ollama + OpenWebUI (default)
docker compose up -d

# Start with vLLM enabled
docker compose --profile vllm up -d

# View logs
docker compose logs -f
```

## Ollama Models (Already Downloaded)

| Model | Size | Parameters |
|-------|------|------------|
| gpt-oss:120b | 65GB | 116.8B MXFP4 |
| deepseek-r1:70b | 42GB | 70.6B Q4_K_M |
| llama3.3:latest | 42GB | 70.6B Q4_K_M |
| qwen3-coder:480b | 290GB | 480.2B Q4_K_M |
| mixtral:latest | 26GB | 46.7B Q4_0 |

## OpenWebUI Connections

Already configured in Admin → Connections:
- **Ollama**: `http://ollama:11434`
- **vLLM/OpenAI**: `http://localhost:8000/v1`

## Updating OpenWebUI

**DO NOT USE WATCHTOWER** - it resets settings!

Manual update process:
```bash
# 1. Check current version
docker inspect open-webui | grep -i image

# 2. Pull new version (check releases first)
# https://github.com/open-webui/open-webui/releases
docker compose pull open-webui

# 3. Restart with new version
docker compose up -d open-webui

# 4. Verify
docker logs open-webui | head -20
```

## Version Pinning

Current pinned version: `v0.7.2` (Jan 2026)

To update, edit `docker-compose.yaml`:
```yaml
image: ghcr.io/open-webui/open-webui:v0.7.x
```

## Troubleshooting

```bash
# Check GPU availability
nvidia-smi

# Check Ollama models
curl http://localhost:11434/api/tags | jq '.models[].name'

# Check vLLM (if running)
curl http://localhost:8000/v1/models

# Restart everything
docker compose down && docker compose up -d
```

## Data Persistence

- **OpenWebUI data**: `comp_open-webui` volume (users, chats, settings)
- **Ollama models**: `/models` on host
- **vLLM cache**: `/models` (shared with Ollama)
