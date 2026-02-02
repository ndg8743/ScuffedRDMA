#!/bin/bash
# =============================================================================
# ScuffedRDMA Multi-Node Cluster Startup Script
# =============================================================================
#
# Starts vLLM distributed inference cluster with configurable transport backend.
#
# Usage:
#   ./start_cluster.sh [OPTIONS]
#
# Options:
#   --transport=TYPE    Transport backend: tcp, roce, ttpoe, auto (default: auto)
#   --model=NAME        Model to serve (default: meta-llama/Llama-4-Scout-17B-16E)
#   --head=IP           Head node IP (default: 192.168.1.150)
#   --worker=IP         Worker node IP (default: 192.168.1.233)
#   --tp=N              Tensor parallel size (default: 3)
#   --pp=N              Pipeline parallel size (default: 2)
#   --dry-run           Print commands without executing
#   --stop              Stop cluster instead of starting
#   --help              Show this help message
#
# Environment Variables:
#   SCUFFED_TRANSPORT   Default transport type
#   VLLM_IMAGE          Docker image for vLLM
#   MODELS_DIR          Path to model cache
#
# =============================================================================

set -e

# Cluster configuration
CHIMERA_IP="${CHIMERA_IP:-192.168.1.150}"
CERBERUS_IP="${CERBERUS_IP:-192.168.1.233}"
VLLM_IMAGE="${VLLM_IMAGE:-vllm/vllm-openai:latest}"
MODELS_DIR="${MODELS_DIR:-/models}"
DEPLOY_DIR="${DEPLOY_DIR:-/home/nathan/ScuffedRDMA/deployment/multi-node}"

# Default options
TRANSPORT="${SCUFFED_TRANSPORT:-auto}"
MODEL="meta-llama/Llama-4-Scout-17B-16E"
TENSOR_PARALLEL=3
PIPELINE_PARALLEL=2
DRY_RUN=false
STOP_CLUSTER=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --transport=*)
            TRANSPORT="${1#*=}"
            shift
            ;;
        --model=*)
            MODEL="${1#*=}"
            shift
            ;;
        --head=*)
            CHIMERA_IP="${1#*=}"
            shift
            ;;
        --worker=*)
            CERBERUS_IP="${1#*=}"
            shift
            ;;
        --tp=*)
            TENSOR_PARALLEL="${1#*=}"
            shift
            ;;
        --pp=*)
            PIPELINE_PARALLEL="${1#*=}"
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --stop)
            STOP_CLUSTER=true
            shift
            ;;
        --help)
            head -40 "$0" | tail -35
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# Transport Configuration
# =============================================================================

get_nccl_env() {
    local transport="$1"

    case "$transport" in
        tcp)
            echo "NCCL_IB_DISABLE=1 NCCL_NET_GDR_LEVEL=0 NCCL_DEBUG=INFO"
            ;;
        roce)
            echo "NCCL_IB_HCA=rxe0 NCCL_IB_GID_INDEX=1 NCCL_NET_GDR_LEVEL=0 NCCL_DEBUG=INFO"
            ;;
        hwroce)
            echo "NCCL_IB_HCA=mlx5_0 NCCL_IB_GID_INDEX=3 NCCL_NET_GDR_LEVEL=5 NCCL_DEBUG=INFO"
            ;;
        ttpoe)
            echo "NCCL_IB_DISABLE=1 NCCL_NET_GDR_LEVEL=0 TTPOE_ENABLED=1 NCCL_DEBUG=INFO"
            ;;
        auto)
            # Auto-detect: check for RDMA devices
            if ssh "infra@$CHIMERA_IP" "lsmod | grep -q rdma_rxe" 2>/dev/null; then
                echo "NCCL_IB_HCA=rxe0 NCCL_IB_GID_INDEX=1 NCCL_NET_GDR_LEVEL=0 NCCL_DEBUG=INFO"
            else
                echo "NCCL_IB_DISABLE=1 NCCL_NET_GDR_LEVEL=0 NCCL_DEBUG=INFO"
            fi
            ;;
        *)
            echo "Error: Unknown transport: $transport" >&2
            exit 1
            ;;
    esac
}

# =============================================================================
# TTPoe Module Management
# =============================================================================

load_ttpoe_modules() {
    local node="$1"
    local interface="$2"
    local dst_mac="$3"

    echo "Loading TTPoe modules on $node..."

    ssh "infra@$node" "
        if ! lsmod | grep -q modttpoe; then
            cd /opt/ttpoe 2>/dev/null || cd ~/ttpoe
            sudo insmod modttpoe/modttpoe.ko dev=$interface dst=$dst_mac verbose=2
        fi
    " 2>/dev/null || echo "Warning: Failed to load TTPoe on $node"
}

unload_ttpoe_modules() {
    local node="$1"

    echo "Unloading TTPoe modules on $node..."
    ssh "infra@$node" "sudo rmmod modttpoe 2>/dev/null" || true
}

# =============================================================================
# Cluster Control
# =============================================================================

stop_cluster() {
    echo "Stopping cluster..."

    echo "Stopping head node (Chimera)..."
    ssh "infra@$CHIMERA_IP" "cd $DEPLOY_DIR && docker compose -f docker-compose.head.yaml down" 2>/dev/null || true

    echo "Stopping worker node (Cerberus)..."
    ssh "infra@$CERBERUS_IP" "cd $DEPLOY_DIR && docker compose -f docker-compose.worker.yaml down" 2>/dev/null || true

    if [[ "$TRANSPORT" == "ttpoe" ]]; then
        unload_ttpoe_modules "$CHIMERA_IP"
        unload_ttpoe_modules "$CERBERUS_IP"
    fi

    echo "Cluster stopped."
}

start_cluster() {
    local nccl_env
    nccl_env=$(get_nccl_env "$TRANSPORT")

    echo "============================================================"
    echo "ScuffedRDMA Cluster Startup"
    echo "============================================================"
    echo "Transport: $TRANSPORT"
    echo "Model: $MODEL"
    echo "Head: $CHIMERA_IP (TP=$TENSOR_PARALLEL)"
    echo "Worker: $CERBERUS_IP"
    echo "Pipeline Parallel: $PIPELINE_PARALLEL"
    echo "NCCL: $nccl_env"
    echo "============================================================"
    echo ""

    # Load TTPoe if needed
    if [[ "$TRANSPORT" == "ttpoe" ]]; then
        # Get MAC addresses
        CHIMERA_MAC=$(ssh "infra@$CHIMERA_IP" "cat /sys/class/net/eth0/address" 2>/dev/null || echo "unknown")
        CERBERUS_MAC=$(ssh "infra@$CERBERUS_IP" "cat /sys/class/net/eth0/address" 2>/dev/null || echo "unknown")

        load_ttpoe_modules "$CHIMERA_IP" "eth0" "$CERBERUS_MAC"
        load_ttpoe_modules "$CERBERUS_IP" "eth0" "$CHIMERA_MAC"
    fi

    # Build docker commands
    WORKER_CMD="cd $DEPLOY_DIR && $nccl_env docker compose -f docker-compose.worker.yaml up -d"
    HEAD_CMD="cd $DEPLOY_DIR && $nccl_env docker compose -f docker-compose.head.yaml up -d"

    if $DRY_RUN; then
        echo "[DRY RUN] Would execute on worker:"
        echo "  ssh infra@$CERBERUS_IP \"$WORKER_CMD\""
        echo ""
        echo "[DRY RUN] Would execute on head:"
        echo "  ssh infra@$CHIMERA_IP \"$HEAD_CMD\""
        return
    fi

    # Start worker first
    echo "Starting worker (Cerberus)..."
    ssh "infra@$CERBERUS_IP" "$WORKER_CMD"

    echo "Waiting for worker to initialize..."
    sleep 5

    # Start head
    echo "Starting head (Chimera)..."
    ssh "infra@$CHIMERA_IP" "$HEAD_CMD"

    echo ""
    echo "Waiting for vLLM to load model..."
    echo "(This may take 2-5 minutes for large models)"
    echo ""

    # Wait for API
    for i in {1..60}; do
        if curl -s "http://$CHIMERA_IP:8000/v1/models" > /dev/null 2>&1; then
            echo ""
            echo "============================================================"
            echo "Cluster ready!"
            echo "API endpoint: http://$CHIMERA_IP:8000/v1"
            echo "============================================================"
            return 0
        fi
        echo -n "."
        sleep 5
    done

    echo ""
    echo "Warning: Timeout waiting for API. Check logs with:"
    echo "  ssh infra@$CHIMERA_IP 'docker logs vllm-head'"
}

# =============================================================================
# Main
# =============================================================================

if $STOP_CLUSTER; then
    stop_cluster
else
    start_cluster
fi
