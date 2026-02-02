# Version 6: rdma-tas (RDMA over TAS/DPDK)

Academic RDMA implementation over TCP Acceleration Service.

## Overview

rdma-tas provides RDMA semantics over commodity Ethernet using DPDK:
- ~5μs latency (single connection)
- Clean RDMA verbs-like API
- No special hardware required (DPDK-compatible NIC)
- EuroSys 2019 peer-reviewed foundation

**GitHub:** https://github.com/mani-shailesh/rdma-tas
**Paper:** https://mani-shailesh.github.io/res/docs/SRoCE.pdf

## Technical Specifications

| Feature | Value |
|---------|-------|
| Latency | ~5μs (single connection) |
| Throughput | 7× faster than Linux TCP |
| API | RDMA verbs-like |
| Hardware | DPDK-compatible NIC |
| Status | Research prototype |

## Architecture

rdma-tas layers RDMA on top of TAS (TCP Acceleration Service):

```
Application
    ↓
libtas_rdma.so (RDMA API)
    ↓
TAS Fast Path (DPDK)
    ↓
Network
```

### Design Choices
- RDMA processing in TAS fast-path cores
- ~1-2 cache lines per connection state
- Leverages TAS auto-scaling

## Prerequisites

### Hardware
- DPDK-compatible NIC:
  - Intel i40e, ixgbe
  - Mellanox mlx5
  - Virtio (for testing)

### Software
```bash
# Install DPDK
sudo apt-get install dpdk dpdk-dev libdpdk-dev

# Install build tools
sudo apt-get install build-essential

# Configure hugepages
echo 1024 | sudo tee /sys/devices/system/node/node*/hugepages/hugepages-2048kB/nr_hugepages
sudo mount -t hugetlbfs nodev /mnt/huge
```

## Building

### Clone and Build
```bash
git clone https://github.com/mani-shailesh/rdma-tas.git
cd rdma-tas

# Standard build (Intel NICs)
make RTE_SDK=/usr

# Mellanox build
make -f Makefile.mlx RTE_SDK=/usr
```

### Output Files
- `tas/tas` - TAS service binary
- `lib/libtas.so` - TAS client library
- `lib/libtas_rdma.so` - RDMA library
- `tests/rdma_*` - Test programs

## Running TAS

### Bind NIC to DPDK
```bash
# For Intel NICs
sudo modprobe vfio-pci
sudo dpdk-devbind.py -b vfio-pci 0000:08:00.0

# Verify
dpdk-devbind.py --status
```

### Start TAS Service
```bash
sudo ./tas/tas --ip-addr=10.0.0.1/24 --fp-cores-max=2
```

### TAS Parameters
```
--ip-addr       IP address for TAS
--fp-cores-max  Number of fast-path cores
--fp-no-ints    Disable interrupts (use polling)
--fp-no-autoscale  Disable auto-scaling
```

## RDMA API

### Header
```c
#include <tas_rdma.h>
```

### Initialization
```c
int rdma_init(void);
```

### Connection Setup (Server)
```c
int rdma_listen(const struct sockaddr_in* localaddr, int backlog);
int rdma_accept(int listenfd, struct sockaddr_in* remoteaddr,
                void **mr_base, uint32_t *mr_len);
```

### Connection Setup (Client)
```c
int rdma_connect(const struct sockaddr_in* remoteaddr,
                 void **mr_base, uint32_t *mr_len);
```

### One-Sided Operations
```c
// Read from remote memory
int rdma_read(int fd, uint32_t len, uint32_t loffset, uint32_t roffset);

// Write to remote memory
int rdma_write(int fd, uint32_t len, uint32_t loffset, uint32_t roffset);
```

### Completion Queue
```c
int rdma_cq_poll(int fd, struct rdma_wqe* compl_evs, uint32_t num);
```

## Example: RDMA Server

```c
#include <tas_rdma.h>
#include <arpa/inet.h>

int main() {
    rdma_init();

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = inet_addr("10.0.0.1"),
        .sin_port = htons(5005)
    };

    void *mr_base;
    uint32_t mr_len;

    int lfd = rdma_listen(&addr, 8);
    int fd = rdma_accept(lfd, NULL, &mr_base, &mr_len);

    // Write data to remote
    char *data = mr_base;
    strcpy(data, "Hello RDMA!");
    rdma_write(fd, strlen(data), 0, 0);

    // Poll completion
    struct rdma_wqe cqe;
    rdma_cq_poll(fd, &cqe, 1);

    return 0;
}
```

## Running Tests

```bash
# Server
LD_PRELOAD=lib/libtas.so ./tests/rdma_server

# Client
LD_PRELOAD=lib/libtas.so ./tests/rdma_client
```

## Limitations

### Performance Degradation
- **Single connection:** ~5μs, excellent
- **64+ connections:** 45-60% throughput drop
- Not suitable for many-connection workloads

### Research Status
- Academic prototype, not production-hardened
- Limited testing at scale
- DPDK dependency adds complexity

## Use Cases

**Good for:**
- Understanding RDMA semantics
- Benchmarking on commodity hardware
- Research and education
- Single-connection high-throughput

**Not suitable for:**
- Production clusters
- Many-connection workloads
- Environments without DPDK expertise

## Comparison

| Metric | rdma-tas | Hardware RoCE | Soft-RoCE |
|--------|----------|---------------|-----------|
| Latency | ~5μs | <2μs | ~10μs |
| Connections | <64 | Thousands | Hundreds |
| CPU overhead | Medium | Low | High |
| Hardware | DPDK NIC | Mellanox | Any |
| Maturity | Research | Production | Deprecated |

## References

- GitHub: https://github.com/mani-shailesh/rdma-tas
- Paper: EuroSys 2019
- TAS Base: https://github.com/tcp-acceleration-service/tas
