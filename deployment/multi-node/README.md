# Multi-Node gpt-oss-120b: TCP vs RDMA Benchmark

Split gpt-oss-120b across 5 GPUs to demonstrate RDMA benefits.

## Cluster Configuration

| Node | GPUs | VRAM | Role |
|------|------|------|------|
| Chimera | 3× RTX 3090 | 72GB | Head (TP=3) |
| Cerberus | 2× RTX 5090 | 64GB | Worker |
| **Total** | **5 GPUs** | **136GB** | PP=2 |

## Why Multi-Node Shows RDMA Benefits

Single-node inference uses PCIe/NVLink (200+ GB/s) - network is unused.

Multi-node requires **cross-node tensor transfers**:
- KV cache synchronization
- Activation transfers between pipeline stages
- Gradient communication (if training)

This is where RDMA (0.92 Gb/s, 190μs) vs TCP makes a measurable difference.

## Quick Start

### Step 1: Start Cerberus (Worker) FIRST

```bash
# SSH to Cerberus
ssh infra@192.168.1.233

# For TCP baseline:
cd /home/nathan/ScuffedRDMA/deployment/multi-node
NCCL_IB_DISABLE=1 NCCL_NET_GDR_LEVEL=0 docker compose -f docker-compose.worker.yaml up -d

# OR for RDMA:
NCCL_IB_HCA=rxe0 docker compose -f docker-compose.worker.yaml up -d
```

### Step 2: Start Chimera (Head)

```bash
# SSH to Chimera
ssh infra@192.168.1.150

# For TCP baseline:
cd /home/nathan/ScuffedRDMA/deployment/multi-node
NCCL_IB_DISABLE=1 NCCL_NET_GDR_LEVEL=0 docker compose -f docker-compose.head.yaml up -d

# OR for RDMA:
NCCL_IB_HCA=rxe0 docker compose -f docker-compose.head.yaml up -d
```

### Step 3: Verify Cluster

```bash
# Check Ray cluster (should show 5 GPUs)
curl http://192.168.1.150:8265/api/cluster_status | jq

# Check vLLM models
curl http://192.168.1.150:8000/v1/models
```

### Step 4: Run Benchmark

```bash
# From any machine
for i in 1 2 3 4 5; do
  echo -n "Iteration $i: "
  START=$(date +%s.%N)
  curl -s http://192.168.1.150:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"openai/gpt-oss-120b","prompt":"Explain RDMA in 100 words.","max_tokens":100}' \
    | jq -r '.usage.completion_tokens'
  END=$(date +%s.%N)
  echo " tokens in $(echo "$END - $START" | bc)s"
done
```

## Full Benchmark Script

```bash
./benchmark_tcp_vs_rdma.sh
```

This script:
1. Starts cluster with TCP (RDMA disabled)
2. Runs 5 iterations, records throughput
3. Restarts cluster with RDMA enabled
4. Runs 5 iterations, records throughput
5. Compares results

## Environment Variables

### TCP Mode (Baseline)
```bash
export NCCL_IB_DISABLE=1
export NCCL_NET_GDR_LEVEL=0
```

### RDMA Mode (Soft-RoCE)
```bash
export NCCL_IB_HCA=rxe0
export NCCL_SOCKET_IFNAME=enp71s0  # Chimera
export NCCL_SOCKET_IFNAME=eno2np1  # Cerberus
```

## Expected Results

| Mode | Throughput | Latency | Notes |
|------|------------|---------|-------|
| TCP | ~80-90 tok/s | Higher | Cross-node via sockets |
| RDMA (Soft-RoCE) | ~95-105 tok/s | Lower | Cross-node via RDMA |
| RDMA (Hardware) | ~120-140 tok/s | Lowest | With Mellanox NICs |

**Expected RDMA improvement: 10-20%** over TCP for multi-node inference.

## Why MXFP4 Matters for RDMA

gpt-oss-120b uses **Microscaling (MX) data formats** ([arXiv:2310.10537](https://arxiv.org/abs/2310.10537)):

| Format | Model Size | Bandwidth Needed |
|--------|------------|------------------|
| FP16 | ~240GB | 4x more |
| MXFP4 | **63GB** | **4x less** |

Benefits for distributed inference:
- **4x less data** transferred over RDMA
- Faster KV cache synchronization
- Lower network bottleneck impact
- FlashInfer provides optimized MXFP4 kernels

## Monitoring

```bash
# Watch NCCL logs for RDMA usage
docker logs -f vllm-gptoss 2>&1 | grep -i "nccl\|rdma\|ib"

# Expected with RDMA:
# NCCL INFO NET/IB : Using [0]rxe0:1/RoCE

# Expected with TCP:
# NCCL INFO NET/Socket : Using [0]enp71s0:192.168.1.150
```

## Troubleshooting

### Worker not connecting
```bash
# Check Ray status on worker
docker logs ray-worker

# Verify network connectivity
ping 192.168.1.150
nc -zv 192.168.1.150 6379
```

### RDMA not detected
```bash
# Verify Soft-RoCE device exists
rdma link show
ibv_devices

# If missing, create it:
sudo rdma link add rxe0 type rxe netdev enp71s0
```

### Out of memory
- Reduce `--max-model-len` to 2048
- Reduce `--gpu-memory-utilization` to 0.85
