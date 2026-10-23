"""
ctypes binding for libscuffedfabric (middleware/libscuffedfabric) plus a
BlobChannel over it.

  FabricPool         the dual-endpoint pool: hot and cold classes, each on its
                     own libfabric endpoint (MSG or RDM, any provider), one
                     registered arena per side.
  FabricBlobChannel  named byte blobs over a FabricPool, same interface as
                     TcpBlobChannel. Blobs tagged hot go on the hot endpoint,
                     everything else on the cold one.

The same Python code drives the native libibverbs implementation
(middleware/libscuffedverbs) by passing lib="verbs": both libraries export
the scuffed_fabric.h API.

Blob wire protocol (per side, data region split in half):
  [0, R)   receive slots, nslots x slot_bytes, written by the peer
  [R, 2R)  local staging, same slot indexing, source of our writes
  [2R, ..) scratch for credit writes
  each slot: 64-byte header | key | payload chunk
  header: magic u32 | blob_id u32 | key_len u16 | flags u16 | pad u32 |
          total u64 | chunk_off u64 | chunk_len u64 | pad to 64
  data write:   fi_writedata into the peer's slot s, imm = DATA | s
  credit write: 8-byte fi_writedata on the hot endpoint, imm = CREDIT | s
Writes and their notification are one operation on one endpoint, so a
notification never overtakes its payload.
"""

from __future__ import annotations

import ctypes
import os
import struct
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from typing import Deque, Dict, List, Optional, Tuple, Union

from .. import telemetry as _telemetry

HOT, COLD = 0, 1
EP_MSG, EP_RDM = 1, 2
F_IMM, F_INJECT, F_MORE = 1, 2, 4
RX_DATA, RX_MSG = 1, 2

_ROOT = Path(__file__).resolve().parents[1]
_LIBS = {
    "fabric": _ROOT / "libscuffedfabric" / "libscuffedfabric.so",
    "verbs": _ROOT / "libscuffedverbs" / "libscuffedverbs.so",
}

Buf = Union[bytes, bytearray, memoryview]


class FabricError(RuntimeError):
    pass


class FabricClosed(FabricError, ConnectionError):
    """The pool was closed locally or the peer went away (flushed / cancelled)."""


_CLOSED_CODES = {-125, -103, -104, -107, -32}  # ECANCELED, ECONNABORTED, ECONNRESET, ENOTCONN, EPIPE


class _Opts(ctypes.Structure):
    _fields_ = [
        ("provider", ctypes.c_char_p * 2),
        ("domain", ctypes.c_char_p),
        ("ep_type", ctypes.c_int * 2),
        ("single_ep", ctypes.c_int),
        ("arena_bytes", ctypes.c_size_t),
        ("hot_comp", ctypes.c_int),
        ("cold_wait", ctypes.c_int),
        ("rma_event", ctypes.c_int),
        ("tx_depth", ctypes.c_size_t * 2),
        ("rx_depth", ctypes.c_size_t * 2),
        ("rx_slot_bytes", ctypes.c_size_t),
        ("verbose", ctypes.c_int),
    ]


class _RxEv(ctypes.Structure):
    _fields_ = [
        ("kind", ctypes.c_int),
        ("cls", ctypes.c_int),
        ("data", ctypes.c_uint64),
        ("len", ctypes.c_size_t),
        ("slot_off", ctypes.c_size_t),
    ]


def build(which: str = "fabric", quiet: bool = True) -> Path:
    """Run make for libscuffedfabric or libscuffedverbs and return the .so path."""
    d = _LIBS[which].parent
    r = subprocess.run(["make", "-C", str(d)], capture_output=True, text=True)
    if r.returncode != 0:
        raise FabricError(f"make in {d} failed:\n{r.stdout}\n{r.stderr}")
    if not quiet:
        print(r.stdout)
    return _LIBS[which]


_loaded: Dict[str, ctypes.CDLL] = {}


def load(which: str = "fabric", path: Optional[str] = None) -> ctypes.CDLL:
    key = path or which
    if key in _loaded:
        return _loaded[key]
    p = Path(path or os.environ.get(f"SCUFFED_{which.upper()}_LIB", "") or _LIBS[which])
    if not p.exists():
        p = build(which)
    lib = ctypes.CDLL(str(p))
    vp, sz, i, u64, cp = ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_uint64, ctypes.c_char_p
    sig = {
        "sf_opts_default": (None, [ctypes.POINTER(_Opts)]),
        "sf_open": (vp, [ctypes.POINTER(_Opts)]),
        "sf_listen": (i, [vp, cp, i, i]),
        "sf_connect": (i, [vp, cp, i, i]),
        "sf_close": (None, [vp]),
        "sf_buf": (vp, [vp]),
        "sf_buf_len": (sz, [vp]),
        "sf_inject_size": (sz, [vp, i]),
        "sf_cq_data_size": (i, [vp, i]),
        "sf_describe": (cp, [vp, i]),
        "sf_capable": (i, [vp, i, cp]),
        "sf_write": (i, [vp, i, sz, sz, sz, u64, i]),
        "sf_read": (i, [vp, i, sz, sz, sz]),
        "sf_send": (i, [vp, i, sz, sz, u64, i]),
        "sf_tx_posted": (u64, [vp, i]),
        "sf_tx_done": (u64, [vp, i]),
        "sf_progress": (i, [vp, i]),
        "sf_wait_tx": (i, [vp, i, u64, i]),
        "sf_poll_rx": (i, [vp, i, ctypes.POINTER(_RxEv), i]),
        "sf_rma_events": (u64, [vp, i]),
        "sf_oob_barrier": (i, [vp]),
        "sf_strerror": (cp, [i]),
        "sf_now_ns": (u64, []),
    }
    for name, (res, args) in sig.items():
        f = getattr(lib, name)
        f.restype, f.argtypes = res, args
    _loaded[key] = lib
    return lib


def _ep(v: Union[str, int, None], default: int) -> int:
    if v is None:
        return default
    if isinstance(v, int):
        return v
    return EP_RDM if v.lower() == "rdm" else EP_MSG


class FabricPool:
    """One side of a dual-endpoint pool. Call listen() or connect() once."""

    def __init__(self, provider: Optional[str] = "tcp", ep_type: str = "msg", *,
                 hot_provider: Optional[str] = None, cold_provider: Optional[str] = None,
                 hot_ep: Optional[str] = None, cold_ep: Optional[str] = None,
                 single_ep: bool = False, arena_mb: int = 64, hot_cntr: bool = False,
                 cold_wait: bool = False, rma_event: bool = False, domain: Optional[str] = None,
                 tx_depth: Tuple[int, int] = (64, 512), rx_depth: Tuple[int, int] = (256, 64),
                 rx_slot_bytes: int = 4096, lib: str = "fabric", lib_path: Optional[str] = None,
                 telemetry: Optional[_telemetry.Telemetry] = None):
        self._lib = load(lib, lib_path)
        self.lib_kind = lib
        o = _Opts()
        self._lib.sf_opts_default(ctypes.byref(o))
        self._keep = []

        def cs(s: Optional[str]):
            if s is None:
                return None
            b = s.encode()
            self._keep.append(b)
            return b

        o.provider[0] = cs(hot_provider or provider)
        o.provider[1] = cs(cold_provider or provider)
        o.domain = cs(domain)
        o.ep_type[0] = _ep(hot_ep, _ep(ep_type, EP_MSG))
        o.ep_type[1] = _ep(cold_ep, _ep(ep_type, EP_MSG))
        o.single_ep = int(single_ep)
        o.arena_bytes = int(arena_mb) << 20
        o.hot_comp = 1 if hot_cntr else 0
        o.cold_wait = int(cold_wait)
        o.rma_event = int(rma_event)
        o.tx_depth[0], o.tx_depth[1] = tx_depth
        o.rx_depth[0], o.rx_depth[1] = rx_depth
        o.rx_slot_bytes = rx_slot_bytes
        self._opts = o
        self._c = self._lib.sf_open(ctypes.byref(o))
        if not self._c:
            raise FabricError("sf_open failed (arena allocation)")
        self.tel = telemetry or _telemetry.default()
        self._view: Optional[memoryview] = None
        self.connected = False

    # ---- setup -----------------------------------------------------------
    def _chk(self, r: int, what: str) -> int:
        if r < 0:
            msg = self._lib.sf_strerror(r).decode(errors="replace")
            cls = FabricClosed if r in _CLOSED_CODES else FabricError
            raise cls(f"{what}: {msg} ({r})")
        return r

    def _h(self):
        c = self._c
        if not c:
            raise FabricClosed("pool is closed")
        return c

    def listen(self, port: int, addr: str = "0.0.0.0", timeout_ms: int = 60000) -> "FabricPool":
        self._chk(self._lib.sf_listen(self._h(), addr.encode(), port, timeout_ms), "sf_listen")
        self.connected = True
        return self

    def connect(self, host: str, port: int, timeout_ms: int = 60000) -> "FabricPool":
        self._chk(self._lib.sf_connect(self._h(), host.encode(), port, timeout_ms), "sf_connect")
        self.connected = True
        return self

    # ---- introspection ---------------------------------------------------
    @property
    def buf(self) -> memoryview:
        """Writable view of the whole arena (data region plus receive slabs)."""
        if self._view is None:
            o = self._opts
            total = self.data_len + o.rx_depth[0] * o.rx_slot_bytes + o.rx_depth[1] * o.rx_slot_bytes
            addr = self._lib.sf_buf(self._h())
            self._view = memoryview((ctypes.c_char * total).from_address(addr)).cast("B")
        return self._view

    @property
    def data_len(self) -> int:
        return int(self._lib.sf_buf_len(self._h()))

    def describe(self, cls: int = HOT) -> str:
        return self._lib.sf_describe(self._h(), cls).decode()

    def capable(self, cls: int, what: str) -> bool:
        return bool(self._lib.sf_capable(self._h(), cls, what.encode()))

    def inject_size(self, cls: int = HOT) -> int:
        return int(self._lib.sf_inject_size(self._h(), cls))

    def cq_data_bytes(self, cls: int = HOT) -> int:
        return int(self._lib.sf_cq_data_size(self._h(), cls))

    # ---- data path -------------------------------------------------------
    def write(self, cls: int, loff: int, nbytes: int, roff: int, imm: Optional[int] = None,
              inject: bool = True, more: bool = False) -> None:
        fl = (F_IMM if imm is not None else 0) | (F_INJECT if inject else 0) | (F_MORE if more else 0)
        self._chk(self._lib.sf_write(self._h(), cls, loff, nbytes, roff, imm or 0, fl), "sf_write")

    def read(self, cls: int, loff: int, nbytes: int, roff: int) -> None:
        self._chk(self._lib.sf_read(self._h(), cls, loff, nbytes, roff), "sf_read")

    def send(self, cls: int, loff: int, nbytes: int, imm: Optional[int] = None) -> None:
        self._chk(self._lib.sf_send(self._h(), cls, loff, nbytes, imm or 0, int(imm is not None)), "sf_send")

    def posted(self, cls: int) -> int:
        return int(self._lib.sf_tx_posted(self._h(), cls))

    def done(self, cls: int) -> int:
        return int(self._lib.sf_tx_done(self._h(), cls))

    def progress(self, cls: int) -> int:
        return self._chk(self._lib.sf_progress(self._h(), cls), "sf_progress")

    def wait_tx(self, cls: int, target: Optional[int] = None, timeout_ms: int = 30000) -> None:
        t = self.posted(cls) if target is None else target
        self._chk(self._lib.sf_wait_tx(self._h(), cls, t, timeout_ms), "sf_wait_tx")

    def poll_rx(self, cls: int, max_events: int = 32) -> List[_RxEv]:
        arr = (_RxEv * max_events)()
        n = self._chk(self._lib.sf_poll_rx(self._h(), cls, arr, max_events), "sf_poll_rx")
        return [arr[i] for i in range(n)]

    def rma_events(self, cls: int = HOT) -> int:
        return int(self._lib.sf_rma_events(self._h(), cls))

    def barrier(self) -> None:
        self._chk(self._lib.sf_oob_barrier(self._h()), "sf_oob_barrier")

    def now_ns(self) -> int:
        return int(self._lib.sf_now_ns())

    def close(self) -> None:
        c, self._c = self._c, None
        if c:
            self._view = None
            self._lib.sf_close(c)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


# --------------------------------------------------------------- blob channel

_HDR = struct.Struct("<IIHHIQQQ")  # 40 bytes, padded to 64
_HDR_BYTES = 64
_MAGIC = 0x53424C42  # 'SBLB'
_DATA = 0x10000000
_CREDIT = 0x20000000
_KIND_MASK = 0xF0000000
_SLOT_MASK = 0x0000FFFF
_FLAG_HOT = 1


class FabricBlobChannel:
    """BlobChannel over a FabricPool. Thread-safe; any thread may send or recv."""

    def __init__(self, pool: FabricPool, nslots: int = 8, slot_bytes: int = 4 << 20):
        self.pool = pool
        self.nslots = nslots
        self.slot_bytes = slot_bytes
        self.R = nslots * slot_bytes
        if 2 * self.R + 4096 > pool.data_len:
            raise FabricError(f"arena too small: need {2 * self.R + 4096} bytes, have {pool.data_len}")
        if pool.cq_data_bytes(HOT) < 4 or pool.cq_data_bytes(COLD) < 4:
            raise FabricError("provider carries less than 4 bytes of remote CQ data")
        self.scratch = 2 * self.R
        self._lock = threading.RLock()
        self._free: Deque[int] = deque(range(nslots))        # peer slots we may write
        self._staged_at: Dict[int, Tuple[int, int]] = {}     # slot -> (class, posted count)
        self._ready: Deque[Tuple[str, bytes]] = deque()
        self._partial: Dict[int, dict] = {}
        self._blob_id = 0
        self.tel = pool.tel

    @classmethod
    def listen(cls, port: int, addr: str = "0.0.0.0", provider: str = "tcp", ep_type: str = "msg",
               nslots: int = 8, slot_mb: int = 4, timeout_ms: int = 120000, **pool_kw) -> "FabricBlobChannel":
        arena_mb = 2 * nslots * slot_mb + 1
        pool = FabricPool(provider, ep_type, arena_mb=arena_mb, **pool_kw).listen(port, addr, timeout_ms)
        return cls(pool, nslots, slot_mb << 20)

    @classmethod
    def connect(cls, host: str, port: int, provider: str = "tcp", ep_type: str = "msg",
                nslots: int = 8, slot_mb: int = 4, timeout_ms: int = 120000, **pool_kw) -> "FabricBlobChannel":
        arena_mb = 2 * nslots * slot_mb + 1
        pool = FabricPool(provider, ep_type, arena_mb=arena_mb, **pool_kw).connect(host, port, timeout_ms)
        return cls(pool, nslots, slot_mb << 20)

    # ---- internals ---------------------------------------------------------
    def _pump(self) -> int:
        """Drain both classes: completions, blob chunks, credits. Caller holds the lock."""
        p = self.pool
        n = 0
        for cls in (HOT, COLD):
            p.progress(cls)
            for ev in p.poll_rx(cls):
                n += 1
                if ev.kind != RX_DATA:
                    continue
                kind, slot = ev.data & _KIND_MASK, ev.data & _SLOT_MASK
                if kind == _CREDIT:
                    self._free.append(slot)
                elif kind == _DATA:
                    self._consume(slot)
        return n

    def _consume(self, slot: int) -> None:
        p = self.pool
        base = slot * self.slot_bytes
        buf = p.buf
        magic, blob_id, klen, flags, _pad, total, off, clen = _HDR.unpack_from(buf, base)
        if magic != _MAGIC:
            raise FabricError(f"bad blob header in slot {slot}")
        key = bytes(buf[base + _HDR_BYTES: base + _HDR_BYTES + klen]).decode()
        start = base + _HDR_BYTES + klen
        st = self._partial.get(blob_id)
        if st is None:
            st = self._partial[blob_id] = {"key": key, "data": bytearray(total), "got": 0, "t0": time.perf_counter()}
        st["data"][off:off + clen] = buf[start:start + clen]
        st["got"] += clen
        # hand the slot back before the payload leaves our hands
        p.write(HOT, self.scratch, 8, self.scratch + 8, imm=_CREDIT | slot, inject=True)
        if st["got"] >= total:
            del self._partial[blob_id]
            self._ready.append((st["key"], bytes(st["data"])))

    def _take_slot(self, deadline: Optional[float]) -> int:
        while True:
            with self._lock:
                if self._free:
                    slot = self._free.popleft()
                    staged = self._staged_at.pop(slot, None)
                    if staged is not None and self.pool.done(staged[0]) < staged[1]:
                        self.pool.wait_tx(staged[0], staged[1])
                    return slot
                self._pump()
            if deadline is not None and time.monotonic() > deadline:
                raise TimeoutError("no free remote slot (peer not receiving?)")

    # ---- BlobChannel ---------------------------------------------------------
    def send(self, key: str, payload: Buf, hot: bool = False, timeout: Optional[float] = 120.0) -> None:
        kb = key.encode()
        mv = memoryview(payload).cast("B")
        total = mv.nbytes
        cap = self.slot_bytes - _HDR_BYTES - len(kb)
        if cap <= 0:
            raise ValueError("key longer than a slot")
        cls = HOT if hot else COLD
        deadline = None if timeout is None else time.monotonic() + timeout
        t0 = time.perf_counter()
        with self._lock:
            self._blob_id = (self._blob_id + 1) & 0xFFFFFFFF
            blob_id = self._blob_id
        off = 0
        while True:
            clen = min(cap, total - off)
            slot = self._take_slot(deadline)
            src = self.R + slot * self.slot_bytes
            buf = self.pool.buf
            _HDR.pack_into(buf, src, _MAGIC, blob_id, len(kb), _FLAG_HOT if hot else 0, 0, total, off, clen)
            buf[src + _HDR_BYTES: src + _HDR_BYTES + len(kb)] = kb
            body = src + _HDR_BYTES + len(kb)
            buf[body: body + clen] = mv[off: off + clen]
            n = _HDR_BYTES + len(kb) + clen
            with self._lock:
                self.pool.write(cls, src, n, slot * self.slot_bytes, imm=_DATA | slot,
                                inject=n <= self.pool.inject_size(cls), more=False)
                self._staged_at[slot] = (cls, self.pool.posted(cls))
            off += clen
            if off >= total:
                break
        dt_us = (time.perf_counter() - t0) * 1e6
        self.tel.record("hot" if hot else "cold", dt_us, total)

    def recv(self, timeout: Optional[float] = None) -> Tuple[str, bytes]:
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            with self._lock:
                if self._ready:
                    return self._ready.popleft()
                self._pump()
                if self._ready:
                    return self._ready.popleft()
            if deadline is not None and time.monotonic() > deadline:
                raise TimeoutError("no blob before timeout")

    def close(self) -> None:
        with self._lock:
            try:
                for cls in (HOT, COLD):
                    self.pool.wait_tx(cls, timeout_ms=2000)
            except FabricError:
                pass
            self.pool.close()
