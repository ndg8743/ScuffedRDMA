# Portions adapted from autoscriptlabs/libmesh-rdma (MIT).
# See LICENSE-THIRD-PARTY.
"""
Binary TCP handshake for RDMA QP bootstrap.

Ports `mesh_rdma_qp_info_t`, `mesh_rdma_send_handshake`, and
`mesh_rdma_accept_handshake` from libmesh-rdma's `src/mesh_rdma_core.c`.

Replaces the JSON-based handshake previously in `roce_transport.py`.
Two advantages:

1. Fixed-size wire format (64 bytes) — there is no length field for a
   crafted peer to manipulate, so the unbounded-recv class of bug is
   gone by construction.

2. Network byte order + explicit struct packing — interoperates with
   libmesh-rdma's C code if the two ever need to talk to each other.

The module is pure sockets. It does not import pyverbs.
"""

from __future__ import annotations

import ipaddress
import select
import socket
import struct
import time
from dataclasses import dataclass, field


# Wire format (matches libmesh-rdma mesh_rdma_qp_info_t layout).
# Network byte order throughout.
#
#   !       big-endian
#   I       qpn            (4)
#   I       psn            (4)
#   16s     gid            (16)
#   I       ip             (4, IPv4 in network order)
#   I       gid_index      (4)
#   I       mtu            (4)
#   7I      padding        (28)
#                          = 64 bytes total
_WIRE_FMT = "!II16sIII7I"
WIRE_SIZE = struct.calcsize(_WIRE_FMT)
assert WIRE_SIZE == 64, f"QpInfo wire size drift: {WIRE_SIZE}"


@dataclass
class QpInfo:
    """RDMA queue-pair bootstrap info.

    All fields are required; there is no optional / default framing
    precisely because the wire format is fixed size.
    """
    qpn: int
    psn: int
    gid: bytes      # exactly 16 bytes
    ip: str         # IPv4 dotted-quad
    gid_index: int
    mtu: int

    def __post_init__(self) -> None:
        if len(self.gid) != 16:
            raise ValueError(f"QpInfo.gid must be 16 bytes, got {len(self.gid)}")
        # Validate IP; raises ValueError on garbage.
        ipaddress.IPv4Address(self.ip)

    def pack(self) -> bytes:
        ip_int = int(ipaddress.IPv4Address(self.ip))
        return struct.pack(
            _WIRE_FMT,
            self.qpn & 0xFFFFFFFF,
            self.psn & 0xFFFFFFFF,
            self.gid,
            ip_int,
            self.gid_index & 0xFFFFFFFF,
            self.mtu & 0xFFFFFFFF,
            0, 0, 0, 0, 0, 0, 0,
        )

    @classmethod
    def unpack(cls, buf: bytes) -> "QpInfo":
        if len(buf) != WIRE_SIZE:
            raise ValueError(f"QpInfo payload must be {WIRE_SIZE} bytes, got {len(buf)}")
        qpn, psn, gid, ip_int, gid_index, mtu, *_pad = struct.unpack(_WIRE_FMT, buf)
        return cls(
            qpn=qpn,
            psn=psn,
            gid=gid,
            ip=str(ipaddress.IPv4Address(ip_int)),
            gid_index=gid_index,
            mtu=mtu,
        )


class HandshakeError(RuntimeError):
    """Raised when the TCP bootstrap fails for any reason."""


def _recv_exact(sock: socket.socket, n: int, deadline: float) -> bytes:
    """Receive exactly `n` bytes or raise HandshakeError on timeout."""
    out = bytearray()
    while len(out) < n:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise HandshakeError(f"recv timed out after {len(out)}/{n} bytes")
        sock.settimeout(remaining)
        try:
            chunk = sock.recv(n - len(out))
        except socket.timeout as exc:
            raise HandshakeError("recv timed out") from exc
        if not chunk:
            raise HandshakeError(f"peer closed after {len(out)}/{n} bytes")
        out.extend(chunk)
    return bytes(out)


def send_handshake(host: str, port: int, local: QpInfo,
                   retries: int = 50, delay: float = 0.1,
                   timeout: float = 10.0) -> QpInfo:
    """Client-side handshake.

    Connects to `(host, port)`, sends `local.pack()`, reads 64 bytes
    back, and returns the peer's unpacked QpInfo. Retries the connect
    up to `retries` times with `delay` seconds between attempts — this
    matches libmesh-rdma's behavior of tolerating the peer not being
    ready yet during parallel startup.
    """
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            try:
                sock.connect((host, port))
                sock.sendall(local.pack())
                deadline = time.monotonic() + timeout
                remote_buf = _recv_exact(sock, WIRE_SIZE, deadline)
                return QpInfo.unpack(remote_buf)
            finally:
                sock.close()
        except (ConnectionRefusedError, socket.timeout) as exc:
            last_err = exc
            time.sleep(delay)
        except (OSError, ValueError, HandshakeError) as exc:
            # ValueError here means unpack failed — peer sent garbage.
            # Do not retry; propagate immediately.
            raise HandshakeError(f"handshake failed: {exc}") from exc
    raise HandshakeError(
        f"could not connect to {host}:{port} after {retries} attempts: {last_err}"
    )


def accept_handshake(listen_port: int, local: QpInfo,
                     timeout: float = 10.0,
                     bind_host: str = "0.0.0.0") -> QpInfo:
    """Server-side handshake.

    Binds a listening socket, accepts one connection, reads 64 bytes,
    echoes `local.pack()`, and returns the peer's unpacked QpInfo.
    """
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((bind_host, listen_port))
        srv.listen(1)
        srv.settimeout(timeout)
        try:
            conn, _addr = srv.accept()
        except socket.timeout as exc:
            raise HandshakeError(
                f"no peer connected on {bind_host}:{listen_port} within {timeout}s"
            ) from exc
    finally:
        srv.close()

    try:
        deadline = time.monotonic() + timeout
        remote_buf = _recv_exact(conn, WIRE_SIZE, deadline)
        conn.sendall(local.pack())
        return QpInfo.unpack(remote_buf)
    except (OSError, ValueError, HandshakeError) as exc:
        raise HandshakeError(f"accept handshake failed: {exc}") from exc
    finally:
        conn.close()
