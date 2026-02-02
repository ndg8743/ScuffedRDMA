# Version 1: SR-IOV + GPUDirect RDMA Setup

This guide covers setting up true hardware RDMA with GPUDirect for multi-node LLM inference.

## Prerequisites

### Hardware Requirements
- Mellanox ConnectX-4/5/6 NIC (or newer)
- NVIDIA GPU (Kepler-class or newer)
- Both devices on same PCI Express root complex

### BIOS Settings
- Enable VT-d / IOMMU
- Enable SR-IOV

### Kernel Parameters
Add to GRUB:
```bash
GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt"
sudo update-grub
sudo reboot
```

## CRITICAL: Installation Order

**MOFED → CUDA → nvidia-peermem**

The GPU driver must compile against MOFED symbols for GPUDirect support.

```
1. MOFED/DOCA-Host (network driver)
   └── Exports kernel symbols for RDMA
         ↓
2. CUDA Toolkit & NVIDIA Driver
   └── Compiles against MOFED symbols
         ↓
3. nvidia-peermem module
   └── Bridge between GPU and NIC
```

**WARNING:** If you update MOFED later, you MUST reinstall the NVIDIA driver.

## Step 1: Install MOFED

```bash
# Download MOFED (check for latest version)
wget https://content.mellanox.com/ofed/MLNX_OFED-24.01-0.3.3.1/MLNX_OFED_LINUX-24.01-0.3.3.1-ubuntu22.04-x86_64.tgz
tar xzf MLNX_OFED_*.tgz
cd MLNX_OFED_*

# Install with kernel support
sudo ./mlnxofedinstall --add-kernel-support

# Restart driver stack
sudo /etc/init.d/openibd restart

# Verify
ibstat
ofed_info -s
```

## Step 2: Enable SR-IOV

```bash
# Start Mellanox Software Tools
sudo mst start
sudo mst status

# Enable SR-IOV (2 Virtual Functions)
sudo mlxconfig -d /dev/mst/mt4121_pciconf0 set SRIOV_EN=1 NUM_OF_VFS=2

# Reboot required
sudo reboot
```

After reboot:
```bash
# Create Virtual Functions
echo 2 | sudo tee /sys/class/infiniband/mlx5_0/device/sriov_numvfs

# Verify VFs
lspci | grep Mellanox

# Set MAC for RoCE (if using RoCEv2)
sudo ip link set dev ens785f0 vf 0 mac 00:11:22:33:44:55
```

## Step 3: Install CUDA (AFTER MOFED)

```bash
# Download CUDA toolkit
wget https://developer.download.nvidia.com/compute/cuda/12.4.0/local_installers/cuda_12.4.0_550.54.14_linux.run

# Install (driver will detect MOFED symbols)
sudo sh cuda_12.4.0_550.54.14_linux.run

# Verify
nvidia-smi
nvcc --version
```

## Step 4: Enable nvidia-peermem

```bash
# Load the module
sudo modprobe nvidia-peermem

# Make persistent
echo "nvidia-peermem" | sudo tee /etc/modules-load.d/nvidia-peermem.conf

# Verify
lsmod | grep nvidia_peermem
```

## Step 5: Verify GPUDirect RDMA

```bash
# On Server (Chimera)
ib_write_bw -d mlx5_0 --report_gbits --use_cuda=0

# On Client (Cerberus)
ib_write_bw -d mlx5_0 --report_gbits --use_cuda=0 192.168.1.150
```

Expected output: ~100 Gb/s with <5μs latency

## Environment Variables

For vLLM/NCCL with GPUDirect:
```bash
# DO NOT disable GPUDirect:
# NCCL_NET_GDR_LEVEL=0  # Don't set this!

export NCCL_IB_HCA=mlx5_0
export NCCL_DEBUG=INFO
```

## Troubleshooting

### nvidia-peermem not loading
```bash
# Check if MOFED was installed before CUDA
modinfo nvidia-peermem
# If missing, reinstall CUDA after MOFED
```

### NCCL falling back to TCP
```bash
# Check NCCL logs for "NET/IB"
# Should see: NCCL INFO NET/IB : Using [0]mlx5_0
# If you see NET/Socket, RDMA isn't working
```

### VFs not showing
```bash
# Check IOMMU is enabled
dmesg | grep -i iommu
# Check SR-IOV is enabled in firmware
sudo mst start
sudo mlxconfig -d /dev/mst/mt4121_pciconf0 query | grep SRIOV
```
