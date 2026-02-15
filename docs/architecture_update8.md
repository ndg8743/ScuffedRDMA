# Update 8: RDMA Tensor Cache Architecture

## 1. System Overview

The RDMA Tensor Cache extends the tensor database (a Rust distributed tensor runtime, 20 workspace crates) with a new `tensor_rdma` crate that provides precision-managed, prefetch-aware tensor transfer between heterogeneous GPU nodes connected via Mellanox ConnectX-4 100GbE adapters.

### 1.1 Physical Topology

```
+---------------------------------------+      100GbE ConnectX-4       +---------------------------------------+
|  TOWER 1 (Windows)                    |  <========================> |  TOWER 2 (Linux / Proxmox)            |
|                                       |     (TCP/gRPC for now,      |                                       |
|  RTX 5070 Ti  16GB VRAM               |      SoftRoCE target)       |  2x Tesla V100  32GB VRAM each        |
|  - BF16 native compute                |                             |  - FP16 native compute                |
|  - No GPUDirect RDMA (consumer)       |                             |  - GPUDirect RDMA (datacenter)        |
|  - Coordinator role                   |                             |  - Tensor database server runs here   |
|                                       |                             |  - IP: 192.168.2.111                  |
|  Mellanox ConnectX-4 100GbE           |                             |  Mellanox ConnectX-4 100GbE           |
+---------------------------------------+                             +---------------------------------------+
```

### 1.2 Inference Path

The inference path prioritizes latency. Tensors flow from the tensor database store on Tower 2 to whichever GPU is running the active model layers. The prefetch engine hides transfer latency by predicting upcoming layer accesses.

```
                          INFERENCE DATA FLOW
                          ===================

  Client Request
       |
       v
  +--------------------+
  | Tower 1 (Windows)  |       1. Coordinator receives prompt
  | Coordinator        |       2. Checks local tensor_rdma cache
  | tensor_rdma cache  |       3. On miss: fetch from Tower 2
  +--------------------+
       |                  cache miss
       |  RdmaTransport::rdma_read()
       |  (TCP fallback on Windows)
       v
  +--------------------+
  | Tower 2 (Linux)    |       4. Tensor database server looks up tensor
  | Tensor DB Server   |       5. PrecisionRouter selects wire format:
  | tensor_store       |          V100 target -> FP16
  | 2x V100 32GB      |          5070 Ti target -> BF16
  +--------------------+       6. Encode + send via transport
       |
       v
  +--------------------+
  | PrecisionRouter    |       7. Decode from wire format
  | precision.rs       |       8. Convert to device-native precision
  +--------------------+       9. Stochastic rounding if FP32->FP16
       |
       v
  +--------------------+
  | PrefetchEngine     |       10. Record access in history ring
  | prefetch.rs        |       11. Detect pattern (Sequential/Strided/LayerSweep)
  +--------------------+       12. Issue prefetch for next N layers
       |
       v
  GPU Compute (inference step)
```

### 1.3 Fine-Tuning Path

Fine-tuning adds gradient flow in the reverse direction. Master weights live in FP32 on Tower 2. Gradients computed on either tower are reduced and applied at FP32 precision, then the updated weights propagate back.

```
                        FINE-TUNING DATA FLOW
                        =====================

  +--------------------+       +--------------------+
  | Tower 1            |       | Tower 2            |
  | 5070 Ti (BF16)     |       | V100 x2 (FP16)    |
  +--------------------+       +--------------------+
       |  forward pass              |  forward pass
       v                            v
  local gradients (BF16)       local gradients (FP16)
       |                            |
       |  stochastic_round_batch    |  stochastic_round_batch
       |  rounding.rs               |  rounding.rs
       v                            v
  gradients in wire format     gradients in wire format
  (FP16 common denominator)    (FP16 native)
       \                          /
        \  RdmaTransport         /
         \  rdma_write()        /
          \                    /
           v                  v
       +----------------------------+
       | Tower 2: Tensor DB Server  |
       | FP32 master weight update  |
       | delta_replication.rs       |   <-- delta-compressed
       | broadcasts updated weights |       replication to
       +----------------------------+       followers
                |
                v
       weights re-distributed
       to both towers via prefetch
```

### 1.4 Crate Dependency Context

`tensor_rdma` sits alongside the existing distributed layer, not inside it:

```
  tensor_store ----+----> tensor_chain (consensus, Raft, 2PC, delta replication)
                   |
  tensor_compress -+----> tensor_rdma  (RDMA cache, precision, prefetch, transport)
                          |
                          +--> precision.rs      PrecisionFormat, PrecisionRouter, DeviceCapability
                          +--> rounding.rs       stochastic_round_f32_to_{f16,bf16}
                          +--> prefetch.rs       PrefetchEngine, AccessPattern detection
                          +--> transport.rs      RdmaTransport trait, MemoryTransport, TcpFallbackTransport
                          +--> rdma_cache.rs     RdmaTensorCache<T: RdmaTransport>
                          +--> config.rs         RdmaCacheConfig, TransportConfig, PrefetchStrategy
                          +--> error.rs          RdmaCacheError
```

---

## 2. Thesis Concept to Tensor Database Module Mapping

| Thesis Concept | Tensor Database Module | Status | Gap |
|---|---|---|---|
| Precision management | `tensor_rdma/precision.rs` | Implemented | MXFP4 format defined (4-bit, 2-bit exponent, 1-bit mantissa); encode/decode stubs present. No GPU kernel for MXFP4 compute. |
| Stochastic rounding | `tensor_rdma/rounding.rs` | Implemented | CPU-side `half` crate implementation. Unbiased E[round(x)] = x property verified. GPU kernel version needed for in-pipeline rounding. |
| Prefetch engine | `tensor_rdma/prefetch.rs` | Implemented | Pattern detection (Sequential, Strided, LayerSweep, Random) with ring buffer history. Generates prefetch key lists. Not yet wired to async RDMA reads. |
| RDMA transport | `tensor_rdma/transport.rs` | Memory + TCP stubs | `RdmaTransport` trait with `register_buffer`, `rdma_write`, `rdma_read`. `MemoryTransport` for tests, `TcpFallbackTransport` for Windows. `TransportConfig::SoftRoce` variant exists but no FFI backend. Need rdma-core FFI or pyverbs bridge on Tower 2. |
| KV cache | `tensor_rdma/rdma_cache.rs` | Implemented | `RdmaTensorCache<T>` wraps `TensorStore` + `RdmaTransport` + `PrecisionRouter` + `PrefetchEngine`. Local DashMap hot cache with precision-aware remote fetch. Missing vLLM `MooncakeConnector`/`NixlConnector` interface. |
| Delta compression | `tensor_chain/delta_replication.rs` | Existing | 4-6x bandwidth reduction via archetype-based sparse deltas. Fully functional within tensor_chain. Wire format not yet integrated with tensor_rdma transport. |
| Device capability | `tensor_rdma/precision.rs` | Implemented | `DeviceCapability::v100_32gb()` and `DeviceCapability::rtx5070ti()` factory methods with VRAM, supported formats, GPUDirect flag. |
| Config presets | `tensor_rdma/config.rs` | Implemented | `v100_preset()`, `rtx5070ti_preset()`, `heterogeneous_preset()`. Wire precision, stochastic rounding, prefetch depth all configurable. |

---

## 3. Hardware-Specific Considerations

### 3.1 Tower 2 (Linux / Proxmox) -- Primary Compute Node

Tower 2 is the RDMA-capable node and runs the tensor database server process.

**GPU: 2x Tesla V100 32GB (SXM2 or PCIe)**
- Datacenter-class GPU with full NVIDIA driver support for GPUDirect RDMA.
- `nvidia-peermem` kernel module enables direct NIC-to-GPU DMA, bypassing host memory staging.
- FP16 Tensor Cores (no BF16 on V100). Native compute precision is FP16.
- 32GB HBM2 per card = 64GB total VRAM across both GPUs.
- NVLink between the two V100s for fast intra-node P2P (if SXM2 form factor).

**Network: Mellanox ConnectX-4 100GbE**
- Full rdma-core support on Linux. `ibv_devinfo` should enumerate the device.
- SoftRoCEv2 (rxe) available immediately for development; hardware RoCE once PFC/ECN is configured on the switch.
- Port 4791 (RoCEv2 standard).

**Software stack required:**
```
# rdma-core packages
apt install rdma-core ibverbs-utils libibverbs-dev librdmacm-dev

# GPUDirect RDMA
apt install nvidia-peermem
modprobe nvidia-peermem

# Low-latency GPU memory copy
git clone https://github.com/NVIDIA/gdrcopy && cd gdrcopy && make && make install

# Verify RDMA device
ibv_devinfo
rdma link show
```

**Tensor database server deployment:**
- `database_server` (gRPC via tonic) runs on Tower 2.
- tensor_rdma transport binds on `0.0.0.0:4791` for RDMA connections.
- tensor_chain Raft node also runs here for consensus.
- Both V100s registered as compute devices in `PrecisionRouter`.

### 3.2 Tower 1 (Windows) -- Coordinator Node

Tower 1 orchestrates inference requests and contributes BF16 compute.

**GPU: RTX 5070 Ti 16GB**
- Consumer Blackwell GPU. Native BF16 Tensor Core support (8-bit exponent, 7-bit mantissa).
- No GPUDirect RDMA. Windows NVIDIA drivers do not expose `nvidia-peermem`. All tensor transfers go through host memory.
- `DeviceCapability::rtx5070ti()` sets `gpu_direct_rdma: false`.
- 16GB GDDR7 VRAM.

**Network: Mellanox ConnectX-4 100GbE**
- Windows has no rdma-core. No kernel verbs API. No SoftRoCE.
- `TcpFallbackTransport` is the only viable transport on this node.
- Future: gRPC streaming as an alternative to raw TCP, leveraging `database_server`'s existing tonic infrastructure.

**Role in the cluster:**
- Coordinator: receives client requests, dispatches to Tower 2 via TCP/gRPC.
- BF16 compute contributor for layers that benefit from BF16 dynamic range.
- Runs `RdmaTensorCache<TcpFallbackTransport>` with `rtx5070ti_preset()`.
- Stochastic rounding disabled (BF16 has sufficient dynamic range for most workloads).

### 3.3 Precision Negotiation Between Towers

The `PrecisionRouter` resolves the FP16/BF16 mismatch:

```
  Tower 1 (5070 Ti)                    Tower 2 (V100)
  native: BF16                         native: FP16
  supported: [FP16, BF16, FP32]        supported: [FP16, FP32]
       |                                    |
       +-------> common_format() -----------+
                 returns FP16
                 (intersection of supported formats,
                  smallest element size wins)

  Wire format for Tower1->Tower2: FP16  (5070 Ti converts BF16 -> FP16 before send)
  Wire format for Tower2->Tower1: BF16  (optimal_wire_format picks BF16 for 5070 Ti target)
  Master weights on Tower 2: FP32       (full precision for gradient accumulation)
```

---

## 4. NVIDIA Open-Source Tool Integration Map

All tools below are open-source and target Tower 2 (Linux). Tower 1 has no access to these tools directly.

| Tool | Purpose | Transport Modes | Relevance to Tensor Database |
|---|---|---|---|
| **NCCL** | Collective communication (AllReduce, AllGather, Broadcast) | IB, RoCE, TCP, shared memory, NVLink | Multi-V100 collectives on Tower 2. Not used cross-tower (Windows incompatible). |
| **UCX** | Point-to-point transport abstraction | RC, DC, UD, TCP, shared memory, CUDA | Candidate for `tensor_rdma` transport backend. Handles QP management, memory registration, and transport selection automatically. |
| **UCC** | Topology-aware collective algorithms over UCX | Inherits UCX transports | Higher-level collective API. Could replace manual NCCL configuration for V100 pair. |
| **nvidia-peermem** | GPUDirect RDMA kernel module | Kernel DMA | Required for NIC-to-GPU zero-copy on V100. `modprobe nvidia-peermem` on Tower 2. |
| **gdrcopy** | Low-latency GPU memory copy (user-space) | CPU-GPU via BAR1 mapping | Reduces small-tensor transfer latency. 2-5us for <4KB vs. 10-20us via `cudaMemcpy`. |
| **NIXL** | vLLM KV cache transfer | NVLink > RDMA > TCP (auto-selection) | Direct path for KV cache disaggregation. Matches `rdma_cache.rs` use case. Implements `NixlConnector` interface that `tensor_rdma` needs to bridge. |
| **HPC-X v2.15** | NVIDIA HPC toolkit (bundles UCX, UCC, NCCL, SHARP, HCOLL) | All of the above | Single install for Tower 2. Provides tuned UCX and NCCL builds with ConnectX-4 firmware awareness. |

### 4.1 Integration Layering

```
  +---------------------------------------------------------+
  | Tensor database tensor_rdma                              |
  |   RdmaTransport trait                                   |
  +---------------------------------------------------------+
       |               |                    |
       v               v                    v
  MemoryTransport  TcpFallback          SoftRoceTransport
  (tests)          (Tower 1 / Windows)  (Tower 2 / Linux)
                                             |
                                             v
                                        +---------+
                                        | rdma-core|  (ibv_* verbs API)
                                        +---------+
                                             |
                         +-------------------+-------------------+
                         v                   v                   v
                    nvidia-peermem      gdrcopy              UCX (optional)
                    (GPU RDMA)          (low-latency)        (transport mgmt)
                         |
                         v
                    ConnectX-4 firmware
                    (mlx5 driver)
```

### 4.2 NIXL Integration for vLLM KV Cache

NIXL (NVIDIA Inference eXchange Library) provides the transport-agnostic KV cache transfer that vLLM's disaggregated prefill/decode architecture requires. The connection to `tensor_rdma`:

```
  vLLM Engine (Python)
       |
       | NixlConnector interface
       v
  +-----------------------+
  | NIXL Agent            |     <-- manages memory descriptors
  | xfer_send / xfer_recv |     <-- async transfer API
  +-----------------------+
       |
       | (maps to one of:)
       v
  NVLink path  |  RDMA path  |  TCP path
               |              |
               v              v
          rdma-core       TCP socket
               |
               v
  Tensor database tensor_rdma
  (registers NIXL buffers as RdmaTransport buffers)
```

---

## 5. SAE Feature Steering as Fine-Tuning Alternative

Sparse Autoencoder (SAE) feature steering offers an alternative to gradient-based fine-tuning that maps naturally onto the tensor database's existing sparse vector infrastructure and RDMA transfer.

### 5.1 Why SAE Features Fit This Architecture

Traditional fine-tuning requires:
- Full backward pass (FP16/FP32 gradient computation)
- Gradient accumulation across nodes (AllReduce)
- Master weight update in FP32
- Weight re-distribution

SAE feature steering requires:
- Forward pass to extract activations at target layer
- Sparse feature vector lookup (pre-computed SAE decoder)
- Feature clamping: add/subtract activation directions
- No gradients, no backward pass, no weight modification

### 5.2 SparseVector for SAE Features

The `SparseVector` type (defined in `tensor_store/src/sparse_vector.rs`) stores only non-zero indices and values:

```
  Dense activation vector (4096d):      16,384 bytes  (4096 x 4 bytes)
  SAE feature (99% sparse):                ~80 bytes  (indices + values for ~20 active features)
  Compression ratio:                         ~200x

  Tensor database SparseVector encoding:
    positions: [42, 189, 512, 1024, 3891]
    values:    [0.73, -0.41, 0.22, 0.15, -0.88]
    dimension: 4096
```

With 51x compression at typical SAE sparsity levels, a full feature dictionary transfer is <1KB per feature. Compare this to transferring full model weights (millions of parameters at 2-4 bytes each).

### 5.3 RDMA Transfer of Sparse Features

```
  +--------------------+                    +--------------------+
  | Tower 1            |                    | Tower 2            |
  | Feature store      |                    | V100 inference     |
  | (sparse vectors)   |                    |                    |
  +--------------------+                    +--------------------+
       |                                         ^
       | 1. Client selects features              | 4. Modified activations
       |    to steer (e.g., "increase            |    fed to next layer
       |    code quality", "reduce               |
       |    verbosity")                          |
       v                                         |
  +--------------------+                    +--------------------+
  | SparseVector       |  -- RDMA/TCP -->   | Feature clamping   |
  | ~80 bytes per      |  2. Transfer       | 3. activation +=   |
  | feature direction  |     sparse vecs    |    alpha * feature |
  +--------------------+                    +--------------------+

  Total transfer for 10 steering features:  ~800 bytes
  vs. fine-tuned weight delta:              ~10-100 MB
```

### 5.4 Advantages Over Gradient-Based Fine-Tuning

1. **Bypasses FP16/BF16 precision issues entirely.** Feature clamping operates on activations (which are already in the device's native precision). No cross-precision gradient accumulation needed.

2. **No stochastic rounding required.** The rounding module in `tensor_rdma/rounding.rs` is irrelevant for SAE steering -- there is no lossy precision conversion in the feature application path.

3. **Sub-millisecond transfer.** At ~80 bytes per feature, even TCP fallback on Tower 1 transfers a full steering configuration in under 1ms. RDMA would be <10us.

4. **Composable and reversible.** Feature directions can be added, removed, or scaled at inference time without touching model weights. No checkpoint needed.

5. **Feature clamping modifies model behavior without gradients.** The intervention is `activation[layer] += alpha * sparse_feature_direction`. This is a vector addition, not a parameter update.

---

## 6. Gap Analysis

### 6.1 rdma-core FFI (Rust)

**Current state:** `TransportConfig::SoftRoce { device, gid_index, port }` variant exists in config. No actual FFI binding.

**Required work:**
- Safe Rust wrapper around `libibverbs` (`ibv_open_device`, `ibv_alloc_pd`, `ibv_reg_mr`, `ibv_create_qp`, `ibv_post_send`, `ibv_post_recv`, `ibv_poll_cq`).
- Memory region registration with `IBV_ACCESS_LOCAL_WRITE | IBV_ACCESS_REMOTE_WRITE | IBV_ACCESS_REMOTE_READ`.
- Queue pair state machine: RESET -> INIT -> RTR -> RTS.
- Completion queue polling (either busy-poll or event-driven via `ibv_get_cq_event`).
- Alternative: use `rdma-sys` crate (raw bindings) or `async-rdma` crate as starting point.

**Scope:** ~500-800 lines of unsafe Rust in a `ffi/` submodule, gated behind `#[cfg(target_os = "linux")]`.

### 6.2 Windows RDMA

**Current state:** Not available. Windows has no rdma-core equivalent for userspace verbs.

**Decision:** TCP/gRPC fallback is the permanent solution for Tower 1.

The `TcpFallbackTransport` currently stubs `rdma_write` (records metrics, returns Ok) and `rdma_read` (returns zero-filled buffer). These need to be completed with actual TCP socket communication:
- Connect to Tower 2's `bind_addr` on startup.
- Frame protocol: `[u32 msg_type][u64 buffer_id][u64 offset][u32 len][payload]`.
- Reuse `tensor_chain/tcp/framing.rs` length-delimited codec pattern.

### 6.3 vLLM Connector Interface

**Current state:** `RdmaTensorCache` has get/store/prefetch operations. vLLM expects a `MooncakeConnector` or `NixlConnector` interface (Python).

**Required work:**
- Python shim (via `tensor-db-py` or standalone) that exposes `tensor_rdma` operations as a vLLM-compatible connector.
- Must implement: `register_kv_caches(kv_caches)`, `send_recv_kv_caches_pynixl(...)` or equivalent.
- NIXL agent initialization with the tensor database's transport as the underlying mechanism.
- KV cache block layout must match vLLM's `PagedAttention` block tables.

### 6.4 GPUDirect RDMA Setup on Tower 2

**Current state:** Not configured.

**Required steps:**
1. Install NVIDIA driver >= 525 with peermem support.
2. `modprobe nvidia-peermem` and verify: `cat /sys/kernel/mm/memory_hotplug/online_type`.
3. Install gdrcopy for low-latency small transfers: `insmod gdrdrv.ko`.
4. Verify with `gdrcopy_sanity` test.
5. Pin GPU memory with `cuMemAlloc` (not `cudaMallocAsync` -- see thesis Issue 1) and register with `ibv_reg_mr`.
6. Verify end-to-end: `ib_write_bw --use_cuda=0` between ConnectX-4 and V100.

### 6.5 Delta Compression Wire Integration

**Current state:** `tensor_chain/delta_replication.rs` implements archetype-based sparse delta encoding (4-6x compression). This exists independently from `tensor_rdma`.

**Required work:**
- Share `ArchetypeRegistry` between `tensor_chain` and `tensor_rdma`.
- Add `enable_delta_compression` flag to `RdmaCacheConfig` (already present, default true).
- Before RDMA write: encode tensor as `(archetype_id, sparse_delta)`.
- After RDMA read: decode by adding archetype + delta.
- Wire format: `[u32 archetype_id][u32 nnz][u32[] indices][f16[] values][blake2b checksum]`.

### 6.6 Summary Table

| Gap | Blocking? | Effort | Owner |
|---|---|---|---|
| rdma-core FFI (Rust) | Yes -- no real RDMA without it | ~2 weeks | Tower 2 Linux dev |
| Windows RDMA | No -- TCP fallback is acceptable | N/A | Permanent fallback |
| TcpFallbackTransport completion | Yes -- stubs return dummy data | ~3 days | Cross-platform |
| vLLM connector | No -- inference works without vLLM | ~1 week | Python shim |
| GPUDirect RDMA on Tower 2 | Yes -- needed for NIC-to-GPU path | ~2 days (config) | Tower 2 admin |
| Delta compression wire format | No -- works without it (just slower) | ~3 days | Shared module |

---

## 7. Future Path

### 7.1 Transport Evolution

```
  Phase 1 (current)        Phase 2 (next)           Phase 3 (target)
  =================        ==============           ================

  MemoryTransport          SoftRoCEv2               Hardware RoCE
  (unit tests)             (rxe kernel module)      (ConnectX-4 native)
                           - No special switch       - Requires PFC + ECN
  TcpFallbackTransport       config needed             on switch
  (Tower 1 / Windows)     - ~190us latency          - ~2us latency
                           - Full ibverbs API        - Line-rate 100GbE
                           - GPUDirect via           - GPUDirect RDMA
                             nvidia-peermem            at full bandwidth

                                    |
                                    v
                              Phase 4 (future)
                              ================
                              UEC 1.0
                              (Ultra Ethernet Consortium)
                              - Ordered reliable delivery
                              - Multipath at transport layer
                              - No PFC required
                              - Spray-based load balancing
                              - Replaces RoCE long-term
```

### 7.2 SoftRoCEv2 as Development Bridge

SoftRoCEv2 (`rxe` module) provides the full RDMA verbs API in software, implemented in the Linux kernel. It runs over any Ethernet interface -- including the 100GbE ConnectX-4 on Tower 2.

Key properties:
- Same `ibv_*` API as hardware RDMA. Code written for SoftRoCE works unchanged on hardware RoCE.
- Latency: ~150-200us (kernel processing overhead vs. ~2us for hardware offload).
- Throughput: limited by CPU, not NIC. Expect ~40-60 Gbps on modern Xeon, vs. 100 Gbps wire rate.
- Sufficient for validating the entire tensor_rdma pipeline before investing in switch configuration.

Setup on Tower 2:
```bash
modprobe rdma_rxe
rdma link add rxe0 type rxe netdev eth0
ibv_devinfo   # should show rxe0
```

### 7.3 Hardware RoCE Requirements

Moving from SoftRoCE to hardware RoCE on ConnectX-4 requires:

1. **Priority Flow Control (PFC)** on the switch connecting Tower 1 and Tower 2. Without PFC, RoCE drops packets under congestion and relies on Go-Back-N retransmission (the root cause of thesis Issue 5: 90-second timeout crashes).
2. **ECN (Explicit Congestion Notification)** marking at the switch. ConnectX-4 firmware supports DCQCN (Data Center QoS Congestion Notification) which reacts to ECN marks.
3. **DSCP-based QoS** to separate RDMA traffic (priority 3) from other traffic.
4. Firmware update: `mlxfwmanager --update` to latest ConnectX-4 firmware.

### 7.4 UEC 1.0 Long-Term Target

Ultra Ethernet Consortium (UEC) 1.0 specification addresses the fundamental problems with RoCE:
- **Ordered reliable delivery** without PFC (eliminates head-of-line blocking).
- **Packet spraying** across multiple paths (load balancing built into transport).
- **Multipath transport** (multiple network paths for a single connection).
- **No lossless fabric requirement** (works on standard Ethernet switches).

UEC 1.0 silicon is expected from Broadcom, Intel, and Cisco in the 2026-2027 timeframe. The `RdmaTransport` trait in `tensor_rdma/transport.rs` is designed to be transport-agnostic: a future `UecTransport` implementation would slot in without changes to the cache, precision, or prefetch layers.
