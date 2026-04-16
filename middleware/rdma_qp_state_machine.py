"""
RDMA queue-pair state machine with retry and verification.

Hardened replacement for the inline QP code that used to live in
`roce_transport.py`:

- RESET -> INIT -> RTR -> RTS transitions, each wrapped in a retry
  loop with exponential backoff. Transient `PyverbsError` / `OSError`
  is treated as retryable.
- RTR embeds the destination GID directly via `ah_attr.grh.dgid` and
  sets `sgid_index` from the local GID index. No `ibv_create_ah`
  allocation, no ARP dependency — this is what makes the bootstrap
  work on direct-connect RoCE without a managed switch.
- `verify_rts()` queries the QP state after the final transition and
  raises if the hardware did not actually reach RTS.
- `close()` forces a RESET transition before teardown to avoid the
  `rdma_rxe` zombie state the thesis notes in Update 4 section 9.5.

pyverbs is imported lazily so handshake-only tests can run on CI
nodes without rdma-core installed.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from .rdma_bootstrap import QpInfo


class QueuePairError(RuntimeError):
    """Raised when QP state transitions fail after all retries."""


class QueuePair:
    """Thin wrapper around `pyverbs.qp.QP` with retry + state verification.

    Usage:

        qp = QueuePair(pd, cq, cap, port=1, gid_index=gid_index)
        qp.to_init()
        qp.to_rtr(remote_qp_info)
        qp.to_rts(local_psn=0)
        qp.verify_rts()
        ...
        qp.close()
    """

    def __init__(self, pd: Any, cq: Any, cap: Any, *,
                 port: int = 1, gid_index: int = 0,
                 max_retries: int = 5,
                 base_delay: float = 0.010) -> None:
        # Lazy import so the module is usable without pyverbs (e.g. in
        # handshake-only tests on CI nodes without rdma-core).
        import pyverbs.enums as e
        import pyverbs.qp as qp_mod
        self._e = e
        self._qp_mod = qp_mod

        self._pd = pd
        self._cq = cq
        self._port = port
        self._gid_index = gid_index
        self._max_retries = max_retries
        self._base_delay = base_delay

        init_attr = qp_mod.QPInitAttr(
            qp_type=e.IBV_QPT_RC,
            scq=cq,
            rcq=cq,
            cap=cap,
        )
        self._qp = qp_mod.QP(pd, init_attr)

    @property
    def qp(self) -> Any:
        return self._qp

    @property
    def qp_num(self) -> int:
        return self._qp.qp_num

    def _retry(self, name: str, fn, *args, **kwargs) -> None:
        last_err: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                fn(*args, **kwargs)
                return
            except Exception as exc:  # pyverbs raises its own errors
                last_err = exc
                # Exponential backoff: 10, 20, 40, 80, 160 ms
                time.sleep(self._base_delay * (2 ** attempt))
        raise QueuePairError(
            f"{name} failed after {self._max_retries} attempts: {last_err}"
        )

    def _new_attr(self) -> Any:
        """Construct a pyverbs QPAttr across versions.

        Older pyverbs accepted many fields as constructor kwargs; newer
        versions reject them. Building the object empty and setting
        fields as attributes works on both.
        """
        return self._qp_mod.QPAttr()

    def to_init(self, access_flags: Optional[int] = None) -> "QueuePair":
        e = self._e
        if access_flags is None:
            access_flags = (e.IBV_ACCESS_LOCAL_WRITE
                            | e.IBV_ACCESS_REMOTE_WRITE
                            | e.IBV_ACCESS_REMOTE_READ)
        attr = self._new_attr()
        attr.qp_state = e.IBV_QPS_INIT
        attr.pkey_index = 0
        attr.port_num = self._port
        attr.qp_access_flags = access_flags
        self._retry("to_init", self._qp.to_init, attr)
        return self

    @staticmethod
    def _bytes_to_pyverbs_gid(raw: bytes):
        """Wrap 16 raw GID bytes in a pyverbs GID object.

        pyverbs's ``GID`` wants a colon-separated IPv6 string; we
        reformat our 16-byte network representation into the right
        shape.
        """
        import pyverbs.addr as addr
        if len(raw) != 16:
            raise ValueError(f"GID must be 16 bytes, got {len(raw)}")
        hexs = raw.hex()
        parts = [hexs[i:i + 4] for i in range(0, 32, 4)]
        return addr.GID(":".join(parts))

    def to_rtr(self, remote: QpInfo,
               path_mtu: Optional[int] = None) -> "QueuePair":
        """Transition to Ready-To-Receive.

        Embeds ``remote.gid`` directly in the AHAttr (dgid / sgid_index /
        hop_limit). pyverbs's ``AHAttr`` exposes the GRH fields as
        first-class attributes rather than a ``.grh`` sub-object.
        """
        e = self._e
        if path_mtu is None:
            path_mtu = e.IBV_MTU_1024

        attr = self._new_attr()
        attr.qp_state = e.IBV_QPS_RTR
        attr.path_mtu = path_mtu
        attr.dest_qp_num = remote.qpn
        attr.rq_psn = remote.psn
        attr.max_dest_rd_atomic = 1
        attr.min_rnr_timer = 12
        attr.ah_attr.port_num = self._port
        attr.ah_attr.sl = 0
        attr.ah_attr.src_path_bits = 0
        # GRH fields — passing the destination GID directly bypasses the
        # ARP/AH path entirely. RoCE requires is_global = 1.
        attr.ah_attr.is_global = 1
        attr.ah_attr.dgid = self._bytes_to_pyverbs_gid(remote.gid)
        attr.ah_attr.sgid_index = self._gid_index
        attr.ah_attr.hop_limit = 1
        attr.ah_attr.flow_label = 0
        attr.ah_attr.traffic_class = 0

        self._retry("to_rtr", self._qp.to_rtr, attr)
        return self

    def to_rts(self, local_psn: int = 0) -> "QueuePair":
        e = self._e
        attr = self._new_attr()
        attr.qp_state = e.IBV_QPS_RTS
        attr.sq_psn = local_psn
        attr.timeout = 14
        attr.retry_cnt = 7
        attr.rnr_retry = 7
        attr.max_rd_atomic = 1
        self._retry("to_rts", self._qp.to_rts, attr)
        return self

    def verify_rts(self) -> None:
        """Query the QP state and raise if it is not RTS."""
        e = self._e
        state = self._query_state()
        if state != e.IBV_QPS_RTS:
            raise QueuePairError(
                f"QP failed to reach RTS: state={state}, expected={e.IBV_QPS_RTS}"
            )

    def _query_state(self) -> int:
        # pyverbs exposes query via `.query(attr_mask)`; the exact mask
        # varies by version, so we try the common ones.
        e = self._e
        try:
            attr, _ = self._qp.query(e.IBV_QP_STATE)
            return attr.qp_state
        except Exception:
            # Fallback: some pyverbs versions expose `.qp_state` directly
            return getattr(self._qp, "qp_state", -1)

    def reset(self) -> None:
        """Force transition to RESET state to avoid zombie resources."""
        try:
            e = self._e
            attr = self._new_attr()
            attr.qp_state = e.IBV_QPS_RESET
            self._qp.modify(attr, e.IBV_QP_STATE)
        except Exception:
            # Reset failures during teardown are non-fatal; the caller
            # still needs to close() the underlying QP object.
            pass

    def close(self) -> None:
        try:
            self.reset()
        finally:
            try:
                self._qp.close()
            except Exception:
                pass
