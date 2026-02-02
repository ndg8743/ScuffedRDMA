#!/bin/bash
# Start vLLM on Chimera (head node)
# This provides OpenAI-compatible API at http://localhost:8000/v1

set -e

# Configuration
MODEL="${MODEL:-meta-llama/Llama-3.1-8B-Instruct}"
TP_SIZE="${TP_SIZE:-3}"  # 3 GPUs on Chimera
PORT="${PORT:-8000}"

echo "Starting vLLM server..."
echo "  Model: $MODEL"
echo "  Tensor Parallel Size: $TP_SIZE"
echo "  API Port: $PORT"

# Option 1: Docker (recommended)
docker run -d \
    --name vllm-server \
    --gpus all \
    --network host \
    --ipc host \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -e HUGGING_FACE_HUB_TOKEN="${HUGGING_FACE_HUB_TOKEN:-}" \
    vllm/vllm-openai:latest \
    --model "$MODEL" \
    --tensor-parallel-size "$TP_SIZE" \
    --port "$PORT" \
    --host 0.0.0.0

echo ""
echo "vLLM started! Test with:"
echo "  curl http://localhost:$PORT/v1/models"
echo ""
echo "OpenWebUI should now see vLLM models at http://localhost:$PORT/v1"
