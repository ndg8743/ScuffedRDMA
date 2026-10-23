"""
Blob channels: move named byte blobs (KV layers, metadata) between two
processes. The vLLM connector and the storage tier talk to this interface,
not to a specific transport.

  BlobChannel        the protocol (send / recv / close)
  TcpBlobChannel     length-prefixed framing over one TCP socket. Baseline
                     and test double; runs anywhere.
  FabricBlobChannel  in middleware.fabric.pool: libfabric dual-endpoint pool
                     (hot endpoint for headers and small blobs, cold endpoint
                     for bulk), over verbs / tcp / shm providers.

Wire framing for TcpBlobChannel:
  u32 magic 'SCBC' | u8 flags (bit0 = hot) | u16 key_len | u64 payload_len | key | payload
"""

from __future__ import annotations

import socket
import struct
import threading
from typing import Optional, Protocol, Tuple, Union, runtime_checkable

Buf = Union[bytes, bytearray, memoryview]

_MAGIC = 0x53434243  # 'SCBC'
_HDR = struct.Struct("!IBHQ")


@runtime_checkable
class BlobChannel(Protocol):
    def send(self, key: str, payload: Buf, hot: bool = False) -> None: ...
    def recv(self, timeout: Optional[float] = None) -> Tuple[str, bytes]: ...
    def close(self) -> None: ...


class TcpBlobChannel:
    """One TCP connection, both directions. Thread-safe send; single reader."""

    def __init__(self, sock: socket.socket):
        self._s = sock
        self._s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._wlock = threading.Lock()

    @classmethod
    def listen(cls, port: int, addr: str = "0.0.0.0", timeout: Optional[float] = None) -> "TcpBlobChannel":
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((addr, port))
        srv.listen(1)
        srv.settimeout(timeout)
        conn, _ = srv.accept()
        srv.close()
        conn.settimeout(None)
        return cls(conn)

    @classmethod
    def connect(cls, host: str, port: int, timeout: float = 30.0) -> "TcpBlobChannel":
        s = socket.create_connection((host, port), timeout=timeout)
        s.settimeout(None)
        return cls(s)

    @staticmethod
    def pair() -> Tuple["TcpBlobChannel", "TcpBlobChannel"]:
        a, b = socket.socketpair()
        return TcpBlobChannel.__new__(TcpBlobChannel)._init_unix(a), TcpBlobChannel.__new__(TcpBlobChannel)._init_unix(b)

    def _init_unix(self, s: socket.socket) -> "TcpBlobChannel":
        self._s = s
        self._wlock = threading.Lock()
        return self

    def send(self, key: str, payload: Buf, hot: bool = False) -> None:
        k = key.encode()
        mv = memoryview(payload).cast("B")
        hdr = _HDR.pack(_MAGIC, 1 if hot else 0, len(k), mv.nbytes)
        with self._wlock:
            self._s.sendall(hdr + k)
            self._s.sendall(mv)

    def _recv_exact(self, n: int) -> bytes:
        buf = bytearray(n)
        view = memoryview(buf)
        got = 0
        while got < n:
            r = self._s.recv_into(view[got:], n - got)
            if r == 0:
                raise ConnectionError("peer closed")
            got += r
        return bytes(buf)

    def recv(self, timeout: Optional[float] = None) -> Tuple[str, bytes]:
        self._s.settimeout(timeout)
        try:
            magic, _flags, klen, plen = _HDR.unpack(self._recv_exact(_HDR.size))
        finally:
            self._s.settimeout(None)
        if magic != _MAGIC:
            raise ValueError("bad frame magic")
        key = self._recv_exact(klen).decode()
        return key, self._recv_exact(plen)

    def close(self) -> None:
        try:
            self._s.close()
        except OSError:
            pass
