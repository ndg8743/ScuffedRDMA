# Version 4: Tesla TTPoe (Time-Triggered Protocol over Ethernet)

Tesla's open-source low-latency transport protocol from the Dojo supercomputer.

## Overview

TTPoe is a hardware-first transport protocol that achieves:
- ~1-2μs latency (hardware-mediated)
- 10,000+ concurrent endpoints validated
- Near-zero CPU overhead
- Works with standard Ethernet (no special NICs)

**GitHub:** https://github.com/teslamotors/ttpoe

## Technical Specifications

| Feature | Value |
|---------|-------|
| Latency | 1-2 μs |
| Scale | 10,000+ endpoints |
| Transport | Raw Ethernet II / IPv4 encapsulation |
| CPU overhead | Near-zero (kernel module) |
| Hardware | Any Ethernet NIC |

## Architecture

TTPoe provides two kernel modules:

1. **modttpoe.ko** - Core transport layer
   - TCP-inspired state machine
   - Hardware-constrained optimizations
   - Automatic congestion management

2. **modttpip.ko** - Gateway module
   - IPv4 encapsulation
   - Multi-zone routing
   - Zone-based traffic isolation

## Building

### Prerequisites
```bash
# Install kernel headers
sudo apt-get install linux-headers-$(uname -r) build-essential
```

### Compile
```bash
git clone https://github.com/teslamotors/ttpoe.git
cd ttpoe
make all

# Verify modules built
ls -la modttpoe/modttpoe.ko modttpip/modttpip.ko
```

## Loading Modules

### Basic Load (modttpoe)
```bash
# Load with debug output
sudo insmod modttpoe/modttpoe.ko dev=eth0 verbose=2

# Check module loaded
lsmod | grep modttpoe

# View kernel messages
dmesg | tail -20
```

### Module Parameters
```bash
# dev - Network interface (required)
# dst - Destination MAC address
# vc - Virtual circuit ID
# verbose - Debug level (0-3)
# drop_rate - Simulate packet drops for testing

sudo insmod modttpoe/modttpoe.ko \
    dev=eth0 \
    dst=00:11:22:33:44:55 \
    vc=1 \
    verbose=2
```

### Gateway Module (modttpip)
```bash
# For multi-zone routing
sudo insmod modttpip/modttpip.ko \
    dev=eth0 \
    gwips=192.168.1.10,192.168.2.10 \
    verbose=1
```

## Testing

### Run Unit Tests
```bash
cd ttpoe
./tests/run.sh --target=2 -v

# Expected: 27 passing tests
```

### Basic Connectivity Test

**Node 1 (Server):**
```bash
sudo insmod modttpoe/modttpoe.ko dev=eth0 verbose=2
```

**Node 2 (Client):**
```bash
sudo insmod modttpoe/modttpoe.ko dev=eth0 dst=<node1_mac> verbose=2
```

Check connectivity via kernel logs:
```bash
dmesg | grep -i ttp
```

## Configuration

### /proc Interface
```bash
# View TTPoe state
cat /proc/net/ttpoe/state

# View statistics
cat /proc/net/ttpoe/stats
```

### Virtual Circuits
TTPoe supports multiple virtual circuits for traffic isolation:
```bash
# Load with specific VC
sudo insmod modttpoe/modttpoe.ko dev=eth0 vc=5 verbose=1
```

## Unloading
```bash
sudo rmmod modttpoe
sudo rmmod modttpip  # if loaded
```

## Comparison with Other Protocols

| Protocol | Latency | CPU Overhead | Hardware Required |
|----------|---------|--------------|-------------------|
| TTPoe | 1-2μs | Near-zero | Any Ethernet |
| RoCEv2 | <2μs | Near-zero | Mellanox NIC |
| Soft-RoCE | ~10μs | High | Any NIC |
| TCP | ~50μs | High | Any NIC |

## Use Cases

**Ideal for:**
- Custom AI/HPC clusters
- Edge deployments with controlled infrastructure
- High-frequency trading systems
- Real-time control systems

**Not ideal for:**
- Multi-vendor cloud environments
- Workloads requiring standard RDMA APIs
- Integration with existing NCCL/MPI stacks

## Limitations

1. **Kernel module required** - Not suitable for all environments
2. **Custom protocol** - No RDMA verbs API compatibility
3. **Limited ecosystem** - Primarily Tesla/Dojo focused
4. **Documentation** - Mainly code and spec sheets

## Integration Notes

TTPoe is not a drop-in replacement for RDMA. It's a separate transport layer designed for:
- Point-to-point high-speed communication
- Custom application protocols
- Hardware-accelerated message passing

For RDMA semantics, use RoCE (hardware or software).

## References

- GitHub: https://github.com/teslamotors/ttpoe
- Hot Chips 2024 presentation
- Tesla Dojo architecture papers
