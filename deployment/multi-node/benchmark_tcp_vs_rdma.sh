#!/bin/bash
# =============================================================================
# gpt-oss-120b Multi-Node Benchmark: TCP vs RDMA
# =============================================================================
#
# This script runs gpt-oss-120b across 5 GPUs (Chimera + Cerberus) and
# compares performance with and without RDMA.
#
# Prerequisites:
#   - Soft-RoCE configured on both nodes (rxe0)
#   - /models directory with HuggingFace cache
#   - Docker with GPU support
#
# Usage:
#   ./benchmark_tcp_vs_rdma.sh
#
# =============================================================================

set -e

CHIMERA_IP="192.168.1.150"
CERBERUS_IP="192.168.1.233"
RESULTS_DIR="./benchmark_results_$(date +%Y%m%d_%H%M%S)"
ITERATIONS=5
MAX_TOKENS=100
PROMPT="Explain how RDMA improves distributed AI inference performance in exactly 100 words."

mkdir -p "$RESULTS_DIR"

echo "============================================================"
echo "gpt-oss-120b Multi-Node Benchmark: TCP vs RDMA"
echo "============================================================"
echo "Chimera:   $CHIMERA_IP (3× RTX 3090, 72GB)"
echo "Cerberus:  $CERBERUS_IP (2× RTX 5090, 64GB)"
echo "Total:     5 GPUs, 136GB VRAM"
echo "Results:   $RESULTS_DIR"
echo "============================================================"
echo ""

# Function to run benchmark
run_benchmark() {
    local MODE=$1
    local OUTPUT_FILE="$RESULTS_DIR/${MODE}_results.json"

    echo "Running $MODE benchmark ($ITERATIONS iterations)..."
    echo ""

    local total_tokens=0
    local total_time=0

    for i in $(seq 1 $ITERATIONS); do
        echo -n "  Iteration $i: "

        START=$(date +%s.%N)

        RESULT=$(curl -s --max-time 120 http://$CHIMERA_IP:8000/v1/completions \
            -H "Content-Type: application/json" \
            -d "{
                \"model\": \"openai/gpt-oss-120b\",
                \"prompt\": \"$PROMPT\",
                \"max_tokens\": $MAX_TOKENS
            }")

        END=$(date +%s.%N)
        DURATION=$(echo "$END - $START" | bc)

        TOKENS=$(echo "$RESULT" | jq -r '.usage.completion_tokens // 0')
        TPS=$(echo "scale=2; $TOKENS / $DURATION" | bc 2>/dev/null || echo "0")

        echo "$TOKENS tokens in ${DURATION}s = $TPS tok/s"

        # Save result
        echo "{\"iteration\": $i, \"tokens\": $TOKENS, \"time\": $DURATION, \"tps\": $TPS}" >> "$OUTPUT_FILE"

        total_tokens=$((total_tokens + TOKENS))
        total_time=$(echo "$total_time + $DURATION" | bc)
    done

    AVG_TPS=$(echo "scale=2; $total_tokens / $total_time" | bc)
    echo ""
    echo "  $MODE Average: $AVG_TPS tokens/sec"
    echo ""

    echo "$AVG_TPS"
}

# =============================================================================
# TEST 1: TCP Baseline (RDMA Disabled)
# =============================================================================
echo "============================================================"
echo "TEST 1: TCP Baseline (RDMA Disabled)"
echo "============================================================"
echo ""
echo "Stopping existing containers..."
ssh infra@$CHIMERA_IP "cd /home/nathan/ScuffedRDMA/deployment/multi-node && docker compose -f docker-compose.head.yaml down" 2>/dev/null || true
ssh infra@$CERBERUS_IP "cd /home/nathan/ScuffedRDMA/deployment/multi-node && docker compose -f docker-compose.worker.yaml down" 2>/dev/null || true

echo "Starting worker (Cerberus) with TCP..."
ssh infra@$CERBERUS_IP "cd /home/nathan/ScuffedRDMA/deployment/multi-node && \
    NCCL_IB_DISABLE=1 NCCL_NET_GDR_LEVEL=0 \
    docker compose -f docker-compose.worker.yaml up -d"

sleep 5

echo "Starting head (Chimera) with TCP..."
ssh infra@$CHIMERA_IP "cd /home/nathan/ScuffedRDMA/deployment/multi-node && \
    NCCL_IB_DISABLE=1 NCCL_NET_GDR_LEVEL=0 \
    docker compose -f docker-compose.head.yaml up -d"

echo "Waiting for vLLM to load model (this may take 2-3 minutes)..."
sleep 120

# Wait for API to be ready
for i in {1..30}; do
    if curl -s http://$CHIMERA_IP:8000/v1/models > /dev/null 2>&1; then
        echo "vLLM API ready!"
        break
    fi
    echo "Waiting for API... ($i/30)"
    sleep 10
done

TCP_RESULT=$(run_benchmark "TCP")

# =============================================================================
# TEST 2: RDMA (Soft-RoCE Enabled)
# =============================================================================
echo "============================================================"
echo "TEST 2: RDMA (Soft-RoCE Enabled)"
echo "============================================================"
echo ""
echo "Stopping existing containers..."
ssh infra@$CHIMERA_IP "cd /home/nathan/ScuffedRDMA/deployment/multi-node && docker compose -f docker-compose.head.yaml down" 2>/dev/null || true
ssh infra@$CERBERUS_IP "cd /home/nathan/ScuffedRDMA/deployment/multi-node && docker compose -f docker-compose.worker.yaml down" 2>/dev/null || true

echo "Starting worker (Cerberus) with RDMA..."
ssh infra@$CERBERUS_IP "cd /home/nathan/ScuffedRDMA/deployment/multi-node && \
    NCCL_IB_HCA=rxe0 \
    docker compose -f docker-compose.worker.yaml up -d"

sleep 5

echo "Starting head (Chimera) with RDMA..."
ssh infra@$CHIMERA_IP "cd /home/nathan/ScuffedRDMA/deployment/multi-node && \
    NCCL_IB_HCA=rxe0 \
    docker compose -f docker-compose.head.yaml up -d"

echo "Waiting for vLLM to load model (this may take 2-3 minutes)..."
sleep 120

# Wait for API to be ready
for i in {1..30}; do
    if curl -s http://$CHIMERA_IP:8000/v1/models > /dev/null 2>&1; then
        echo "vLLM API ready!"
        break
    fi
    echo "Waiting for API... ($i/30)"
    sleep 10
done

RDMA_RESULT=$(run_benchmark "RDMA")

# =============================================================================
# RESULTS SUMMARY
# =============================================================================
echo "============================================================"
echo "RESULTS SUMMARY"
echo "============================================================"
echo ""
echo "Configuration:"
echo "  Model: gpt-oss-120b (116.8B params, MXFP4)"
echo "  GPUs: 5 (3× RTX 3090 + 2× RTX 5090)"
echo "  VRAM: 136GB total"
echo "  Pipeline Parallel: 2 (across nodes)"
echo "  Tensor Parallel: 3 (within Chimera)"
echo ""
echo "Results:"
echo "  TCP Baseline:  $TCP_RESULT tokens/sec"
echo "  RDMA (RoCE):   $RDMA_RESULT tokens/sec"
echo ""

# Calculate improvement
if [ -n "$TCP_RESULT" ] && [ -n "$RDMA_RESULT" ]; then
    IMPROVEMENT=$(echo "scale=2; (($RDMA_RESULT - $TCP_RESULT) / $TCP_RESULT) * 100" | bc)
    echo "  Improvement:   ${IMPROVEMENT}%"
fi
echo ""
echo "============================================================"
echo "Detailed results saved to: $RESULTS_DIR"
echo "============================================================"
