#!/bin/bash
# =============================================================================
# ScuffedRDMA Transport Benchmark Suite
# =============================================================================
#
# Benchmarks all available transports (TCP, RoCE, TTPoe) with vLLM
# and generates comparison reports.
#
# Usage:
#   ./benchmark_all.sh [OPTIONS]
#
# Options:
#   --model=NAME        Model to benchmark (default: meta-llama/Llama-4-Scout-17B-16E)
#   --iterations=N      Benchmark iterations per transport (default: 5)
#   --max-tokens=N      Max tokens per request (default: 100)
#   --output-dir=PATH   Results output directory
#   --transports=LIST   Comma-separated transports to test (default: tcp,roce)
#   --skip-start        Don't restart cluster (use existing)
#   --generate-latex    Generate LaTeX table
#   --help              Show help
#
# Output:
#   benchmarks/results/benchmark_TIMESTAMP/
#   ├── tcp_results.json
#   ├── roce_results.json
#   ├── ttpoe_results.json  (if available)
#   ├── summary.json
#   ├── comparison.csv
#   └── results.tex
#
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
MODEL="${MODEL:-meta-llama/Llama-4-Scout-17B-16E}"
ITERATIONS=5
MAX_TOKENS=100
TRANSPORTS="tcp,roce"
CHIMERA_IP="${CHIMERA_IP:-192.168.1.150}"
OUTPUT_DIR=""
SKIP_START=false
GENERATE_LATEX=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model=*)
            MODEL="${1#*=}"
            shift
            ;;
        --iterations=*)
            ITERATIONS="${1#*=}"
            shift
            ;;
        --max-tokens=*)
            MAX_TOKENS="${1#*=}"
            shift
            ;;
        --output-dir=*)
            OUTPUT_DIR="${1#*=}"
            shift
            ;;
        --transports=*)
            TRANSPORTS="${1#*=}"
            shift
            ;;
        --skip-start)
            SKIP_START=true
            shift
            ;;
        --generate-latex)
            GENERATE_LATEX=true
            shift
            ;;
        --help)
            head -35 "$0" | tail -32
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set output directory
if [[ -z "$OUTPUT_DIR" ]]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    OUTPUT_DIR="$PROJECT_DIR/benchmarks/results/benchmark_$TIMESTAMP"
fi

mkdir -p "$OUTPUT_DIR"

# Prompt for benchmark
PROMPT="Explain the benefits of RDMA networking for distributed AI inference, focusing on latency reduction and CPU overhead. Be specific about performance improvements."

echo "============================================================"
echo "ScuffedRDMA Transport Benchmark Suite"
echo "============================================================"
echo "Model: $MODEL"
echo "Iterations: $ITERATIONS"
echo "Max Tokens: $MAX_TOKENS"
echo "Transports: $TRANSPORTS"
echo "Output: $OUTPUT_DIR"
echo "============================================================"
echo ""

# =============================================================================
# Benchmark Functions
# =============================================================================

run_single_benchmark() {
    local transport="$1"
    local output_file="$OUTPUT_DIR/${transport}_results.json"

    echo "----------------------------------------"
    echo "Benchmarking: $transport"
    echo "----------------------------------------"

    local total_tokens=0
    local total_time=0
    local ttft_sum=0
    local results=()

    for i in $(seq 1 $ITERATIONS); do
        echo -n "  Iteration $i/$ITERATIONS: "

        START=$(date +%s.%N)

        RESULT=$(curl -s --max-time 300 "http://$CHIMERA_IP:8000/v1/completions" \
            -H "Content-Type: application/json" \
            -d "{
                \"model\": \"$MODEL\",
                \"prompt\": \"$PROMPT\",
                \"max_tokens\": $MAX_TOKENS
            }" 2>/dev/null || echo '{"error": "request failed"}')

        END=$(date +%s.%N)
        DURATION=$(echo "$END - $START" | bc)

        # Parse result
        TOKENS=$(echo "$RESULT" | jq -r '.usage.completion_tokens // 0')
        ERROR=$(echo "$RESULT" | jq -r '.error // empty')

        if [[ -n "$ERROR" || "$TOKENS" == "0" ]]; then
            echo "ERROR"
            continue
        fi

        TPS=$(echo "scale=2; $TOKENS / $DURATION" | bc 2>/dev/null || echo "0")
        echo "$TOKENS tokens in ${DURATION}s = $TPS tok/s"

        total_tokens=$((total_tokens + TOKENS))
        total_time=$(echo "$total_time + $DURATION" | bc)

        # Store result
        results+=("{\"iteration\": $i, \"tokens\": $TOKENS, \"time\": $DURATION, \"tps\": $TPS}")
    done

    # Calculate averages
    if [[ $total_tokens -gt 0 ]]; then
        AVG_TPS=$(echo "scale=2; $total_tokens / $total_time" | bc)
        AVG_TIME=$(echo "scale=3; $total_time / $ITERATIONS" | bc)
    else
        AVG_TPS=0
        AVG_TIME=0
    fi

    echo ""
    echo "  Average: $AVG_TPS tokens/sec"
    echo ""

    # Write JSON results
    cat > "$output_file" << EOF
{
    "transport": "$transport",
    "model": "$MODEL",
    "iterations": $ITERATIONS,
    "max_tokens": $MAX_TOKENS,
    "results": [
        $(IFS=,; echo "${results[*]}")
    ],
    "summary": {
        "total_tokens": $total_tokens,
        "total_time_sec": $total_time,
        "avg_tokens_per_sec": $AVG_TPS,
        "avg_time_sec": $AVG_TIME
    },
    "timestamp": "$(date -Iseconds)"
}
EOF

    echo "$AVG_TPS"
}

start_with_transport() {
    local transport="$1"

    if $SKIP_START; then
        echo "Skipping cluster restart (--skip-start)"
        return 0
    fi

    echo "Starting cluster with transport: $transport"
    "$SCRIPT_DIR/start_cluster.sh" --transport="$transport" --model="$MODEL"

    # Wait for model to load
    sleep 10
}

stop_cluster() {
    if $SKIP_START; then
        return 0
    fi

    echo "Stopping cluster..."
    "$SCRIPT_DIR/start_cluster.sh" --stop 2>/dev/null || true
    sleep 5
}

# =============================================================================
# Main Benchmark Loop
# =============================================================================

declare -A RESULTS

IFS=',' read -ra TRANSPORT_LIST <<< "$TRANSPORTS"

for transport in "${TRANSPORT_LIST[@]}"; do
    transport=$(echo "$transport" | tr -d ' ')

    # Start cluster with this transport
    start_with_transport "$transport"

    # Wait for API
    echo "Waiting for API to be ready..."
    for i in {1..60}; do
        if curl -s "http://$CHIMERA_IP:8000/v1/models" > /dev/null 2>&1; then
            break
        fi
        sleep 5
    done

    # Run benchmark
    RESULTS[$transport]=$(run_single_benchmark "$transport")

    # Stop cluster
    stop_cluster
done

# =============================================================================
# Generate Summary
# =============================================================================

echo "============================================================"
echo "BENCHMARK SUMMARY"
echo "============================================================"
echo ""

# Build summary JSON
SUMMARY_JSON="{"
SUMMARY_JSON+="\"model\": \"$MODEL\","
SUMMARY_JSON+="\"iterations\": $ITERATIONS,"
SUMMARY_JSON+="\"max_tokens\": $MAX_TOKENS,"
SUMMARY_JSON+="\"timestamp\": \"$(date -Iseconds)\","
SUMMARY_JSON+="\"results\": {"

first=true
for transport in "${!RESULTS[@]}"; do
    tps="${RESULTS[$transport]}"
    echo "  $transport: $tps tokens/sec"

    if ! $first; then
        SUMMARY_JSON+=","
    fi
    SUMMARY_JSON+="\"$transport\": $tps"
    first=false
done

SUMMARY_JSON+="}}"

echo "$SUMMARY_JSON" | jq . > "$OUTPUT_DIR/summary.json"

# Calculate improvements
if [[ -n "${RESULTS[tcp]}" && -n "${RESULTS[roce]}" ]]; then
    TCP_TPS="${RESULTS[tcp]}"
    ROCE_TPS="${RESULTS[roce]}"
    IMPROVEMENT=$(echo "scale=2; (($ROCE_TPS - $TCP_TPS) / $TCP_TPS) * 100" | bc 2>/dev/null || echo "0")
    echo ""
    echo "  RoCE vs TCP improvement: ${IMPROVEMENT}%"
fi

if [[ -n "${RESULTS[tcp]}" && -n "${RESULTS[ttpoe]}" ]]; then
    TCP_TPS="${RESULTS[tcp]}"
    TTPOE_TPS="${RESULTS[ttpoe]}"
    IMPROVEMENT=$(echo "scale=2; (($TTPOE_TPS - $TCP_TPS) / $TCP_TPS) * 100" | bc 2>/dev/null || echo "0")
    echo "  TTPoe vs TCP improvement: ${IMPROVEMENT}%"
fi

echo ""
echo "Results saved to: $OUTPUT_DIR"

# =============================================================================
# Generate CSV
# =============================================================================

CSV_FILE="$OUTPUT_DIR/comparison.csv"
echo "transport,avg_tps,iterations,model" > "$CSV_FILE"
for transport in "${!RESULTS[@]}"; do
    echo "$transport,${RESULTS[$transport]},$ITERATIONS,$MODEL" >> "$CSV_FILE"
done

# =============================================================================
# Generate LaTeX Table
# =============================================================================

if $GENERATE_LATEX; then
    LATEX_FILE="$OUTPUT_DIR/results.tex"

    cat > "$LATEX_FILE" << 'EOF'
% Transport Benchmark Results
% Generated by ScuffedRDMA benchmark_all.sh

\begin{table}[h]
\centering
\caption{Transport Performance Comparison}
\label{tab:transport-benchmark}
\begin{tabular}{lccc}
\toprule
\textbf{Transport} & \textbf{Tokens/sec} & \textbf{vs TCP} & \textbf{Expected Latency} \\
\midrule
EOF

    TCP_TPS="${RESULTS[tcp]:-0}"

    for transport in tcp roce ttpoe; do
        if [[ -n "${RESULTS[$transport]}" ]]; then
            tps="${RESULTS[$transport]}"

            if [[ "$transport" == "tcp" ]]; then
                improvement="baseline"
                latency="\\textasciitilde1ms"
            elif [[ "$transport" == "roce" ]]; then
                improvement=$(echo "scale=1; (($tps - $TCP_TPS) / $TCP_TPS) * 100" | bc 2>/dev/null || echo "0")
                improvement="+${improvement}\\%"
                latency="\\textasciitilde190\\textmu s"
            elif [[ "$transport" == "ttpoe" ]]; then
                improvement=$(echo "scale=1; (($tps - $TCP_TPS) / $TCP_TPS) * 100" | bc 2>/dev/null || echo "0")
                improvement="+${improvement}\\%"
                latency="\\textasciitilde2\\textmu s"
            fi

            transport_name=$(echo "$transport" | tr '[:lower:]' '[:upper:]')
            if [[ "$transport" == "roce" ]]; then
                transport_name="Soft-RoCE"
            elif [[ "$transport" == "ttpoe" ]]; then
                transport_name="TTPoe"
            fi

            echo "$transport_name & $tps & $improvement & $latency \\\\" >> "$LATEX_FILE"
        fi
    done

    cat >> "$LATEX_FILE" << 'EOF'
\bottomrule
\end{tabular}
\end{table}
EOF

    echo "LaTeX table generated: $LATEX_FILE"
fi

echo "============================================================"
echo "Benchmark complete!"
echo "============================================================"
