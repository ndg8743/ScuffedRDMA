"""
Dual QP Pool Transport for libscuffedrdma.

Provides separate hot (low-latency, busy-poll) and cold (high-throughput,
sleep-poll) RC QP pools over a shared PD. This eliminates head-of-line
blocking when small latency-sensitive transfers share a QP with large
bulk transfers.

Addresses UCX issues:
  - #11004: All RoCE QPs use same UDP src port (our QPs get distinct ports)
  - #11034: pthread_spin_lock contention with shared ucp_context
  - #1319: On-demand QP creation
"""

import ctypes
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

_pyverbs_available = False
_pv = {}  # pyverbs modules

try:
    import pyverbs.device as _pv_device
    import pyverbs.pd as _pv_pd
    import pyverbs.cq as _pv_cq
    import pyverbs.qp as _pv_qp
    import pyverbs.mr as _pv_mr
    import pyverbs.enums as _pv_enums
    import pyverbs.wr as _pv_wr
    import pyverbs.addr as _pv_addr

    _pv = {
        'device': _pv_device, 'pd': _pv_pd, 'cq': _pv_cq,
        'qp': _pv_qp, 'mr': _pv_mr, 'enums': _pv_enums,
        'wr': _pv_wr, 'addr': _pv_addr,
    }
    _pyverbs_available = True
except ImportError:
    pass


class QueueSelection(Enum):
    HOT_QP = "hot"
    COLD_QP = "cold"


@dataclass
class QueueStats:
    latencies_us: List[float] = field(default_factory=list)
    bytes_transferred: int = 0
    ops_completed: int = 0
    poll_iterations: int = 0
    queue_depth_samples: List[int] = field(default_factory=list)

    @property
    def p50_us(self) -> float:
        if not self.latencies_us:
            return 0.0
        s = sorted(self.latencies_us)
        return s[len(s) // 2]

    @property
    def p95_us(self) -> float:
        if not self.latencies_us:
            return 0.0
        s = sorted(self.latencies_us)
        return s[int(len(s) * 0.95)]

    @property
    def p99_us(self) -> float:
        if not self.latencies_us:
            return 0.0
        s = sorted(self.latencies_us)
        return s[int(len(s) * 0.99)]

    def to_dict(self) -> dict:
        return {
            'p50_us': self.p50_us,
            'p95_us': self.p95_us,
            'p99_us': self.p99_us,
            'bytes_transferred': self.bytes_transferred,
            'ops_completed': self.ops_completed,
            'poll_iterations': self.poll_iterations,
            'avg_queue_depth': (
                sum(self.queue_depth_samples) / len(self.queue_depth_samples)
                if self.queue_depth_samples else 0.0
            ),
        }


class RegisteredBuffer:
    """RDMA memory region with ctypes backing store."""

    def __init__(self, size: int, pd: Any, access_flags: int):
        self._size = size
        self.mr = _pv['mr'].MR(pd, size, access_flags)

    @property
    def buf(self) -> int:
        return self.mr.buf

    @property
    def addr(self) -> int:
        return self.mr.buf

    @property
    def lkey(self) -> int:
        return self.mr.lkey

    @property
    def rkey(self) -> int:
        return self.mr.rkey

    @property
    def size(self) -> int:
        return self._size

    def write(self, data: bytes, offset: int = 0) -> None:
        ctypes.memmove(self.mr.buf + offset, data, len(data))

    def read(self, length: int, offset: int = 0) -> bytes:
        return ctypes.string_at(self.mr.buf + offset, length)

    def close(self) -> None:
        try:
            self.mr.close()
        except Exception:
            pass


class _QPEntry:
    """A single QP with its dedicated CQ."""

    def __init__(self, ctx: Any, pd: Any, cq_depth: int,
                 max_send_wr: int, max_recv_wr: int):
        e = _pv['enums']
        q = _pv['qp']

        self.cq = _pv['cq'].CQ(ctx, cq_depth)
        cap = q.QPCap(max_send_wr=max_send_wr, max_recv_wr=max_recv_wr,
                       max_send_sge=1, max_recv_sge=1)
        self.qp = q.QP(pd, q.QPInitAttr(qp_type=e.IBV_QPT_RC,
                                          scq=self.cq, rcq=self.cq, cap=cap))
        self.outstanding = 0

    @property
    def qp_num(self) -> int:
        return self.qp.qp_num

    def connect(self, remote_qpn: int, remote_lid: int,
                remote_gid: Any, ib_port: int, gid_index: int) -> None:
        """INIT -> RTR -> RTS."""
        e = _pv['enums']
        q = _pv['qp']
        a = _pv['addr']

        # INIT
        init_attr = q.QPAttr()
        init_attr.qp_state = e.IBV_QPS_INIT
        init_attr.pkey_index = 0
        init_attr.port_num = ib_port
        init_attr.qp_access_flags = (
            e.IBV_ACCESS_LOCAL_WRITE |
            e.IBV_ACCESS_REMOTE_WRITE |
            e.IBV_ACCESS_REMOTE_READ
        )
        self.qp.to_init(init_attr)

        # RTR - build AHAttr with GlobalRoute for RoCE
        gr = a.GlobalRoute(dgid=remote_gid, sgid_index=gid_index)
        gr.hop_limit = 1
        ah_attr = a.AHAttr(dlid=remote_lid, sl=0, port_num=ib_port,
                            is_global=1, gr=gr)

        rtr_attr = q.QPAttr()
        rtr_attr.qp_state = e.IBV_QPS_RTR
        rtr_attr.path_mtu = e.IBV_MTU_1024
        rtr_attr.dest_qp_num = remote_qpn
        rtr_attr.rq_psn = 0
        rtr_attr.max_dest_rd_atomic = 1
        rtr_attr.min_rnr_timer = 12
        rtr_attr.ah_attr = ah_attr
        self.qp.to_rtr(rtr_attr)

        # RTS
        rts_attr = q.QPAttr()
        rts_attr.qp_state = e.IBV_QPS_RTS
        rts_attr.sq_psn = 0
        rts_attr.timeout = 14
        rts_attr.retry_cnt = 7
        rts_attr.rnr_retry = 7
        rts_attr.max_rd_atomic = 1
        self.qp.to_rts(rts_attr)

    def close(self) -> None:
        for resource in (self.qp, self.cq):
            try:
                resource.close()
            except Exception:
                pass


class DualQPPool:
    """
    Dual QP pool: hot (busy-poll) and cold (sleep-poll) RC queues.

    Hot QPs: CQ depth 16, busy-poll for minimum latency.
    Cold QPs: CQ depth 256, sleep-poll for throughput.
    All QPs share one PD and registered memory regions.
    """

    def __init__(self, device_name: str = "rxe0", ib_port: int = 1,
                 gid_index: int = 1, n_hot: int = 2, n_cold: int = 2):
        if not _pyverbs_available:
            raise ImportError("pyverbs not available. apt install python3-pyverbs")

        self._device_name = device_name
        self._ib_port = ib_port
        self._gid_index = gid_index
        self._n_hot = n_hot
        self._n_cold = n_cold

        self._ctx: Any = None
        self._pd: Any = None
        self._gid: Any = None  # GID object for connect
        self._hot_qps: List[_QPEntry] = []
        self._cold_qps: List[_QPEntry] = []
        self._buffers: Dict[str, RegisteredBuffer] = {}
        self._hot_idx = 0
        self._cold_idx = 0

        self.hot_stats = QueueStats()
        self.cold_stats = QueueStats()

    def open(self) -> None:
        """Open device, allocate PD, create QP pools."""
        self._ctx = _pv['device'].Context(name=self._device_name)
        self._pd = _pv['pd'].PD(self._ctx)
        self._gid = self._ctx.query_gid(self._ib_port, self._gid_index)

        for _ in range(self._n_hot):
            self._hot_qps.append(
                _QPEntry(self._ctx, self._pd, cq_depth=16,
                         max_send_wr=16, max_recv_wr=16))

        for _ in range(self._n_cold):
            self._cold_qps.append(
                _QPEntry(self._ctx, self._pd, cq_depth=256,
                         max_send_wr=128, max_recv_wr=128))

    def get_local_info(self) -> Dict[str, Any]:
        """Local connection info for out-of-band exchange."""
        port_attr = self._ctx.query_port(self._ib_port)
        return {
            'lid': port_attr.lid,
            'gid': self._gid,  # GID object, passed directly to GlobalRoute
            'hot_qpns': [qpe.qp_num for qpe in self._hot_qps],
            'cold_qpns': [qpe.qp_num for qpe in self._cold_qps],
        }

    def connect_all(self, remote_info: Dict[str, Any]) -> None:
        """Connect all QPs to their remote counterparts."""
        lid = remote_info['lid']
        gid = remote_info['gid']

        for i, qpe in enumerate(self._hot_qps):
            qpe.connect(remote_info['hot_qpns'][i], lid, gid,
                        self._ib_port, self._gid_index)

        for i, qpe in enumerate(self._cold_qps):
            qpe.connect(remote_info['cold_qpns'][i], lid, gid,
                        self._ib_port, self._gid_index)

    def register_buffer(self, name: str, size: int) -> RegisteredBuffer:
        """Register a shared memory region accessible by all QPs."""
        e = _pv['enums']
        access = (e.IBV_ACCESS_LOCAL_WRITE | e.IBV_ACCESS_REMOTE_WRITE |
                  e.IBV_ACCESS_REMOTE_READ)
        buf = RegisteredBuffer(size, self._pd, access)
        self._buffers[name] = buf
        return buf

    def _select_hot_qp(self) -> _QPEntry:
        qpe = self._hot_qps[self._hot_idx % self._n_hot]
        self._hot_idx += 1
        return qpe

    def _select_cold_qp(self) -> _QPEntry:
        qpe = self._cold_qps[self._cold_idx % self._n_cold]
        self._cold_idx += 1
        return qpe

    def post_write_hot(self, local_buf: RegisteredBuffer, remote_addr: int,
                       remote_rkey: int, length: int,
                       local_offset: int = 0) -> float:
        """RDMA Write on hot QP, busy-poll. Returns latency in us."""
        qpe = self._select_hot_qp()
        t0 = time.perf_counter()
        self._post_rdma_write(qpe, local_buf, remote_addr, remote_rkey,
                              length, local_offset)
        iters = self._poll_busy(qpe)
        lat = (time.perf_counter() - t0) * 1e6
        self.hot_stats.latencies_us.append(lat)
        self.hot_stats.bytes_transferred += length
        self.hot_stats.ops_completed += 1
        self.hot_stats.poll_iterations += iters
        return lat

    def post_write_cold(self, local_buf: RegisteredBuffer, remote_addr: int,
                        remote_rkey: int, length: int,
                        local_offset: int = 0) -> float:
        """RDMA Write on cold QP, sleep-poll. Returns latency in us."""
        qpe = self._select_cold_qp()
        t0 = time.perf_counter()
        self._post_rdma_write(qpe, local_buf, remote_addr, remote_rkey,
                              length, local_offset)
        iters = self._poll_sleep(qpe)
        lat = (time.perf_counter() - t0) * 1e6
        self.cold_stats.latencies_us.append(lat)
        self.cold_stats.bytes_transferred += length
        self.cold_stats.ops_completed += 1
        self.cold_stats.poll_iterations += iters
        return lat

    def _post_rdma_write(self, qpe: _QPEntry, local_buf: RegisteredBuffer,
                         remote_addr: int, remote_rkey: int,
                         length: int, local_offset: int) -> None:
        e = _pv['enums']
        w = _pv['wr']
        sge = w.SGE(local_buf.buf + local_offset, length, local_buf.lkey)
        send_wr = w.SendWR(opcode=e.IBV_WR_RDMA_WRITE, num_sge=1, sg=[sge])
        send_wr.set_wr_rdma(remote_rkey, remote_addr)
        qpe.qp.post_send(send_wr)
        qpe.outstanding += 1

    def _poll_busy(self, qpe: _QPEntry, timeout: float = 5.0) -> int:
        """Busy-poll CQ: minimum latency, maximum CPU."""
        deadline = time.perf_counter() + timeout
        iters = 0
        while time.perf_counter() < deadline:
            iters += 1
            nc, wcs = qpe.cq.poll(num_entries=1)
            if nc > 0:
                qpe.outstanding -= 1
                return iters
        raise TimeoutError("Hot QP CQ poll timeout")

    def _poll_sleep(self, qpe: _QPEntry, timeout: float = 10.0,
                    sleep_us: float = 50.0) -> int:
        """Sleep-poll CQ: trades latency for CPU efficiency."""
        deadline = time.perf_counter() + timeout
        iters = 0
        while time.perf_counter() < deadline:
            iters += 1
            nc, wcs = qpe.cq.poll(num_entries=1)
            if nc > 0:
                qpe.outstanding -= 1
                return iters
            time.sleep(sleep_us / 1e6)
        raise TimeoutError("Cold QP CQ poll timeout")

    @property
    def hot_queue_depth(self) -> int:
        return sum(qpe.outstanding for qpe in self._hot_qps)

    @property
    def cold_queue_depth(self) -> int:
        return sum(qpe.outstanding for qpe in self._cold_qps)

    def sample_queue_depths(self) -> Tuple[int, int]:
        hd = self.hot_queue_depth
        cd = self.cold_queue_depth
        self.hot_stats.queue_depth_samples.append(hd)
        self.cold_stats.queue_depth_samples.append(cd)
        return hd, cd

    def close(self) -> None:
        for buf in self._buffers.values():
            buf.close()
        self._buffers.clear()

        for qpe in self._hot_qps + self._cold_qps:
            qpe.close()
        self._hot_qps.clear()
        self._cold_qps.clear()

        for resource in (self._pd, self._ctx):
            if resource is not None:
                try:
                    resource.close()
                except Exception:
                    pass
        self._pd = None
        self._ctx = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False
