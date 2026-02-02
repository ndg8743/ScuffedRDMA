#!/bin/bash
# Complete benchmark suite for gpt-oss-120b
# Tests: Ollama (TCP), vLLM (TCP), vLLM (RDMA)
#
# Run on Chimera: ./run_all_benchmarks.sh

set -e

RESULTS_DIR="/tmp/benchmark_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "=============================================="
echo "GPT-OSS 120B Complete Benchmark Suite"
echo "Results: $RESULTS_DIR"
echo "=============================================="
echo ""

# Check GPU status
echo "=== GPU Status ==="
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv
echo ""

# Check RDMA status
echo "=== RDMA Status ==="
rdma link show 2>/dev/null || echo "RDMA not configured"
echo ""

# ============================================
# Test 1: Ollama (TCP baseline)
# ============================================
echo "=== Test 1: Ollama gpt-oss:120b (TCP) ==="
echo ""

for i in 1 2 3 4 5; do
    echo -n "Iteration $i: "
    RESULT=$(curl -s --max-time 120 http://localhost:11434/api/generate -d '{
        "model": "gpt-oss:120b",
        "prompt": "Explain RDMA networking in 100 words.",
        "stream": false,
        "options": {"num_predict": 100}
    }')

    TOKENS=$(echo "$RESULT" | jq -r '.eval_count')
    DURATION=$(echo "$RESULT" | jq -r '.eval_duration')
    TPS=$(echo "scale=2; $TOKENS / ($DURATION / 1000000000)" | bc)
    echo "$TOKENS tokens, $TPS tok/s"
    echo "$RESULT" >> "$RESULTS_DIR/ollama_tcp.jsonl"
done

echo ""

# ============================================
# Test 2: vLLM (TCP mode - RDMA disabled)
# ============================================
echo "=== Test 2: vLLM gpt-oss-120b (TCP - RDMA disabled) ==="
echo ""

# Check if vLLM is running
if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    export NCCL_NET_GDR_LEVEL=0
    export NCCL_IB_DISABLE=1

    for i in 1 2 3 4 5; do
        echo -n "Iteration $i: "
        START=$(date +%s.%N)

        RESULT=$(curl -s --max-time 120 http://localhost:8000/v1/completions -H "Content-Type: application/json" -d '{
            "model": "openai/gpt-oss-120b",
            "prompt": "Explain RDMA networking in 100 words.",
            "max_tokens": 100
        }')

        END=$(date +%s.%N)
        DURATION=$(echo "$END - $START" | bc)
        TOKENS=$(echo "$RESULT" | jq -r '.usage.completion_tokens // 0')
        TPS=$(echo "scale=2; $TOKENS / $DURATION" | bc)
        echo "$TOKENS tokens in ${DURATION}s = $TPS tok/s"
        echo "$RESULT" >> "$RESULTS_DIR/vllm_tcp.jsonl"
    done
else
    echo "vLLM not running on port 8000. Start with:"
    echo "  docker run --gpus all -p 8000:8000 vllm/vllm-openai:gptoss --model openai/gpt-oss-120b"
fi

echo ""

# ============================================
# Test 3: vLLM (RDMA enabled via Soft-RoCE)
# ============================================
echo "=== Test 3: vLLM gpt-oss-120b (RDMA - Soft-RoCE) ==="
echo ""

if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
    # Enable RDMA
    export NCCL_IB_HCA=rxe0
    unset NCCL_NET_GDR_LEVEL
    unset NCCL_IB_DISABLE

    for i in 1 2 3 4 5; do
        echo -n "Iteration $i: "
        START=$(date +%s.%N)

        RESULT=$(curl -s --max-time 120 http://localhost:8000/v1/completions -H "Content-Type: application/json" -d '{
            "model": "openai/gpt-oss-120b",
            "prompt": "Explain RDMA networking in 100 words.",
            "max_tokens": 100
        }')

        END=$(date +%s.%N)
        DURATION=$(echo "$END - $START" | bc)
        TOKENS=$(echo "$RESULT" | jq -r '.usage.completion_tokens // 0')
        TPS=$(echo "scale=2; $TOKENS / $DURATION" | bc)
        echo "$TOKENS tokens in ${DURATION}s = $TPS tok/s"
        echo "$RESULT" >> "$RESULTS_DIR/vllm_rdma.jsonl"
    done
else
    echo "vLLM not running. Skipping RDMA test."
fi

echo ""
echo "=============================================="
echo "Benchmark Complete"
echo "Results saved to: $RESULTS_DIR"
echo "=============================================="

# Summary
echo ""
echo "=== Summary ==="
if [ -f "$RESULTS_DIR/ollama_tcp.jsonl" ]; then
    OLLAMA_AVG=$(cat "$RESULTS_DIR/ollama_tcp.jsonl" | jq -s '[.[].eval_count] | add / length')
    echo "Ollama (TCP): ~$OLLAMA_AVG tokens avg"
fi
