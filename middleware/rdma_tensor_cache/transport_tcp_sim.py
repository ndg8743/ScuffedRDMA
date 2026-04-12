"""
TCP simulation of RDMA semantics.

Provides the same API as PyverbsTransport (register_buffer, rdma_write,
rdma_read) over asyncio TCP sockets. Cross-platform, intended for
development on Windows and functional testing without RDMA hardware.
"""

import asyncio
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import numpy as np


# Wire protocol opcodes
_OP_WRITE = 0x01
_OP_READ_REQ = 0x02
_OP_READ_RESP = 0x03
_OP_SEND = 0x04

_HEADER_FMT = '<BIQQI'  # opcode, buf_id, offset, length, checksum
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)

# Upper bound for a single RDMA Read response. Defense-in-depth against
# a crafted peer reporting an 8-byte resp_len near 2^63.
MAX_RDMA_READ_BYTES = 1 * 1024 * 1024 * 1024  # 1 GB


@dataclass
class SimBuffer:
    """Simulated RDMA memory region."""
    name: str
    data: bytearray
    rkey: int

    def write(self, payload: bytes, offset: int = 0) -> None:
        self.data[offset:offset + len(payload)] = payload

    def read(self, length: int, offset: int = 0) -> bytes:
        return bytes(self.data[offset:offset + length])


class TcpSimTransport:
    """
    TCP-based simulation of RDMA one-sided operations.

    Maintains registered buffers locally and uses a simple wire protocol
    to simulate RDMA Write/Read semantics. Same API surface as
    PyverbsTransport for transparent backend swapping.
    """

    def __init__(self):
        self._buffers: Dict[str, SimBuffer] = {}
        self._rkey_counter = 1000
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._server: Optional[asyncio.Server] = None
        self._peer_reader: Optional[asyncio.StreamReader] = None
        self._peer_writer: Optional[asyncio.StreamWriter] = None
        self._connected = False
        self._bytes_sent = 0
        self._bytes_recv = 0
        self._ops = 0
        self._rkey_map: Dict[int, SimBuffer] = {}

        # Synchronous fallback for non-async usage
        self._sync_sock = None

    @staticmethod
    def is_available() -> bool:
        return True

    def register_buffer(self, name: str, size: int) -> SimBuffer:
        """
        Register a simulated RDMA buffer.

        Args:
            name: Buffer identifier.
            size: Buffer size in bytes.

        Returns:
            SimBuffer with an assigned rkey.
        """
        rkey = self._rkey_counter
        self._rkey_counter += 1
        buf = SimBuffer(name=name, data=bytearray(size), rkey=rkey)
        self._buffers[name] = buf
        self._rkey_map[rkey] = buf
        return buf

    # ---- Synchronous API (for compatibility with cache layer) ----

    def connect(self, host: str, port: int, timeout: float = 10.0) -> None:
        """Establish TCP connection (synchronous)."""
        self._sync_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sync_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._sync_sock.settimeout(timeout)
        self._sync_sock.connect((host, port))
        self._connected = True

    def listen(self, port: int, host: str = '0.0.0.0') -> None:
        """Start listening (synchronous)."""
        self._sync_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sync_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sync_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._sync_sock.bind((host, port))
        self._sync_sock.listen(1)

    def accept(self, timeout: float = 30.0) -> None:
        """Accept an incoming connection."""
        self._sync_sock.settimeout(timeout)
        conn, _ = self._sync_sock.accept()
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._sync_sock = conn
        self._connected = True

    def send(self, data: bytes) -> int:
        """Send raw data (RDMA Send simulation)."""
        header = struct.pack(_HEADER_FMT, _OP_SEND, 0, 0, len(data), 0)
        self._sync_sock.sendall(header + data)
        self._bytes_sent += len(data)
        self._ops += 1
        return len(data)

    def recv(self, size: int, timeout: Optional[float] = None) -> bytes:
        """Receive raw data."""
        if timeout is not None:
            self._sync_sock.settimeout(timeout)
        header = self._recv_exact(_HEADER_SIZE)
        opcode, buf_id, offset, length, cksum = struct.unpack(_HEADER_FMT, header)
        data = self._recv_exact(length)
        self._bytes_recv += length
        return data

    def rdma_write(self, local_buf: SimBuffer, remote_addr: int,
                   remote_rkey: int, length: int, local_offset: int = 0) -> None:
        """Simulate one-sided RDMA Write over TCP."""
        payload = local_buf.read(length, local_offset)
        header = struct.pack(_HEADER_FMT, _OP_WRITE, remote_rkey,
                             remote_addr, length, 0)
        self._sync_sock.sendall(header + payload)
        self._bytes_sent += length
        self._ops += 1

    def rdma_read(self, local_buf: SimBuffer, remote_addr: int,
                  remote_rkey: int, length: int, local_offset: int = 0) -> None:
        """Simulate one-sided RDMA Read over TCP."""
        header = struct.pack(_HEADER_FMT, _OP_READ_REQ, remote_rkey,
                             remote_addr, length, 0)
        self._sync_sock.sendall(header)

        resp_header = self._recv_exact(_HEADER_SIZE)
        _, _, _, resp_len, _ = struct.unpack(_HEADER_FMT, resp_header)
        data = self._recv_exact(resp_len)
        local_buf.write(data, local_offset)
        self._bytes_recv += resp_len
        self._ops += 1

    def handle_incoming(self) -> Optional[Tuple[int, bytes]]:
        """
        Process one incoming RDMA operation (server-side).

        Returns:
            (opcode, data) or None if no data available.
        """
        try:
            header = self._recv_exact(_HEADER_SIZE)
        except (OSError, TimeoutError):
            return None

        opcode, buf_id, offset, length, cksum = struct.unpack(_HEADER_FMT, header)

        if opcode == _OP_WRITE:
            data = self._recv_exact(length)
            buf = self._rkey_map.get(buf_id)
            if buf:
                buf.write(data, offset)
            return (_OP_WRITE, data)

        elif opcode == _OP_READ_REQ:
            buf = self._rkey_map.get(buf_id)
            if buf:
                data = buf.read(length, offset)
            else:
                data = b'\x00' * length
            resp = struct.pack(_HEADER_FMT, _OP_READ_RESP, buf_id, offset, len(data), 0)
            self._sync_sock.sendall(resp + data)
            return (_OP_READ_REQ, b'')

        elif opcode == _OP_SEND:
            data = self._recv_exact(length)
            return (_OP_SEND, data)

        return None

    def _recv_exact(self, size: int) -> bytes:
        """Receive exactly size bytes."""
        chunks = []
        remaining = size
        while remaining > 0:
            chunk = self._sync_sock.recv(min(remaining, 65536))
            if not chunk:
                raise ConnectionError("Connection closed")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b''.join(chunks)

    # ---- Async API ----

    async def async_connect(self, host: str, port: int) -> None:
        """Establish async TCP connection."""
        self._reader, self._writer = await asyncio.open_connection(host, port)
        self._connected = True

    async def async_listen(self, host: str = '0.0.0.0', port: int = 0):
        """Start async TCP server. Returns (host, port) it's bound to."""
        async def _on_connect(reader, writer):
            self._peer_reader = reader
            self._peer_writer = writer

        self._server = await asyncio.start_server(_on_connect, host, port)
        addr = self._server.sockets[0].getsockname()
        return addr

    async def async_rdma_write(self, local_buf: SimBuffer, remote_addr: int,
                               remote_rkey: int, length: int,
                               local_offset: int = 0) -> None:
        """Async RDMA Write simulation."""
        payload = local_buf.read(length, local_offset)
        header = struct.pack(_HEADER_FMT, _OP_WRITE, remote_rkey,
                             remote_addr, length, 0)
        self._writer.write(header + payload)
        await self._writer.drain()
        self._bytes_sent += length
        self._ops += 1

    async def async_rdma_read(self, local_buf: SimBuffer, remote_addr: int,
                              remote_rkey: int, length: int,
                              local_offset: int = 0) -> None:
        """Async RDMA Read simulation."""
        header = struct.pack(_HEADER_FMT, _OP_READ_REQ, remote_rkey,
                             remote_addr, length, 0)
        self._writer.write(header)
        await self._writer.drain()

        resp_header = await self._reader.readexactly(_HEADER_SIZE)
        _, _, _, resp_len, _ = struct.unpack(_HEADER_FMT, resp_header)
        if not 0 < resp_len <= MAX_RDMA_READ_BYTES:
            raise ValueError(
                f"RDMA Read response length out of range: {resp_len} "
                f"(max {MAX_RDMA_READ_BYTES})"
            )
        data = await self._reader.readexactly(resp_len)
        local_buf.write(data, local_offset)
        self._bytes_recv += resp_len
        self._ops += 1

    def close(self) -> None:
        """Close all connections and release resources."""
        if self._writer:
            try:
                self._writer.close()
            except Exception:
                pass
        if self._peer_writer:
            try:
                self._peer_writer.close()
            except Exception:
                pass
        if self._server:
            self._server.close()
        if self._sync_sock:
            try:
                self._sync_sock.close()
            except Exception:
                pass
        self._connected = False
        self._buffers.clear()
        self._rkey_map.clear()

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
