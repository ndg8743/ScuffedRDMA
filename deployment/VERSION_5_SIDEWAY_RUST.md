# Version 5: Sideway - Rust RDMA Library

Modern Rust abstraction layer for RDMA programming.

## Overview

Sideway provides:
- Safe Rust bindings to libibverbs/librdmacm
- Modern ibverbs APIs (ibv_wr_*, ibv_start_poll)
- Dynamic linking (no vendoring required)
- Tested at 400 Gbps on Mellanox ConnectX-6/7

**GitHub:** https://github.com/RDMA-Rust/sideway

## Features

| Feature | Status |
|---------|--------|
| Modern ibverbs API | ✓ |
| Dynamic linking | ✓ |
| ConnectX-5/6/7 support | ✓ |
| BlueField DPA | ✓ |
| SoftRoCE | ✓ |
| 400 Gbps validated | ✓ |

## Installation

### Prerequisites
```bash
# Install RDMA development libraries
sudo apt-get install libibverbs-dev librdmacm-dev

# Install Rust (if not present)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Add to Cargo.toml
```toml
[dependencies]
sideway = "0.4"  # Check for latest version
```

## Basic Usage

### Create RDMA Context
```rust
use sideway::verbs::{Device, DeviceList};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // List available RDMA devices
    let device_list = DeviceList::new()?;

    for device in device_list.iter() {
        println!("Device: {}", device.name()?);
    }

    // Open first device
    let device = device_list.get(0)?;
    let context = device.open()?;

    Ok(())
}
```

### Create Queue Pair
```rust
use sideway::verbs::{Context, ProtectionDomain, CompletionQueue, QueuePair};

fn create_qp(ctx: &Context) -> Result<QueuePair, Box<dyn std::error::Error>> {
    // Create protection domain
    let pd = ProtectionDomain::new(ctx)?;

    // Create completion queues
    let send_cq = CompletionQueue::new(ctx, 128)?;
    let recv_cq = CompletionQueue::new(ctx, 128)?;

    // Create queue pair
    let qp = QueuePair::new(&pd, &send_cq, &recv_cq)?;

    Ok(qp)
}
```

### Memory Registration
```rust
use sideway::verbs::{MemoryRegion, AccessFlags};

fn register_memory(pd: &ProtectionDomain, buffer: &mut [u8])
    -> Result<MemoryRegion, Box<dyn std::error::Error>>
{
    let mr = MemoryRegion::new(
        pd,
        buffer,
        AccessFlags::LOCAL_WRITE | AccessFlags::REMOTE_READ | AccessFlags::REMOTE_WRITE
    )?;

    Ok(mr)
}
```

### Post Send (Modern API)
```rust
use sideway::verbs::{SendWorkRequest, SendFlags};

fn post_send(qp: &QueuePair, mr: &MemoryRegion, remote_addr: u64, rkey: u32)
    -> Result<(), Box<dyn std::error::Error>>
{
    let wr = SendWorkRequest::rdma_write()
        .local_addr(mr.addr())
        .length(mr.length())
        .lkey(mr.lkey())
        .remote_addr(remote_addr)
        .rkey(rkey)
        .send_flags(SendFlags::SIGNALED)
        .build();

    qp.post_send(&wr)?;

    Ok(())
}
```

### Poll Completion Queue
```rust
use sideway::verbs::WorkCompletion;

fn poll_cq(cq: &CompletionQueue) -> Result<Vec<WorkCompletion>, Box<dyn std::error::Error>> {
    let mut completions = vec![WorkCompletion::default(); 16];
    let n = cq.poll(&mut completions)?;

    completions.truncate(n);
    Ok(completions)
}
```

## Examples

### Run Examples from Repo
```bash
git clone https://github.com/RDMA-Rust/sideway.git
cd sideway

# List devices
cargo run --example list_devices

# Run ping-pong test
cargo run --example pingpong -- --server
cargo run --example pingpong -- --client <server_ip>
```

## Performance

Based on November 2025 benchmarks:
- Saturated 400 Gbps ConnectX-7 NICs
- Latency comparable to C implementations
- Zero-copy operations

## Use Cases

**Recommended for:**
- RDMA monitoring and orchestration tools
- Custom RDMA applications in Rust
- Test harnesses and benchmarks
- Cloud-native RDMA tooling

**Not recommended for:**
- Primary data plane (use C/DPDK for maximum performance)
- Legacy system integration
- Environments without Rust toolchain

## Integration with vLLM/NCCL

Sideway is not a replacement for NCCL. It's useful for:
- Building custom monitoring agents
- RDMA connection management tools
- Performance debugging utilities

For AI workloads, continue using NCCL with hardware RoCE.

## Building from Source

```bash
git clone https://github.com/RDMA-Rust/sideway.git
cd sideway

# Build
cargo build --release

# Run tests
cargo test

# Build documentation
cargo doc --open
```

## References

- GitHub: https://github.com/RDMA-Rust/sideway
- Crates.io: https://crates.io/crates/sideway
- 400 Gbps benchmark discussion: Reddit r/rust
