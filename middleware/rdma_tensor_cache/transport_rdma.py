"""
Real pyverbs/rdma-core transport backend.

Wraps ibv_reg_mr, ibv_post_send (RDMA Write), and ibv_post_recv
for zero-copy tensor transfers. Linux-only; gracefully degrades
on Windows or when pyverbs is not installed.
"""

import struct
import time
from typing import Any, Dict, Optional, Tuple

import numpy as np

_pyverbs_available = False
_pyverbs_modules: Dict[str, Any] = {}

try:
    import pyverbs.device as _pv_device
    import pyverbs.pd as _pv_pd
    import pyverbs.cq as _pv_cq
    import pyverbs.qp as _pv_qp
    import pyverbs.mr as _pv_mr
    import pyverbs.enums as _pv_enums
    import pyverbs.wr as _pv_wr

    _pyverbs_modules = {
        'device': _pv_device,
        'pd': _pv_pd,
        'cq': _pv_cq,
        'qp': _pv_qp,
        'mr': _pv_mr,
        'enums': _pv_enums,
        'wr': _pv_wr,
    }
    _pyverbs_available = True
except ImportError:
    pass


@np.errstate(over='ignore')
def _checksum(buf: bytes) -> int:
    """Fast 32-bit checksum for integrity verification."""
    arr = np.frombuffer(buf[:len(buf) - len(buf) % 4], dtype=np.uint32)
    return int(arr.sum()) & 0xFFFFFFFF


class RegisteredBuffer:
    """An RDMA-registered memory region backed by a numpy array."""

    def __init__(self, size: int, pd: Any, access_flags: int):
        self.array = np.zeros(size, dtype=np.uint8)
        self.mr = _pyverbs_modules['mr'].MR(pd, self.array, access_flags)

    @property
    def buf(self):
        return self.mr.buf

    @property
    def lkey(self) -> int:
        return self.mr.lkey

    @property
    def rkey(self) -> int:
        return self.mr.rkey

    def write(self, data: bytes, offset: int = 0) -> None:
        self.array[offset:offset + len(data)] = np.frombuffer(data, dtype=np.uint8)

    def read(self, length: int, offset: int = 0) -> bytes:
        return self.array[offset:offset + length].tobytes()

    def close(self) -> None:
        try:
            self.mr.close()
        except Exception:
            pass


class PyverbsTransport:
    """
    RDMA transport using pyverbs (rdma-core Python bindings).

    Provides register_buffer / rdma_write / rdma_read with the same
    API shape as TcpSimTransport for transparent backend swapping.
    """

    def __init__(self, device_name: str = "rxe0", ib_port: int = 1,
                 gid_index: int = 0):
        if not _pyverbs_available:
            raise ImportError(
                "pyverbs not available. Install rdma-core on Linux: "
                "apt install rdma-core python3-pyverbs"
            )

        self._device_name = device_name
        self._ib_port = ib_port
        self._gid_index = gid_index

        self._ctx: Any = None
        self._pd: Any = None
        self._cq: Any = None
        self._qp: Any = None
        self._buffers: Dict[str, RegisteredBuffer] = {}
        self._connected = False

        self._bytes_sent = 0
        self._bytes_recv = 0
        self._ops = 0

    @staticmethod
    def is_available() -> bool:
        return _pyverbs_available

    def open(self, cq_depth: int = 256) -> None:
        """Open device, allocate PD and CQ."""
        d = _pyverbs_modules['device']
        pd_mod = _pyverbs_modules['pd']
        cq_mod = _pyverbs_modules['cq']

        self._ctx = d.Context(name=self._device_name)
        self._pd = pd_mod.PD(self._ctx)
        self._cq = cq_mod.CQ(self._ctx, cq_depth)

    def create_qp(self, max_send_wr: int = 64, max_recv_wr: int = 64) -> Dict[str, Any]:
        """
        Create a queue pair and return local connection info.

        Returns:
            Dict with qpn, lid, gid for out-of-band exchange.
        """
        e = _pyverbs_modules['enums']
        qp_mod = _pyverbs_modules['qp']

        cap = qp_mod.QPCap(
            max_send_wr=max_send_wr,
            max_recv_wr=max_recv_wr,
            max_send_sge=1,
            max_recv_sge=1,
        )
        init_attr = qp_mod.QPInitAttr(
            qp_type=e.IBV_QPT_RC,
            scq=self._cq,
            rcq=self._cq,
            cap=cap,
        )
        self._qp = qp_mod.QP(self._pd, init_attr)

        port_attr = self._ctx.query_port(self._ib_port)
        gid = self._ctx.query_gid(self._ib_port, self._gid_index)

        return {
            'qpn': self._qp.qp_num,
            'lid': port_attr.lid,
            'gid': gid.gid,
        }

    def connect_qp(self, remote_qpn: int, remote_lid: int,
                    remote_gid: Any = None) -> None:
        """Transition QP through INIT -> RTR -> RTS."""
        e = _pyverbs_modules['enums']
        qp_mod = _pyverbs_modules['qp']

        # INIT
        init_attr = qp_mod.QPAttr(
            qp_state=e.IBV_QPS_INIT,
            pkey_index=0,
            port_num=self._ib_port,
            qp_access_flags=(
                e.IBV_ACCESS_LOCAL_WRITE |
                e.IBV_ACCESS_REMOTE_WRITE |
                e.IBV_ACCESS_REMOTE_READ
            ),
        )
        self._qp.to_init(init_attr)

        # RTR
        rtr_attr = qp_mod.QPAttr(
            qp_state=e.IBV_QPS_RTR,
            path_mtu=e.IBV_MTU_4096,
            dest_qp_num=remote_qpn,
            rq_psn=0,
            max_dest_rd_atomic=4,
            min_rnr_timer=12,
        )
        rtr_attr.ah_attr.dlid = remote_lid
        rtr_attr.ah_attr.sl = 0
        rtr_attr.ah_attr.port_num = self._ib_port
        if remote_gid is not None:
            rtr_attr.ah_attr.is_global = 1
            rtr_attr.ah_attr.grh.dgid = remote_gid
            rtr_attr.ah_attr.grh.sgid_index = self._gid_index
            rtr_attr.ah_attr.grh.hop_limit = 64
        self._qp.to_rtr(rtr_attr)

        # RTS
        rts_attr = qp_mod.QPAttr(
            qp_state=e.IBV_QPS_RTS,
            sq_psn=0,
            timeout=14,
            retry_cnt=7,
            rnr_retry=7,
            max_rd_atomic=4,
        )
        self._qp.to_rts(rts_attr)
        self._connected = True

    def register_buffer(self, name: str, size: int) -> RegisteredBuffer:
        """
        Register an RDMA memory region.

        Args:
            name: Buffer identifier.
            size: Buffer size in bytes.

        Returns:
            RegisteredBuffer wrapping the MR.
        """
        e = _pyverbs_modules['enums']
        access = (
            e.IBV_ACCESS_LOCAL_WRITE |
            e.IBV_ACCESS_REMOTE_WRITE |
            e.IBV_ACCESS_REMOTE_READ
        )
        buf = RegisteredBuffer(size, self._pd, access)
        self._buffers[name] = buf
        return buf

    def rdma_write(self, local_buf: RegisteredBuffer, remote_addr: int,
                   remote_rkey: int, length: int, local_offset: int = 0) -> None:
        """
        One-sided RDMA Write to remote memory.

        Args:
            local_buf: Source registered buffer.
            remote_addr: Remote virtual address.
            remote_rkey: Remote memory region key.
            length: Bytes to write.
            local_offset: Offset into local buffer.
        """
        e = _pyverbs_modules['enums']
        wr_mod = _pyverbs_modules['wr']

        sge = wr_mod.SGE(local_buf.buf + local_offset, length, local_buf.lkey)
        send_wr = wr_mod.SendWR(
            opcode=e.IBV_WR_RDMA_WRITE,
            num_sge=1,
            sg=[sge],
        )
        send_wr.wr.rdma.remote_addr = remote_addr
        send_wr.wr.rdma.rkey = remote_rkey

        self._qp.post_send(send_wr)
        self._poll_cq()
        self._bytes_sent += length
        self._ops += 1

    def rdma_read(self, local_buf: RegisteredBuffer, remote_addr: int,
                  remote_rkey: int, length: int, local_offset: int = 0) -> None:
        """
        One-sided RDMA Read from remote memory.

        Args:
            local_buf: Destination registered buffer.
            remote_addr: Remote virtual address.
            remote_rkey: Remote memory region key.
            length: Bytes to read.
            local_offset: Offset into local buffer.
        """
        e = _pyverbs_modules['enums']
        wr_mod = _pyverbs_modules['wr']

        sge = wr_mod.SGE(local_buf.buf + local_offset, length, local_buf.lkey)
        send_wr = wr_mod.SendWR(
            opcode=e.IBV_WR_RDMA_READ,
            num_sge=1,
            sg=[sge],
        )
        send_wr.wr.rdma.remote_addr = remote_addr
        send_wr.wr.rdma.rkey = remote_rkey

        self._qp.post_send(send_wr)
        self._poll_cq()
        self._bytes_recv += length
        self._ops += 1

    def send(self, data: bytes) -> int:
        """Send data via RDMA Send verb (for compatibility with cache layer)."""
        e = _pyverbs_modules['enums']
        wr_mod = _pyverbs_modules['wr']

        buf = self._get_or_create_scratch(len(data))
        buf.write(data)

        sge = wr_mod.SGE(buf.buf, len(data), buf.lkey)
        send_wr = wr_mod.SendWR(opcode=e.IBV_WR_SEND, num_sge=1, sg=[sge])
        self._qp.post_send(send_wr)
        self._poll_cq()
        self._bytes_sent += len(data)
        return len(data)

    def recv(self, size: int, timeout: float = 30.0) -> bytes:
        """Receive via RDMA Recv verb."""
        wr_mod = _pyverbs_modules['wr']

        buf = self._get_or_create_scratch(size)
        sge = wr_mod.SGE(buf.buf, size, buf.lkey)
        recv_wr = wr_mod.RecvWR(num_sge=1, sg=[sge])
        self._qp.post_recv(recv_wr)

        wc = self._poll_cq(timeout)
        received = wc[0].byte_len if wc else 0
        self._bytes_recv += received
        return buf.read(received)

    def _poll_cq(self, timeout: float = 10.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            wcs = self._cq.poll(1)
            if wcs:
                return wcs
        raise TimeoutError("CQ poll timeout")

    def _get_or_create_scratch(self, size: int) -> RegisteredBuffer:
        name = "__scratch__"
        existing = self._buffers.get(name)
        if existing and len(existing.array) >= size:
            return existing
        if existing:
            existing.close()
        return self.register_buffer(name, max(size, 65536))

    def close(self) -> None:
        """Release all RDMA resources."""
        for buf in self._buffers.values():
            buf.close()
        self._buffers.clear()

        for resource in (self._qp, self._cq, self._pd, self._ctx):
            if resource is not None:
                try:
                    resource.close()
                except Exception:
                    pass

        self._qp = None
        self._cq = None
        self._pd = None
        self._ctx = None
        self._connected = False

    @property
    def stats(self) -> Dict[str, int]:
        return {
            'bytes_sent': self._bytes_sent,
            'bytes_recv': self._bytes_recv,
            'ops': self._ops,
        }

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False
