# middleware

Adaptive transport layer for disaggregated LLM inference. Picks between TCP, SoftRoCE, and Tesla TTPoe at runtime and exposes one `send` / `recv` interface regardless of backend.

## Layout

### Transports
- `transport_base.py` — abstract `TransportBase` and `TransportMetrics` that every backend implements.
- `tcp_transport.py` — Berkeley-socket baseline. Fallback when RDMA is unavailable.
- `roce_transport.py` — SoftRoCE (`rxe0`) via rdma-core. Delegates bootstrap and QP state to the primitives below.
- `ttpoe_transport.py` — Tesla Dojo TTPoe via `modttpoe.ko` over a char device.
- `selector.py` — `TransportSelector` factory. Resolves backend from `SCUFFED_TRANSPORT`, explicit arg, or availability probing.
- `nccl_config.py` — emits the NCCL env vars (`NCCL_IB_HCA`, `NCCL_SOCKET_IFNAME`, …) that match the selected transport.

### RDMA primitives
- `rdma_bootstrap.py` — fixed-size 64-byte `QpInfo` exchange over TCP. `send_handshake` / `accept_handshake` with retry. No length field, so crafted peers cannot drive unbounded allocations.
- `rdma_gid_discovery.py` — scans the port's GID table and picks the highest-index IPv4-mapped entry. Replaces the fragile `gid_index = 0` default.
- `rdma_qp_state_machine.py` — `QueuePair` class driving RESET → INIT → RTR → RTS with exponential-backoff retry and state-query verification. Embeds the destination GID directly in the AH attributes so the path works on direct-connect RoCE without a managed switch.

### Subpackages
- `rdma_tensor_cache/` — the core libscuffedrdma code (dual QP pool, WFA, PMP, scuffedQuant, vLLM KV connector). See [`rdma_tensor_cache/README.md`](rdma_tensor_cache/README.md).
- `tests/` — pytest suite. See [`tests/README.md`](tests/README.md).

## Usage

```python
from middleware import TransportSelector

ts = TransportSelector('roce')
transport = ts.get_transport()
transport.connect(host, port)
transport.send(data)
response = transport.recv(size)
```
