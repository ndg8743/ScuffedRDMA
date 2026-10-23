"""
KV spill/retrieve to local NVMe (Update 6, next step 1).

StorageTier keeps spilled KV blocks in one backing file:

  spill(key, buf)    -> Future[None]   queued; every `coalesce` blocks are
                                       written with one pwrite (+ fdatasync)
  retrieve(key)      -> Future[bytes]  pread, crc32 checked
  retrieve_batch(keys)                 contiguous keys read with one pread
  delete(key)                          extent goes back on the free list
  flush()                              write a partial batch now
  spill_if(decision, key, buf)         spill only when the routing decision
                                       (policy Decision, StorageDecision, or
                                       "spill") says so

Allocation is in `align`-byte units (4096). Freed extents are reused
first-fit and merged with neighbors. O_DIRECT is optional: buffers are
staged through page-aligned mmap memory; if the filesystem rejects
O_DIRECT (tmpfs, some overlays) the tier falls back to buffered I/O and
records why in `o_direct_reason`.

Latency is reported to telemetry under class "storage" (spill: submit to
durable; retrieve: submit to verified bytes). benchmark_coalescing()
produces the same JSON shape as benchmarks/results/test_arch/chimera_storage_spill.json.
"""

from __future__ import annotations

import errno
import mmap
import os
import socket
import threading
import time
import zlib
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from ..telemetry import Telemetry

ALIGN = 4096


class IntegrityError(IOError):
    """crc32 of the bytes read back does not match what was spilled."""


@dataclass
class Extent:
    offset: int
    length: int        # payload bytes
    alloc: int         # allocated bytes (multiple of align)
    crc: int


def _round_up(n: int, a: int) -> int:
    return (n + a - 1) // a * a


class StorageTier:
    def __init__(self, path: str, block_bytes: int = 1 << 20, coalesce: int = 1, workers: int = 4,
                 o_direct: bool = False, fsync: bool = True, telemetry: Optional[Telemetry] = None,
                 align: int = ALIGN):
        if coalesce < 1 or workers < 1:
            raise ValueError("coalesce and workers must be >= 1")
        if os.path.isdir(path):
            path = os.path.join(path, "kvspill.bin")
        self.path = path
        self.block_bytes = block_bytes
        self.coalesce = coalesce
        self.align = align
        self.fsync = fsync
        self.tel = telemetry
        self.o_direct_requested = o_direct
        self.o_direct = False
        self.o_direct_reason = "not requested"
        self._fd = self._open(o_direct)
        self._lock = threading.Lock()
        self._index: Dict[str, Extent] = {}
        self._free: List[Tuple[int, int]] = []      # (offset, alloc) sorted by offset
        self._end = 0
        self._pending: List[Tuple[str, bytes, Future, float]] = []
        self._inflight: Dict[str, bytes] = {}
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="kvspill")
        self.batch_write_us: List[float] = []
        self.batch_bytes: List[int] = []
        self._closed = False

    # -- file -------------------------------------------------------------------
    def _open(self, o_direct: bool) -> int:
        flags = os.O_RDWR | os.O_CREAT
        if o_direct:
            if not hasattr(os, "O_DIRECT"):
                self.o_direct_reason = "O_DIRECT not available on this platform"
            else:
                try:
                    fd = os.open(self.path, flags | os.O_DIRECT, 0o644)
                    # probe: tmpfs accepts the flag on some kernels but fails the I/O
                    buf = mmap.mmap(-1, self.align)
                    try:
                        os.pwrite(fd, buf, 0)
                    finally:
                        buf.close()
                    os.ftruncate(fd, 0)
                    self.o_direct = True
                    self.o_direct_reason = "active"
                    return fd
                except OSError as e:
                    try:
                        os.close(fd)  # type: ignore[possibly-undefined]
                    except Exception:
                        pass
                    self.o_direct_reason = f"filesystem rejected O_DIRECT ({errno.errorcode.get(e.errno, e.errno)}); buffered I/O"
        fd = os.open(self.path, flags, 0o644)
        os.ftruncate(fd, 0)
        return fd

    def _alloc(self, nbytes: int) -> int:
        need = _round_up(max(nbytes, 1), self.align)
        for i, (off, size) in enumerate(self._free):
            if size >= need:
                if size == need:
                    self._free.pop(i)
                else:
                    self._free[i] = (off + need, size - need)
                return off
        off = self._end
        self._end += need
        return off

    def _release(self, off: int, alloc: int) -> None:
        self._free.append((off, alloc))
        self._free.sort()
        merged: List[Tuple[int, int]] = []
        for o, s in self._free:
            if merged and merged[-1][0] + merged[-1][1] == o:
                merged[-1] = (merged[-1][0], merged[-1][1] + s)
            else:
                merged.append((o, s))
        # shrink the tail
        if merged and merged[-1][0] + merged[-1][1] == self._end:
            self._end = merged[-1][0]
            merged.pop()
        self._free = merged

    # -- write path -----------------------------------------------------------------
    def spill(self, key: str, buf: Any) -> Future:
        if self._closed:
            raise RuntimeError("StorageTier is closed")
        data = bytes(memoryview(buf).cast("B"))
        fut: Future = Future()
        with self._lock:
            if key in self._index or key in self._inflight:
                self._delete_locked(key)
            self._pending.append((key, data, fut, time.perf_counter()))
            self._inflight[key] = data
            batch = None
            if len(self._pending) >= self.coalesce:
                batch, self._pending = self._pending, []
        if batch:
            self._pool.submit(self._write_batch, batch)
        return fut

    def flush(self) -> None:
        with self._lock:
            batch, self._pending = self._pending, []
        if batch:
            self._pool.submit(self._write_batch, batch).result()

    def _write_batch(self, batch: List[Tuple[str, bytes, Future, float]]) -> None:
        try:
            # each block gets its own aligned slot inside one contiguous extent
            slots = [_round_up(len(d), self.align) for _, d, _, _ in batch]
            total = sum(slots)
            with self._lock:
                base = self._alloc(total)
            if self.o_direct:
                stage = mmap.mmap(-1, total)
                pos = 0
                for (_, d, _, _), s in zip(batch, slots):
                    stage[pos:pos + len(d)] = d
                    pos += s
                payload: Any = stage
            else:
                parts = []
                for (_, d, _, _), s in zip(batch, slots):
                    parts.append(d)
                    if s > len(d):
                        parts.append(b"\0" * (s - len(d)))
                payload = b"".join(parts)
            t0 = time.perf_counter()
            n = os.pwrite(self._fd, payload, base)
            if n != total:
                raise IOError(f"short write {n} of {total}")
            if self.fsync:
                os.fdatasync(self._fd)
            dt_us = (time.perf_counter() - t0) * 1e6
            if self.o_direct:
                payload.close()
            done = time.perf_counter()
            with self._lock:
                self.batch_write_us.append(dt_us)
                self.batch_bytes.append(sum(len(d) for _, d, _, _ in batch))
                pos = base
                for (key, d, fut, ts), s in zip(batch, slots):
                    if self._inflight.get(key) is d:
                        self._index[key] = Extent(pos, len(d), s, zlib.crc32(d))
                        del self._inflight[key]
                    else:
                        # deleted or overwritten while in flight: free its slot
                        self._release(pos, s)
                    pos += s
            for (key, d, fut, ts), s in zip(batch, slots):
                if self.tel is not None:
                    self.tel.record("storage", (done - ts) * 1e6, len(d))
                fut.set_result(None)
        except BaseException as e:  # pragma: no cover - surfaced through futures
            for _, _, fut, _ in batch:
                if not fut.done():
                    fut.set_exception(e)
            if self.tel is not None:
                self.tel.event("storage", "timeout")

    # -- read path ------------------------------------------------------------------
    def _pread(self, off: int, length: int, alloc: int) -> bytes:
        if self.o_direct:
            buf = mmap.mmap(-1, alloc)
            try:
                n = os.preadv(self._fd, [buf], off)
                if n < length:
                    raise IOError(f"short read {n} of {length}")
                return bytes(buf[:length])
            finally:
                buf.close()
        data = os.pread(self._fd, length, off)
        if len(data) != length:
            raise IOError(f"short read {len(data)} of {length}")
        return data

    def _retrieve(self, key: str, t0: float) -> bytes:
        with self._lock:
            if key in self._inflight:
                data = self._inflight[key]
                ext = None
            else:
                ext = self._index.get(key)
                if ext is None:
                    raise KeyError(key)
        if ext is not None:
            data = self._pread(ext.offset, ext.length, ext.alloc)
            if zlib.crc32(data) != ext.crc:
                if self.tel is not None:
                    self.tel.event("storage", "qp_error")
                raise IntegrityError(f"crc mismatch for {key!r} at offset {ext.offset}")
        if self.tel is not None:
            self.tel.record("storage", (time.perf_counter() - t0) * 1e6, len(data))
        return data

    def retrieve(self, key: str) -> Future:
        return self._pool.submit(self._retrieve, key, time.perf_counter())

    def retrieve_batch(self, keys: Sequence[str]) -> Dict[str, bytes]:
        """Read keys, merging physically contiguous extents into single preads."""
        with self._lock:
            missing = [k for k in keys if k not in self._index and k not in self._inflight]
            if missing:
                raise KeyError(missing[0])
            exts = sorted(((self._index[k], k) for k in keys if k in self._index), key=lambda e: e[0].offset)
            out = {k: self._inflight[k] for k in keys if k in self._inflight}
        i = 0
        while i < len(exts):
            j = i
            while j + 1 < len(exts) and exts[j][0].offset + exts[j][0].alloc == exts[j + 1][0].offset:
                j += 1
            start = exts[i][0].offset
            span = exts[j][0].offset + exts[j][0].alloc - start
            blob = self._pread(start, span, span)
            for e, k in exts[i:j + 1]:
                data = blob[e.offset - start:e.offset - start + e.length]
                if zlib.crc32(data) != e.crc:
                    raise IntegrityError(f"crc mismatch for {k!r}")
                out[k] = data
            i = j + 1
        return out

    # -- management -----------------------------------------------------------------
    def _delete_locked(self, key: str) -> bool:
        if key in self._inflight:
            del self._inflight[key]
            return True
        ext = self._index.pop(key, None)
        if ext is None:
            return False
        self._release(ext.offset, ext.alloc)
        return True

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._delete_locked(key)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._index or key in self._inflight

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._index) + list(self._inflight)

    def extent(self, key: str) -> Optional[Extent]:
        with self._lock:
            return self._index.get(key)

    def spill_if(self, decision: Any, key: str, buf: Any) -> Optional[Future]:
        route = getattr(decision, "route", None)
        if route is None:
            route = getattr(decision, "value", decision)
        return self.spill(key, buf) if str(route).lower() == "spill" else None

    def drop_page_cache(self) -> None:
        try:
            os.posix_fadvise(self._fd, 0, 0, os.POSIX_FADV_DONTNEED)
        except (AttributeError, OSError):
            pass

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            used = sum(e.alloc for e in self._index.values())
            return {"path": self.path, "keys": len(self._index), "pending": len(self._pending),
                    "file_bytes": self._end, "used_bytes": used,
                    "free_extents": len(self._free), "free_bytes": sum(s for _, s in self._free),
                    "o_direct": self.o_direct, "o_direct_reason": self.o_direct_reason,
                    "coalesce": self.coalesce, "batches_written": len(self.batch_write_us)}

    def close(self, remove: bool = False) -> None:
        if self._closed:
            return
        self.flush()
        self._pool.shutdown(wait=True)
        os.close(self._fd)
        self._closed = True
        if remove:
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def _pct(xs: Sequence[float], p: float) -> float:
    return float(np.percentile(np.asarray(xs, dtype=float), p)) if len(xs) else float("nan")


def benchmark_coalescing(path: str, block_bytes: int = 1568 * 1024,
                         coalesce_list: Iterable[int] = (1, 2, 5, 10, 20, 50),
                         batches: int = 20, o_direct: bool = False, fsync: bool = True,
                         block_sizes: Optional[Iterable[int]] = None, seed: int = 0,
                         meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Sweep coalescing depth (and optionally block size) through StorageTier.

    For each (block size, coalesce c): spill `batches` x c blocks, time each
    batch write (pwrite + fdatasync), drop the page cache, then read every
    batch back with one retrieve_batch() call. Top-level fields mirror
    chimera_storage_spill.json (write_us / read_us are medians per coalesced
    payload); percentiles and the full sweep are extra fields.
    """
    rng = np.random.default_rng(seed)
    sizes = list(block_sizes) if block_sizes else [block_bytes]
    sweeps = []
    o_direct_status = None
    for bsz in sizes:
        block = rng.integers(0, 256, size=bsz, dtype=np.uint8).tobytes()
        rows = []
        for c in coalesce_list:
            fpath = path if not os.path.isdir(path) else os.path.join(path, f"bench_{bsz}_{c}.bin")
            tier = StorageTier(fpath, block_bytes=bsz, coalesce=c, workers=1, o_direct=o_direct, fsync=fsync)
            o_direct_status = tier.o_direct_reason
            try:
                futs = [tier.spill(f"b{i}_{j}", block) for i in range(batches) for j in range(c)]
                tier.flush()
                for f in futs:
                    f.result()
                tier.drop_page_cache()
                read_us = []
                for i in range(batches):
                    t0 = time.perf_counter()
                    got = tier.retrieve_batch([f"b{i}_{j}" for j in range(c)])
                    read_us.append((time.perf_counter() - t0) * 1e6)
                    assert len(got) == c
                write_us = list(tier.batch_write_us)
            finally:
                tier.close(remove=True)
            payload = bsz * c
            w50, r50 = _pct(write_us, 50), _pct(read_us, 50)
            rows.append({
                "coalesce": c, "payload_kb": payload / 1024,
                "write_us": w50, "write_mbps": (payload / 1e6) / (w50 / 1e6) if w50 > 0 else 0.0,
                "read_us": r50, "read_mbps": (payload / 1e6) / (r50 / 1e6) if r50 > 0 else 0.0,
                "write_p95_us": _pct(write_us, 95), "write_p99_us": _pct(write_us, 99),
                "read_p95_us": _pct(read_us, 95), "read_p99_us": _pct(read_us, 99),
                "batches": batches,
            })
        sweeps.append({"block_bytes": bsz, "single_block_kb": bsz / 1024, "coalesce_results": rows})
    first = sweeps[0]
    out = {"hostname": socket.gethostname(), "path": path, "o_direct": o_direct_status, "fsync": fsync,
           "single_block_kb": first["single_block_kb"], "coalesce_results": first["coalesce_results"],
           "sweeps": sweeps}
    if meta:
        out.update(meta)
    return out
