# Version 3: Hardware RoCE with Mellanox ConnectX

This guide covers setting up true hardware RDMA with Mellanox ConnectX NICs.

## Overview

Hardware RoCE (RDMA over Converged Ethernet) provides:
- Sub-2μs latency (vs ~10μs for Soft-RoCE)
- Zero CPU overhead for data transfer
- GPUDirect RDMA support for GPU-to-GPU communication
- Production-grade reliability

## Hardware Requirements

### Supported NICs
| NIC | Speed | GPUDirect | Notes |
|-----|-------|-----------|-------|
| ConnectX-3 | 40/56 Gbps | Limited | Legacy, avoid for new deployments |
| ConnectX-4 | 25/50/100 Gbps | Yes | Recommended minimum |
| ConnectX-5 | 25/50/100 Gbps | Yes | Production standard |
| ConnectX-6 | 100/200 Gbps | Yes | Current generation |
| ConnectX-7 | 200/400 Gbps | Yes | Datacenter scale |

### BIOS Settings
- Enable VT-d / IOMMU
- Enable SR-IOV (if using virtual functions)
- Enable PCIe ACS (Access Control Services)

### Kernel Parameters
```bash
# Add to /etc/default/grub
GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt"

sudo update-grub
sudo reboot
```

## Installation Order (CRITICAL)

**MOFED → CUDA → nvidia-peermem**

The order is non-negotiable. GPU drivers must compile against MOFED symbols.

```
1. MOFED/DOCA-Host
   └── Exports kernel symbols for RDMA
         ↓
2. CUDA Toolkit & NVIDIA Driver
   └── Compiles against MOFED for GPUDirect
         ↓
3. nvidia-peermem module
   └── Bridge between GPU and NIC
```

**WARNING:** Updating MOFED requires reinstalling CUDA drivers.

---

## Step 1: Install MOFED

### Download
```bash
# Check latest version at: https://network.nvidia.com/products/infiniband-drivers/linux/mlnx_ofed/

# Ubuntu 22.04 example
wget https://content.mellanox.com/ofed/MLNX_OFED-24.01-0.3.3.1/MLNX_OFED_LINUX-24.01-0.3.3.1-ubuntu22.04-x86_64.tgz

tar xzf MLNX_OFED_LINUX-*.tgz
cd MLNX_OFED_LINUX-*/
```

### Install
```bash
# Full installation with kernel support
sudo ./mlnxofedinstall --add-kernel-support

# Restart driver stack
sudo /etc/init.d/openibd restart

# Verify installation
ofed_info -s
# Expected: MLNX_OFED_LINUX-24.01-0.3.3.1

ibstat
# Should show ConnectX device with State: Active
```

---

## Step 2: Configure RoCE

### Check Device
```bash
# List RDMA devices
ibv_devices

# Detailed info
ibv_devinfo -d mlx5_0

# Check link status
ibstat mlx5_0
```

### Set RoCE Mode
```bash
# RoCEv2 is recommended (routable)
sudo cma_roce_mode -d mlx5_0 -p 1 -m 2

# Verify
cma_roce_mode -d mlx5_0 -p 1
# Expected: RoCE v2
```

### Configure GID Table
```bash
# Show GIDs
show_gids

# The IPv4-mapped address (::ffff:x.x.x.x) is typically GID index 1
```

---

## Step 3: Install CUDA (After MOFED)

```bash
# Download CUDA toolkit
wget https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda_12.4.0_550.54.14_linux.run

# Install (driver will detect MOFED symbols)
sudo sh cuda_12.4.0_550.54.14_linux.run

# Verify
nvidia-smi
nvcc --version
```

---

## Step 4: Enable GPUDirect RDMA

```bash
# Load nvidia-peermem module
sudo modprobe nvidia-peermem

# Make persistent
echo "nvidia-peermem" | sudo tee /etc/modules-load.d/nvidia-peermem.conf

# Verify
lsmod | grep nvidia_peermem

# Check GPU BAR1 for RDMA
nvidia-smi -q | grep -A3 "BAR1"
```

---

## Step 5: Verify GPUDirect RDMA

### CPU-to-CPU RDMA Test
```bash
# Server
ib_write_bw -d mlx5_0 --report_gbits

# Client
ib_write_bw -d mlx5_0 --report_gbits <server_ip>

# Expected: ~100 Gbps for ConnectX-5/6
```

### GPU-to-GPU RDMA Test
```bash
# Server (use GPU 0)
ib_write_bw -d mlx5_0 --report_gbits --use_cuda=0

# Client (use GPU 0)
ib_write_bw -d mlx5_0 --report_gbits --use_cuda=0 <server_ip>

# Expected: Similar throughput, but using GPU memory
```

---

## Network Configuration

### Switch Requirements for RoCEv2
- DCB (Data Center Bridging) support
- PFC (Priority Flow Control) enabled
- ECN (Explicit Congestion Notification) configured

### PFC Configuration (per switch vendor)
```bash
# Enable PFC on priority 3 (typical RDMA priority)
# This is switch-specific - consult vendor documentation
```

### ECN Configuration
```bash
# Enable ECN marking on the NIC
sudo mlnx_qos -i ens785f0 --trust=dscp
sudo mlnx_qos -i ens785f0 --pfc=0,0,0,1,0,0,0,0

# Set ECN thresholds
sudo cma_roce_tos -d mlx5_0 -t 106  # DSCP 26 for RoCE
```

---

## Environment Variables for NCCL

```bash
# Hardware RoCE with GPUDirect
export NCCL_IB_HCA=mlx5_0
export NCCL_IB_GID_INDEX=3          # Adjust based on show_gids output
export NCCL_NET_GDR_LEVEL=5         # Enable GPUDirect (default)
export NCCL_DEBUG=INFO

# Do NOT set NCCL_NET_GDR_LEVEL=0 (disables GPUDirect)
```

---

## Docker Configuration

### Privileged Container with RDMA
```yaml
services:
  rdma-app:
    image: your-image
    privileged: true
    network_mode: host
    ipc: host
    volumes:
      - /dev/infiniband:/dev/infiniband
    environment:
      - NCCL_IB_HCA=mlx5_0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

### Non-Privileged with Device Mapping
```yaml
services:
  rdma-app:
    devices:
      - /dev/infiniband/uverbs0:/dev/infiniband/uverbs0
      - /dev/infiniband/rdma_cm:/dev/infiniband/rdma_cm
    cap_add:
      - IPC_LOCK
      - SYS_RESOURCE
```

---

## Troubleshooting

### NCCL Falls Back to TCP
```bash
# Check NCCL logs for "NET/IB"
# If you see "NET/Socket", RDMA isn't working

# Verify RDMA device
ibv_devinfo

# Check permissions
ls -la /dev/infiniband/
```

### nvidia-peermem Not Loading
```bash
# Check if MOFED was installed before CUDA
modinfo nvidia-peermem

# If missing symbols, reinstall CUDA after MOFED
sudo /usr/local/cuda/bin/cuda-uninstaller
# Then reinstall CUDA
```

### Low Bandwidth
```bash
# Check link speed
ibstat mlx5_0 | grep Rate

# Check for errors
ethtool -S ens785f0 | grep -i error

# Verify PCIe speed
lspci -vvv -s <pci_address> | grep -i width
```

### GPUDirect Not Working
```bash
# Check GPU and NIC are on same PCIe root
nvidia-smi topo -m

# Check nvidia-peermem
lsmod | grep nvidia_peermem

# Verify BAR1 mapping
nvidia-smi -q | grep -A5 "BAR1"
```

---

## Performance Tuning

### IRQ Affinity
```bash
# Pin IRQs to specific CPUs
sudo set_irq_affinity_bynode.sh 0 mlx5_0
```

### Hugepages
```bash
# Allocate hugepages
echo 4096 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Mount hugetlbfs
sudo mount -t hugetlbfs nodev /mnt/huge
```

### NUMA Awareness
```bash
# Check NUMA topology
numactl --hardware

# Pin RDMA operations to local NUMA node
numactl --cpunodebind=0 --membind=0 <application>
```

---

## Comparison

| Metric | Soft-RoCE | Hardware RoCE |
|--------|-----------|---------------|
| Latency | ~10μs | <2μs |
| Bandwidth | Limited by CPU | Line rate |
| CPU overhead | High | Near-zero |
| GPUDirect | No | Yes |
| Cost | $0 | $200-2000+ |
| Production use | Development only | Recommended |
