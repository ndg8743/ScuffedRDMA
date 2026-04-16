"""
Soft-RoCE Transport Implementation.

RDMA over Converged Ethernet using the rdma-core verbs API.
Provides kernel-bypass data transfer with RDMA semantics.

Bootstrap and QP state machine are delegated to three sibling modules:

    rdma_gid_discovery.find_ipv4_gid_index  — picks the right GID
    rdma_bootstrap.send_handshake/accept    — fixed 64-byte TCP protocol
    rdma_qp_state_machine.QueuePair         — retrying state machine
"""

import os
import subprocess
import time
from typing import Optional, Dict, Any, Tuple

from .rdma_bootstrap import HandshakeError, QpInfo, accept_handshake, send_handshake
from .rdma_gid_discovery import find_ipv4_gid_index
from .rdma_qp_state_machine import QueuePair, QueuePairError
from .transport_base import TransportBase, TransportType


class RoCETransport(TransportBase):
    """
    Soft-RoCE transport using RDMA verbs.

    Uses the rxe (RDMA over Ethernet) kernel module with rdma-core
    for RDMA operations. Expected latency: ~190us with Soft-RoCE.

    Note: This implementation provides a socket-like interface over RDMA
    for compatibility with the middleware layer. For maximum performance,
    direct verbs programming may be preferred.
    """

    # RDMA verbs are optional - gracefully degrade if not available
    _verbs_available = False
    _pyverbs = None

    def __init__(self, device: str = "rxe0"):
        """
        Initialize RoCE transport.

        Args:
            device: RDMA device name (default: rxe0 for Soft-RoCE)
        """
        super().__init__("Soft-RoCE", TransportType.ROCE)
        self._device = device
        self._context = None
        self._pd = None
        self._cq = None
        self._qp_wrapper: Optional[QueuePair] = None
        self._qp = None
        self._mr = None
        self._buffer = None
        self._buffer_size = 4096  # 4KB default buffer

        # Remote connection info (populated after handshake)
        self._remote_info: Optional[QpInfo] = None
        self._local_gid_index: int = 0

        # Try to import pyverbs
        self._try_import_verbs()

    @classmethod
    def _try_import_verbs(cls):
        """Attempt to import pyverbs library."""
        if cls._verbs_available:
            return

        try:
            import pyverbs.device as d
            import pyverbs.pd as pd
            import pyverbs.cq as cq
            import pyverbs.qp as qp
            import pyverbs.mr as mr
            import pyverbs.enums as e
            cls._pyverbs = {
                'device': d,
                'pd': pd,
                'cq': cq,
                'qp': qp,
                'mr': mr,
                'enums': e,
            }
            cls._verbs_available = True
        except ImportError:
            cls._verbs_available = False

    def is_available(self) -> bool:
        """
        Check if RoCE is available on this system.

        Checks for:
        1. rdma-core / pyverbs library
        2. rxe kernel module loaded
        3. RDMA device present
        """
        # Check pyverbs availability
        if not self._verbs_available:
            return False

        # Check for rxe module
        try:
            result = subprocess.run(
                ['lsmod'],
                capture_output=True,
                text=True
            )
            if 'rdma_rxe' not in result.stdout:
                return False
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

        # Check for RDMA device
        try:
            result = subprocess.run(
                ['rdma', 'link', 'show'],
                capture_output=True,
                text=True
            )
            if self._device not in result.stdout:
                return False
        except (subprocess.SubprocessError, FileNotFoundError):
            pass  # rdma tool might not be available

        return True

    def connect(self, host: str, port: int, **kwargs) -> bool:
        """
        Establish RDMA connection.

        Args:
            host: Remote hostname or IP (peer of the TCP handshake)
            port: Remote port (TCP bootstrap listen port)
            **kwargs:
                buffer_size: Size of RDMA buffer (default: 4096)
                timeout: Connection timeout in seconds
                preferred_ip: IPv4 address to match against the RDMA GID
                  table, used to pick the right RoCEv2 GID index
                is_server: If True, accept a handshake on `port` instead
                  of connecting to `(host, port)`. Required for the
                  listening side of a cross-node bootstrap.

        Returns:
            True if connected successfully
        """
        if not self._verbs_available:
            raise ConnectionError("pyverbs not available - install rdma-core")

        buffer_size = kwargs.get('buffer_size', self._buffer_size)
        timeout = kwargs.get('timeout', 10.0)
        preferred_ip = kwargs.get('preferred_ip', None)
        is_server = kwargs.get('is_server', False)

        try:
            d = self._pyverbs['device']
            pd_mod = self._pyverbs['pd']
            cq_mod = self._pyverbs['cq']
            qp_mod = self._pyverbs['qp']
            mr_mod = self._pyverbs['mr']
            e = self._pyverbs['enums']

            devices = d.get_device_list()
            for dev in devices:
                if dev.name.decode() == self._device:
                    self._context = d.Context(name=dev.name)
                    break

            if not self._context:
                raise ConnectionError(f"RDMA device {self._device} not found")

            self._pd = pd_mod.PD(self._context)
            self._cq = cq_mod.CQ(self._context, 100)

            self._local_gid_index = find_ipv4_gid_index(
                self._context, port=1, preferred_ip=preferred_ip
            )

            cap = qp_mod.QPCap(max_send_wr=16, max_recv_wr=16,
                               max_send_sge=1, max_recv_sge=1)
            self._qp_wrapper = QueuePair(
                self._pd, self._cq, cap,
                port=1, gid_index=self._local_gid_index,
            )
            self._qp = self._qp_wrapper.qp

            self._buffer_size = buffer_size
            self._buffer = bytearray(buffer_size)
            self._mr = mr_mod.MR(
                self._pd,
                self._buffer,
                e.IBV_ACCESS_LOCAL_WRITE | e.IBV_ACCESS_REMOTE_WRITE | e.IBV_ACCESS_REMOTE_READ
            )

            local_qp_info = self._build_local_qp_info(preferred_ip)

            if is_server:
                remote = accept_handshake(port, local_qp_info, timeout=timeout)
            else:
                remote = send_handshake(host, port, local_qp_info, timeout=timeout)
            self._remote_info = remote

            self._qp_wrapper.to_init()
            self._qp_wrapper.to_rtr(remote)
            self._qp_wrapper.to_rts(local_psn=local_qp_info.psn)
            self._qp_wrapper.verify_rts()

            self._connected = True
            self._config.update({
                "device": self._device,
                "host": host,
                "port": port,
                "buffer_size": buffer_size,
                "local_qpn": self._qp.qp_num,
                "remote_qpn": remote.qpn,
                "gid_index": self._local_gid_index,
            })

            return True

        except (HandshakeError, QueuePairError) as exc:
            self.disconnect()
            raise ConnectionError(f"RoCE connect failed: {exc}")
        except Exception as exc:
            self.disconnect()
            raise ConnectionError(f"RoCE connect failed: {exc}")

    def _build_local_qp_info(self, preferred_ip: Optional[str]) -> QpInfo:
        """Populate a QpInfo from the live context + MR for the handshake."""
        e = self._pyverbs['enums']
        port_attr = self._context.query_port(1)

        gid_entry = self._context.query_gid(1, self._local_gid_index)
        raw_gid = getattr(gid_entry, "gid", gid_entry)
        if isinstance(raw_gid, str):
            cleaned = raw_gid.replace(":", "")
            raw_gid = bytes.fromhex(cleaned)
        elif isinstance(raw_gid, (bytes, bytearray)):
            raw_gid = bytes(raw_gid)
        else:
            raw_gid = bytes(str(raw_gid).encode())

        mtu_map = {
            getattr(e, "IBV_MTU_256", 1): 256,
            getattr(e, "IBV_MTU_512", 2): 512,
            getattr(e, "IBV_MTU_1024", 3): 1024,
            getattr(e, "IBV_MTU_2048", 4): 2048,
            getattr(e, "IBV_MTU_4096", 5): 4096,
        }
        mtu_bytes = mtu_map.get(getattr(port_attr, "active_mtu", 3), 1024)

        return QpInfo(
            qpn=self._qp.qp_num,
            psn=0,
            gid=raw_gid if len(raw_gid) == 16 else raw_gid.ljust(16, b"\x00")[:16],
            ip=preferred_ip or "0.0.0.0",
            gid_index=self._local_gid_index,
            mtu=mtu_bytes,
        )

    def disconnect(self) -> None:
        """Close RDMA connection and free resources."""
        # Clean up in reverse order of allocation
        if self._mr:
            try:
                self._mr.close()
            except Exception:
                pass
            self._mr = None

        if self._qp_wrapper:
            try:
                self._qp_wrapper.close()
            except Exception:
                pass
            self._qp_wrapper = None
        self._qp = None

        if self._cq:
            try:
                self._cq.close()
            except Exception:
                pass
            self._cq = None

        if self._pd:
            try:
                self._pd.close()
            except Exception:
                pass
            self._pd = None

        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

        self._buffer = None
        self._connected = False

    def send(self, data: bytes) -> int:
        """
        Send data using RDMA write.

        Args:
            data: Bytes to send

        Returns:
            Number of bytes sent
        """
        if not self._connected:
            raise ConnectionError("Not connected")

        if len(data) > self._buffer_size:
            raise ValueError(f"Data too large: {len(data)} > {self._buffer_size}")

        try:
            e = self._pyverbs['enums']

            start = time.perf_counter()

            # Copy data to registered buffer
            self._buffer[:len(data)] = data

            # Post send work request
            from pyverbs.wr import SendWR, SGE

            sge = SGE(self._mr.buf, len(data), self._mr.lkey)
            send_wr = SendWR(opcode=e.IBV_WR_SEND, num_sge=1, sg=[sge])

            self._qp.post_send(send_wr)

            # Poll for completion
            wcs = self._cq.poll(1)
            while not wcs:
                wcs = self._cq.poll(1)

            latency = time.perf_counter() - start
            self.metrics.bytes_sent += len(data)
            self.metrics.update_latency(latency)

            return len(data)

        except Exception as e:
            self.metrics.send_errors += 1
            raise IOError(f"RDMA send failed: {e}")

    def recv(self, size: int, timeout: Optional[float] = None) -> bytes:
        """
        Receive data using RDMA.

        Args:
            size: Maximum bytes to receive
            timeout: Optional timeout in seconds

        Returns:
            Received bytes
        """
        if not self._connected:
            raise ConnectionError("Not connected")

        try:
            e = self._pyverbs['enums']
            from pyverbs.wr import RecvWR, SGE

            start = time.perf_counter()

            # Post receive work request
            sge = SGE(self._mr.buf, min(size, self._buffer_size), self._mr.lkey)
            recv_wr = RecvWR(num_sge=1, sg=[sge])
            self._qp.post_recv(recv_wr)

            # Poll for completion with timeout
            deadline = time.time() + (timeout or 30.0)
            wcs = []
            while not wcs:
                if time.time() > deadline:
                    raise TimeoutError(f"RDMA recv timeout after {timeout}s")
                wcs = self._cq.poll(1)

            # Get received data
            received_size = wcs[0].byte_len
            data = bytes(self._buffer[:received_size])

            latency = time.perf_counter() - start
            self.metrics.bytes_received += received_size
            self.metrics.update_latency(latency)

            return data

        except TimeoutError:
            raise
        except Exception as e:
            self.metrics.recv_errors += 1
            raise IOError(f"RDMA recv failed: {e}")

    @staticmethod
    def setup_softroce(interface: str = "eth0") -> bool:
        """
        Set up Soft-RoCE on the specified interface.

        Args:
            interface: Network interface to use

        Returns:
            True if successful
        """
        try:
            # Load rdma_rxe module
            subprocess.run(['modprobe', 'rdma_rxe'], check=True)

            # Add rxe device
            subprocess.run(
                ['rdma', 'link', 'add', 'rxe0', 'type', 'rxe', 'netdev', interface],
                check=True
            )

            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def teardown_softroce() -> bool:
        """Remove Soft-RoCE configuration."""
        try:
            subprocess.run(['rdma', 'link', 'delete', 'rxe0'], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
