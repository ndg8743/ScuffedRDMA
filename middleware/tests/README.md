# tests

Pytest suite for the middleware layer. Small on purpose, mostly focused
on the libmesh-rdma port since that's where wire-format and state-machine
bugs bite hardest.

## Files

- `test_rdma_bootstrap.py` — covers `rdma_bootstrap.py`,
  `rdma_gid_discovery.py`, and `rdma_qp_state_machine.py`. Includes:
  - `QpInfo` pack/unpack round-trip plus the 64-byte wire-size invariant.
  - Loopback TCP handshake with a sender thread and an accepter thread.
  - IPv4-mapped GID helper tests.
  - Regression tests for the four security findings fixed alongside
    the port (see commit `541fd1a`).

  The `QueuePair` state-machine test needs a real RDMA device and skips
  automatically when `rxe0` is absent.

## Running

```
cd /home/nathan/ScuffedRDMA
pytest middleware/tests/
```

## Stale

None. The test file pairs with the modules it was added beside.
Coverage of `rdma_tensor_cache/` and the other subpackages lives
elsewhere in the repo (outside `middleware/tests/`) or is not yet
written.
