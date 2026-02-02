"""
Soft-RoCE Transport Implementation.

RDMA over Converged Ethernet using rdma-core verbs API.
Provides kernel-bypass data transfer with RDMA semantics.
"""

import os
import subprocess
import time
from typing import Optional, Dict, Any, Tuple

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
        self._qp = None
        self._mr = None
        self._buffer = None
        self._buffer_size = 4096  # 4KB default buffer

        # Remote connection info
        self._remote_qpn = 0
        self._remote_lid = 0
        self._remote_gid = None

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
            host: Remote hostname or IP (for CM connection)
            port: Remote port (used for out-of-band QP exchange)
            **kwargs:
                buffer_size: Size of RDMA buffer (default: 4096)
                timeout: Connection timeout in seconds

        Returns:
            True if connected successfully
        """
        if not self._verbs_available:
            raise ConnectionError("pyverbs not available - install rdma-core")

        buffer_size = kwargs.get('buffer_size', self._buffer_size)
        timeout = kwargs.get('timeout', 10.0)

        try:
            # Import verbs modules
            d = self._pyverbs['device']
            pd_mod = self._pyverbs['pd']
            cq_mod = self._pyverbs['cq']
            qp_mod = self._pyverbs['qp']
            mr_mod = self._pyverbs['mr']
            e = self._pyverbs['enums']

            # Open device context
            devices = d.get_device_list()
            for dev in devices:
                if dev.name.decode() == self._device:
                    self._context = d.Context(name=dev.name)
                    break

            if not self._context:
                raise ConnectionError(f"RDMA device {self._device} not found")

            # Create protection domain
            self._pd = pd_mod.PD(self._context)

            # Create completion queue
            self._cq = cq_mod.CQ(self._context, 100)

            # Create queue pair
            qp_init = qp_mod.QPInitAttr(
                qp_type=e.IBV_QPT_RC,
                scq=self._cq,
                rcq=self._cq,
                cap=qp_mod.QPCap(max_send_wr=16, max_recv_wr=16,
                                  max_send_sge=1, max_recv_sge=1)
            )
            self._qp = qp_mod.QP(self._pd, qp_init)

            # Allocate and register memory
            self._buffer_size = buffer_size
            self._buffer = bytearray(buffer_size)
            self._mr = mr_mod.MR(
                self._pd,
                self._buffer,
                e.IBV_ACCESS_LOCAL_WRITE | e.IBV_ACCESS_REMOTE_WRITE | e.IBV_ACCESS_REMOTE_READ
            )

            # Exchange QP info with remote (via TCP out-of-band)
            local_info = self._get_local_qp_info()
            remote_info = self._exchange_qp_info(host, port, local_info, timeout)

            if not remote_info:
                raise ConnectionError("Failed to exchange QP info")

            # Transition QP to RTR and RTS states
            self._transition_qp_to_rtr(remote_info)
            self._transition_qp_to_rts()

            self._connected = True
            self._config.update({
                "device": self._device,
                "host": host,
                "port": port,
                "buffer_size": buffer_size,
                "local_qpn": self._qp.qp_num,
                "remote_qpn": remote_info['qpn'],
            })

            return True

        except Exception as e:
            self.disconnect()
            raise ConnectionError(f"RoCE connect failed: {e}")

    def _get_local_qp_info(self) -> Dict[str, Any]:
        """Get local QP information for exchange."""
        e = self._pyverbs['enums']

        # Get port attributes
        port_attr = self._context.query_port(1)

        # Get GID
        gid = self._context.query_gid(1, 0)

        return {
            'qpn': self._qp.qp_num,
            'lid': port_attr.lid,
            'gid': gid.gid,
            'rkey': self._mr.rkey,
            'addr': self._mr.buf,
        }

    def _exchange_qp_info(self, host: str, port: int,
                          local_info: Dict, timeout: float) -> Optional[Dict]:
        """
        Exchange QP info with remote peer via TCP.

        In production, this would use RDMA CM. This simplified version
        uses TCP for out-of-band QP exchange.
        """
        import socket
        import json

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))

            # Send local info
            local_data = json.dumps({
                'qpn': local_info['qpn'],
                'lid': local_info['lid'],
                'gid': local_info['gid'].hex() if hasattr(local_info['gid'], 'hex') else str(local_info['gid']),
                'rkey': local_info['rkey'],
            }).encode()
            sock.sendall(len(local_data).to_bytes(4, 'big') + local_data)

            # Receive remote info
            size_data = sock.recv(4)
            if len(size_data) < 4:
                return None
            size = int.from_bytes(size_data, 'big')
            remote_data = sock.recv(size)
            remote_info = json.loads(remote_data.decode())

            sock.close()

            self._remote_qpn = remote_info['qpn']
            self._remote_lid = remote_info['lid']

            return remote_info

        except (socket.error, json.JSONDecodeError) as e:
            return None

    def _transition_qp_to_rtr(self, remote_info: Dict) -> None:
        """Transition QP from INIT to RTR state."""
        e = self._pyverbs['enums']
        qp_mod = self._pyverbs['qp']

        # First transition to INIT
        init_attr = qp_mod.QPAttr(
            qp_state=e.IBV_QPS_INIT,
            pkey_index=0,
            port_num=1,
            qp_access_flags=(e.IBV_ACCESS_LOCAL_WRITE |
                            e.IBV_ACCESS_REMOTE_WRITE |
                            e.IBV_ACCESS_REMOTE_READ)
        )
        self._qp.to_init(init_attr)

        # Then transition to RTR
        rtr_attr = qp_mod.QPAttr(
            qp_state=e.IBV_QPS_RTR,
            path_mtu=e.IBV_MTU_1024,
            dest_qp_num=remote_info['qpn'],
            rq_psn=0,
            max_dest_rd_atomic=1,
            min_rnr_timer=12,
        )
        # Set AH attr for path
        rtr_attr.ah_attr.dlid = remote_info['lid']
        rtr_attr.ah_attr.sl = 0
        rtr_attr.ah_attr.src_path_bits = 0
        rtr_attr.ah_attr.port_num = 1

        self._qp.to_rtr(rtr_attr)

    def _transition_qp_to_rts(self) -> None:
        """Transition QP from RTR to RTS state."""
        e = self._pyverbs['enums']
        qp_mod = self._pyverbs['qp']

        rts_attr = qp_mod.QPAttr(
            qp_state=e.IBV_QPS_RTS,
            sq_psn=0,
            timeout=14,
            retry_cnt=7,
            rnr_retry=7,
            max_rd_atomic=1,
        )
        self._qp.to_rts(rts_attr)

    def disconnect(self) -> None:
        """Close RDMA connection and free resources."""
        # Clean up in reverse order of allocation
        if self._mr:
            try:
                self._mr.close()
            except Exception:
                pass
            self._mr = None

        if self._qp:
            try:
                self._qp.close()
            except Exception:
                pass
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
