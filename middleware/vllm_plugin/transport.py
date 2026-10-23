"""
KV push transport for the connector.

  KVSender    producer side (prefill). One per worker rank. Connects to the
              consumer at peer:port+rank in the background, queues blobs,
              tags each hot/cold with the WFA classifier, sends from a
              thread, and reports every transfer to middleware.telemetry.
  KVReceiver  consumer side (decode). Listens on port+rank, receives blobs
              into a bounded staging pool keyed by blob key, and hands them
              to start_load_kv via wait(key, timeout).

Both sit on a BlobChannel (middleware/fabric/channel.py):
  transport="fabric"  middleware.fabric.pool.FabricBlobChannel (libfabric
                      hot/cold endpoints; provider/ep_type passed through).
                      Falls back to TCP when libfabric or the pool module is
                      unavailable; the fallback is counted as a tcp_fallback
                      telemetry event.
  transport="tcp"     TcpBlobChannel.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections import OrderedDict
from typing import Callable, Dict, Optional, Tuple

from middleware import telemetry as _telemetry
from middleware.fabric.channel import BlobChannel, TcpBlobChannel
from middleware.telemetry import SignalVector

log = logging.getLogger("scuffed.vllm")

_FABRIC_IMPORT_ERR: Optional[BaseException] = None


def _wfa(hot_threshold: int, cold_threshold: int):
    from middleware.rdma_tensor_cache.wfa_classifier import WFAClassifier
    return WFAClassifier(hot_threshold=hot_threshold, cold_threshold=cold_threshold)


def _is_hot(queue_selection) -> bool:
    return getattr(queue_selection, "value", str(queue_selection)) == "hot"


def open_channel(role: str, host: str, port: int, transport: str = "tcp",
                 provider: Optional[str] = None, ep_type: Optional[str] = None,
                 bind: str = "0.0.0.0", timeout: Optional[float] = None,
                 tel=None) -> Tuple[BlobChannel, str]:
    """Open one side of a channel. role is "listen" or "connect". Returns (channel, transport_used)."""
    global _FABRIC_IMPORT_ERR
    tel = tel or _telemetry.default()
    if transport == "fabric" and _FABRIC_IMPORT_ERR is None:
        try:
            try:
                from middleware.fabric.pool import FabricBlobChannel  # built separately
            except ImportError as e:
                _FABRIC_IMPORT_ERR = e          # remember: do not retry the import on every reconnect
                raise
            kw = {}
            if provider:
                kw["provider"] = provider
            if ep_type:
                kw["ep_type"] = ep_type
            if role == "listen":
                return FabricBlobChannel.listen(port, **kw), "fabric"
            return FabricBlobChannel.connect(host, port, **kw), "fabric"
        except Exception as e:  # ImportError, OSError from fi_getinfo, missing lib
            log.warning("fabric transport unavailable (%s); falling back to TCP", e)
            tel.event("hot", "tcp_fallback")
            tel.event("cold", "tcp_fallback")
    elif transport == "fabric":
        tel.event("hot", "tcp_fallback")
        tel.event("cold", "tcp_fallback")
    if role == "listen":
        return TcpBlobChannel.listen(port, addr=bind, timeout=timeout), "tcp"
    return TcpBlobChannel.connect(host, port, timeout=timeout or 30.0), "tcp"


class KVSender:
    def __init__(self, peer: str, port: int, *, transport: str = "tcp",
                 provider: Optional[str] = None, ep_type: Optional[str] = None,
                 hot_threshold: int = 4096, cold_threshold: int = 262144,
                 connect_timeout: float = 600.0, queue_max: int = 1024,
                 channel: Optional[BlobChannel] = None, tel=None):
        self.peer, self.port = peer, port
        self.transport, self.provider, self.ep_type = transport, provider, ep_type
        self.transport_used = "injected" if channel is not None else None
        self._ch = channel
        self._tel = tel or _telemetry.default()
        self._wfa = _wfa(hot_threshold, cold_threshold)
        self._q: "queue.Queue" = queue.Queue(maxsize=queue_max)
        self._connect_timeout = connect_timeout
        self._ready = threading.Event()
        if channel is not None:
            self._ready.set()
        self._err: Optional[BaseException] = None
        self._closed = False
        self._t = threading.Thread(target=self._run, name="scuffed-kv-send", daemon=True)
        self._t.start()

    def _connect(self) -> None:
        deadline = time.monotonic() + self._connect_timeout
        delay = 0.2
        while not self._closed:
            try:
                self._ch, self.transport_used = open_channel(
                    "connect", self.peer, self.port, self.transport,
                    self.provider, self.ep_type, tel=self._tel)
                self._ready.set()
                log.info("KV sender connected to %s:%d over %s", self.peer, self.port, self.transport_used)
                return
            except OSError as e:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"could not reach consumer {self.peer}:{self.port}: {e}")
                time.sleep(delay)
                delay = min(delay * 2, 5.0)

    def classify(self, key: str, nbytes: int, layer_idx: int = -1) -> bool:
        return _is_hot(self._wfa.classify(key, nbytes, layer_idx if layer_idx >= 0 else None))

    def send(self, key: str, payload: bytes, *, hot: Optional[bool] = None, layer_idx: int = -1,
             seq_len: int = 0, phase: str = "prefill", role: str = "kv") -> bool:
        """Queue a blob. hot=None lets the WFA classifier decide. Returns the hot flag used."""
        if self._err is not None:
            raise RuntimeError("KV sender failed") from self._err
        if hot is None:
            hot = self.classify(key, len(payload), layer_idx)
        self._q.put((key, payload, hot, layer_idx, seq_len, phase, role, time.perf_counter()))
        self._tel.set_queue_depth("hot" if hot else "cold", self._q.qsize())
        return hot

    def _run(self) -> None:
        try:
            if self._ch is None:
                self._connect()
            while True:
                item = self._q.get()
                if item is None:
                    self._q.task_done()
                    return
                key, payload, hot, layer_idx, seq_len, phase, role, t_enq = item
                cls = "hot" if hot else "cold"
                t0 = time.perf_counter()
                try:
                    self._ch.send(key, payload, hot=hot)
                except Exception as e:
                    self._tel.event(cls, "qp_error")
                    self._err = e
                    self._q.task_done()
                    raise
                t1 = time.perf_counter()
                send_us = (t1 - t0) * 1e6
                self._tel.observe(SignalVector(
                    size_bytes=len(payload), role=role, tensor_id=key, layer_idx=layer_idx,
                    qp_class=cls, queue_depth=self._q.qsize(), completion_us=send_us,
                    phase=phase, seq_len=seq_len))
                self._tel.record(f"{cls}_queued", (t1 - t_enq) * 1e6, 0)
                self._q.task_done()
        except BaseException as e:  # noqa: BLE001
            self._err = e
            log.error("KV sender stopped: %s", e)
            # drain so flush() does not hang
            while True:
                try:
                    self._q.get_nowait()
                    self._q.task_done()
                except queue.Empty:
                    break

    def flush(self, timeout: Optional[float] = None) -> bool:
        """Block until every queued blob has been handed to the channel."""
        if timeout is None:
            self._q.join()
            return self._err is None
        end = time.monotonic() + timeout
        while self._q.unfinished_tasks and time.monotonic() < end:
            time.sleep(0.001)
        return self._q.unfinished_tasks == 0 and self._err is None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._q.put_nowait(None)
        except queue.Full:
            pass
        self._t.join(timeout=5)
        if self._ch is not None:
            self._ch.close()


class KVReceiver:
    def __init__(self, port: int, *, transport: str = "tcp", provider: Optional[str] = None,
                 ep_type: Optional[str] = None, bind: str = "0.0.0.0",
                 staging_max_bytes: int = 8 << 30, channel: Optional[BlobChannel] = None,
                 tel=None, on_blob: Optional[Callable[[str, bytes], None]] = None):
        self.port, self.bind = port, bind
        self.transport, self.provider, self.ep_type = transport, provider, ep_type
        self.transport_used = "injected" if channel is not None else None
        self._tel = tel or _telemetry.default()
        self._staged: "OrderedDict[str, Tuple[bytes, float]]" = OrderedDict()
        self._bytes = 0
        self._max = staging_max_bytes
        self._cv = threading.Condition()
        self._closed = False
        self._ch = channel
        self._on_blob = on_blob
        self._t = threading.Thread(target=self._run, name="scuffed-kv-recv", daemon=True)
        self._t.start()

    def _run(self) -> None:
        while not self._closed:
            if self._ch is None:
                try:
                    self._ch, self.transport_used = open_channel(
                        "listen", "", self.port, self.transport, self.provider,
                        self.ep_type, bind=self.bind, tel=self._tel)
                    log.info("KV receiver accepted on port %d over %s", self.port, self.transport_used)
                except OSError as e:
                    log.warning("KV receiver listen failed: %s", e)
                    time.sleep(1.0)
                    continue
            try:
                key, payload = self._ch.recv(timeout=None)
            except (ConnectionError, OSError, ValueError) as e:
                if self._closed:
                    return
                log.info("KV receiver lost producer (%s); re-listening", e)
                self._tel.event("cold", "reconnect")
                try:
                    self._ch.close()
                finally:
                    self._ch = None
                continue
            with self._cv:
                self._staged[key] = (payload, time.perf_counter())
                self._bytes += len(payload)
                while self._bytes > self._max and len(self._staged) > 1:
                    old, (ob, _) = self._staged.popitem(last=False)
                    self._bytes -= len(ob)
                    log.warning("staging full, dropped %s", old)
                    self._tel.event("cold", "staging_evict")
                self._cv.notify_all()
            if self._on_blob is not None:
                self._on_blob(key, payload)

    def wait(self, key: str, timeout: Optional[float] = 30.0) -> Optional[bytes]:
        """Pop the blob for key, waiting up to timeout seconds. None on timeout."""
        end = None if timeout is None else time.monotonic() + timeout
        with self._cv:
            while key not in self._staged:
                rem = None if end is None else end - time.monotonic()
                if rem is not None and rem <= 0:
                    return None
                self._cv.wait(rem)
            payload, _ = self._staged.pop(key)
            self._bytes -= len(payload)
            return payload

    def staged_keys(self):
        with self._cv:
            return list(self._staged)

    def discard_prefix(self, prefix: str) -> int:
        with self._cv:
            ks = [k for k in self._staged if k.startswith(prefix)]
            for k in ks:
                self._bytes -= len(self._staged.pop(k)[0])
            return len(ks)

    def close(self) -> None:
        self._closed = True
        if self._ch is not None:
            self._ch.close()
        with self._cv:
            self._cv.notify_all()
