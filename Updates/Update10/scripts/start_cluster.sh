#!/bin/bash
# Unified cluster start script with transport selection
# Usage: ./start_cluster.sh --transport=roce --model=llama4

TRANSPORT="${SCUFFED_TRANSPORT:-auto}"

case "$TRANSPORT" in
    tcp)
        NCCL_ENV="NCCL_IB_DISABLE=1 NCCL_NET_GDR_LEVEL=0"
        ;;
    roce)
        NCCL_ENV="NCCL_IB_HCA=rxe0 NCCL_IB_GID_INDEX=1"
        ;;
    ttpoe)
        ./load_ttpoe.sh load --dev=eth0 --dst=$PEER_MAC
        NCCL_ENV="NCCL_IB_DISABLE=1 TTPOE_ENABLED=1"
        ;;
esac

ssh infra@$WORKER_IP \
    "$NCCL_ENV docker compose -f docker-compose.worker.yaml up -d"
ssh infra@$HEAD_IP \
    "$NCCL_ENV docker compose -f docker-compose.head.yaml up -d"
