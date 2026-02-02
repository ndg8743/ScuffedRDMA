# Version 2: Soft-RoCE (Software RDMA) Setup

This guide covers setting up software RDMA over existing Ethernet adapters using the RXE kernel module.

## Overview

Soft-RoCE (rxe) emulates RDMA over standard Ethernet NICs. It provides:
- RDMA semantics without hardware investment
- ~10μs latency (vs <2μs for hardware RDMA)
- Higher CPU overhead

**Note:** This is suitable for development/testing. For production, consider Mellanox hardware.

## Prerequisites

### Hardware
- Standard Ethernet NIC (10GbE+ recommended)
- Current setup:
  - Chimera: Aquantia 10G (enp71s0)
  - Cerberus: Intel X710 10G (eno1np0/wlp227s0)

## Step 1: Install RDMA Stack

```bash
sudo apt update
sudo apt install -y rdma-core ibverbs-providers perftest libibverbs-dev

# Install Python bindings (optional)
pip install pyverbs
```

## Step 2: Load RXE Kernel Module

```bash
# Load the module
sudo modprobe rdma_rxe

# Make persistent
echo "rdma_rxe" | sudo tee /etc/modules-load.d/rdma_rxe.conf
```

## Step 3: Create Soft-RoCE Interface

### On Chimera
```bash
# Find primary interface
ip a  # enp71s0 for Chimera

# Create rxe device
sudo rdma link add rxe0 type rxe netdev enp71s0

# Verify
ibv_devinfo -d rxe0
ibv_devices
```

### On Cerberus
```bash
# Find primary interface (use wired for stability)
ip a  # eno1np0 or eno2np1 for Cerberus

# Create rxe device
sudo rdma link add rxe0 type rxe netdev eno2np1

# Verify
ibv_devinfo -d rxe0
```

## Step 4: Persistent Soft-RoCE (systemd)

Create `/etc/systemd/system/softroce.service`:

```ini
[Unit]
Description=Soft-RoCE Setup
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/rdma link add rxe0 type rxe netdev <INTERFACE>
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Replace `<INTERFACE>` with:
- Chimera: `enp71s0`
- Cerberus: `eno2np1`

Enable:
```bash
sudo systemctl enable --now softroce.service
```

## Step 5: Verify RDMA Connectivity

```bash
# On Chimera (server)
rping -s -v -a 192.168.1.150

# On Cerberus (client)
rping -c -v -a 192.168.1.150

# Bandwidth test
# Server:
ib_write_bw -d rxe0

# Client:
ib_write_bw -d rxe0 192.168.1.150
```

## Environment Variables for vLLM/NCCL

```bash
# Soft-RoCE configuration
export NCCL_IB_HCA=rxe0
export NCCL_NET_GDR_LEVEL=0    # CRITICAL: Disable GPUDirect (not compatible)
export NCCL_IB_GID_INDEX=3     # RoCEv2
export NCCL_DEBUG=INFO
```

**Important:** `NCCL_NET_GDR_LEVEL=0` is required because GPUDirect RDMA doesn't work with software RDMA.

## Docker Configuration

Update docker-compose.yaml:
```yaml
environment:
  - NCCL_IB_HCA=rxe0
  - NCCL_NET_GDR_LEVEL=0
  - NCCL_IB_GID_INDEX=3
  - NCCL_DEBUG=INFO
```

## Verification

Check NCCL is using Soft-RoCE:
```bash
# Should see in vLLM logs:
# NCCL INFO NET/IB : Using [0]rxe0:1/RoCE
```

If you see `NET/Socket`, Soft-RoCE isn't working.

## Troubleshooting

### rxe0 not appearing
```bash
# Check module is loaded
lsmod | grep rdma_rxe

# Manually create link
sudo rdma link add rxe0 type rxe netdev <interface>
```

### NCCL falls back to TCP
```bash
# Check rxe0 is active on both nodes
ibv_devinfo -d rxe0

# Check firewall allows RoCE UDP port 4791
sudo ufw allow 4791/udp

# Verify NCCL_IB_HCA is set
echo $NCCL_IB_HCA
```

### Performance Warning

Soft-RoCE uses CPU for RDMA emulation. In some cases, highly optimized TCP (default NCCL) may actually be faster than Soft-RoCE due to:
- TCP offload engines in modern NICs
- Lower CPU overhead with kernel bypass

Benchmark both configurations for your specific workload.

## Comparison: Soft-RoCE vs Hardware RDMA

| Metric | Soft-RoCE | Mellanox Hardware |
|--------|-----------|-------------------|
| Latency | ~10μs | <2μs |
| CPU overhead | High | Near-zero |
| GPUDirect | Not supported | Supported |
| Hardware cost | $0 | $200-1000+ per NIC |
