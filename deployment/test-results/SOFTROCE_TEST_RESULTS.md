# Soft-RoCE Test Results

**Date:** February 2, 2026
**Cluster:** Chimera ↔ Cerberus

## Configuration

| Machine | Device | Interface | IP | Speed |
|---------|--------|-----------|-----|-------|
| Chimera | rxe0 | enp71s0 | 192.168.1.150 | 10G (Aquantia) |
| Cerberus | rxe0 | eno2np1 | 192.168.1.233 | 10G (Intel X710) |

## Bandwidth Test (ib_write_bw)

### WiFi (wlp227s0 - 192.168.1.242)
```
BW average: 0.28 Gb/sec
MsgRate: 0.000541 Mpps
```

### 10G Ethernet (eno2np1 - 192.168.1.233)
```
BW peak: 0.92 Gb/sec
BW average: 0.92 Gb/sec
MsgRate: 0.001754 Mpps
```

**Improvement:** 3.3x faster on 10G Ethernet vs WiFi

## Latency Test (ib_write_lat)

```
Message size: 2 bytes
Iterations: 1000

t_min:     130.21 μs
t_max:     219.66 μs
t_typical: 198.91 μs
t_avg:     189.61 μs
t_stdev:   17.03 μs
99%:       207.14 μs
99.9%:     219.66 μs
```

## Analysis

### Expected vs Actual
| Metric | Expected (Soft-RoCE) | Actual | Notes |
|--------|---------------------|--------|-------|
| Latency | ~10 μs | ~190 μs | High overhead |
| Bandwidth | ~5-8 Gb/sec | 0.92 Gb/sec | CPU limited |

### Why Latency is High
1. **Software RDMA:** All operations go through kernel, not hardware offload
2. **CPU overhead:** Soft-RoCE emulates RDMA in software
3. **No zero-copy:** Data copies between kernel and user space
4. **Deprecated:** NVIDIA deprecated Soft-RoCE in Oct 2023

### Recommendations
- For development/testing: Soft-RoCE is adequate
- For production: Use Hardware RoCE (Mellanox ConnectX)
- Expected hardware RoCE latency: <2 μs

## Commands Used

### Setup
```bash
# Create Soft-RoCE device
sudo modprobe rdma_rxe
sudo rdma link add rxe0 type rxe netdev <interface>

# Verify
ibv_devices
ibv_devinfo -d rxe0
```

### Bandwidth Test
```bash
# Server
ib_write_bw -d rxe0 --report_gbits

# Client
ib_write_bw -d rxe0 --report_gbits <server_ip>
```

### Latency Test
```bash
# Server
ib_write_lat -d rxe0

# Client
ib_write_lat -d rxe0 <server_ip>
```

## Firewall Rules Added
```bash
# Allow RDMA traffic from local LAN
sudo ufw allow from 192.168.1.0/24 to any port 4791 proto udp comment 'RoCEv2'
sudo ufw allow from 192.168.1.0/24 comment 'Allow local LAN for RDMA'
```
