# middleware

Adaptive transport layer for distributed LLM inference. Picks between TCP,
Soft-RoCE, and Tesla TTPoe at runtime and exposes a single `send`/`recv`
interface regardless of backend.

## Layout

- `transport_base.py` — abstract `TransportBase` and `TransportMetrics`
  that every backend implements.
- `tcp_transport.py` — Berkeley-socket baseline. Used for comparison and
  as a fallback when RDMA is unavailable.
- `roce_transport.py` — Soft-RoCE (rxe0) over rdma-core. Delegates the
  bootstrap and QP state machine to the three libmesh-rdma ports below.
- `ttpoe_transport.py` — Tesla Dojo's TTPoe via `modttpoe.ko` over a
  character device. Sub-microsecond latency when the kernel modules load.
- `selector.py` — `TransportSelector` factory. Picks a backend from the
  `SCUFFED_TRANSPORT` env var, explicit arg, or availability probing.
- `nccl_config.py` — emits the NCCL env vars (`NCCL_IB_HCA`,
  `NCCL_SOCKET_IFNAME`, etc.) that match the selected transport.

## libmesh-rdma port

Three modules port the RDMA bootstrap from `autoscriptlabs/libmesh-rdma`.
They replace the earlier JSON handshake and the inline QP code that used
to live in `roce_transport.py`:

- `rdma_bootstrap.py` — 64-byte fixed-size TCP handshake with network
  byte order and struct packing. No length field for a crafted peer to
  abuse.
- `rdma_gid_discovery.py` — finds the right IPv4-mapped GID index for
  RoCEv2 instead of hardcoding `gid_index = 0`. Needed for direct-connect
  setups without a managed switch.
- `rdma_qp_state_machine.py` — RESET to INIT to RTR to RTS transitions
  wrapped in retries with exponential backoff. Forces RESET on close to
  avoid the `rdma_rxe` zombie state described in thesis Update 4 section
  9.5.

## Subpackages

- `rdma_tensor_cache/` — the main libscuffedrdma code. Dual QP pools, WFA
  classifier, PMP bang-bang controller, KV cache connector. See
  [rdma_tensor_cache/README.md](rdma_tensor_cache/README.md).
- `tests/` — pytest suite focused on the libmesh-rdma port. See
  [tests/README.md](tests/README.md).

## Usage

```python
from middleware import TransportSelector

ts = TransportSelector('roce')
transport = ts.get_transport()
transport.connect(host, port)
transport.send(data)
response = transport.recv(size)
```
