"""
TCP Transport Implementation.

Standard TCP socket wrapper providing the baseline transport
for comparison with RDMA-based transports.
"""

import socket
import time
import select
from typing import Optional

from .transport_base import TransportBase, TransportType


class TCPTransport(TransportBase):
    """
    TCP transport using standard Berkeley sockets.

    This serves as the baseline transport for performance comparisons.
    Expected latency: ~1ms (depending on network conditions)
    """

    def __init__(self):
        super().__init__("TCP Socket", TransportType.TCP)
        self._socket: Optional[socket.socket] = None
        self._host: str = ""
        self._port: int = 0
        self._buffer_size = 65536  # 64KB default buffer

    def connect(self, host: str, port: int, **kwargs) -> bool:
        """
        Establish TCP connection.

        Args:
            host: Remote hostname or IP
            port: Remote port
            **kwargs:
                timeout: Connection timeout in seconds (default: 10)
                buffer_size: Socket buffer size (default: 65536)
                nodelay: Disable Nagle's algorithm (default: True)

        Returns:
            True if connected successfully
        """
        timeout = kwargs.get('timeout', 10.0)
        buffer_size = kwargs.get('buffer_size', self._buffer_size)
        nodelay = kwargs.get('nodelay', True)

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(timeout)

            # Set socket options for low latency
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_size)

            if nodelay:
                self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            self._socket.connect((host, port))
            self._connected = True
            self._host = host
            self._port = port
            self._buffer_size = buffer_size

            self._config.update({
                "host": host,
                "port": port,
                "buffer_size": buffer_size,
                "nodelay": nodelay,
            })

            return True

        except (socket.error, OSError) as e:
            self._connected = False
            self._socket = None
            raise ConnectionError(f"TCP connect failed: {e}")

    def disconnect(self) -> None:
        """Close TCP connection."""
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            try:
                self._socket.close()
            except socket.error:
                pass
            self._socket = None
        self._connected = False

    def send(self, data: bytes) -> int:
        """
        Send data over TCP.

        Args:
            data: Bytes to send

        Returns:
            Number of bytes sent
        """
        if not self._connected or not self._socket:
            raise ConnectionError("Not connected")

        try:
            start = time.perf_counter()
            total_sent = 0
            while total_sent < len(data):
                sent = self._socket.send(data[total_sent:])
                if sent == 0:
                    raise IOError("Connection closed")
                total_sent += sent

            latency = time.perf_counter() - start
            self.metrics.bytes_sent += total_sent
            self.metrics.update_latency(latency)
            return total_sent

        except socket.error as e:
            self.metrics.send_errors += 1
            raise IOError(f"TCP send failed: {e}")

    def recv(self, size: int, timeout: Optional[float] = None) -> bytes:
        """
        Receive data over TCP.

        Args:
            size: Maximum bytes to receive
            timeout: Optional timeout in seconds

        Returns:
            Received bytes
        """
        if not self._connected or not self._socket:
            raise ConnectionError("Not connected")

        try:
            if timeout is not None:
                # Use select for timeout
                ready = select.select([self._socket], [], [], timeout)
                if not ready[0]:
                    raise TimeoutError(f"TCP recv timeout after {timeout}s")

            start = time.perf_counter()
            data = self._socket.recv(size)
            latency = time.perf_counter() - start

            if not data:
                raise IOError("Connection closed by remote")

            self.metrics.bytes_received += len(data)
            self.metrics.update_latency(latency)
            return data

        except socket.timeout:
            raise TimeoutError("TCP recv timeout")
        except socket.error as e:
            self.metrics.recv_errors += 1
            raise IOError(f"TCP recv failed: {e}")

    def is_available(self) -> bool:
        """TCP is always available."""
        return True

    def listen(self, port: int, backlog: int = 5) -> None:
        """
        Start listening for incoming connections.

        Args:
            port: Port to listen on
            backlog: Connection queue size
        """
        if self._socket:
            self.disconnect()

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('', port))
        self._socket.listen(backlog)
        self._port = port

    def accept(self, timeout: Optional[float] = None) -> 'TCPTransport':
        """
        Accept incoming connection.

        Args:
            timeout: Accept timeout in seconds

        Returns:
            New TCPTransport for the accepted connection
        """
        if not self._socket:
            raise ConnectionError("Not listening")

        if timeout is not None:
            self._socket.settimeout(timeout)

        client_sock, addr = self._socket.accept()
        client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        transport = TCPTransport()
        transport._socket = client_sock
        transport._connected = True
        transport._host = addr[0]
        transport._port = addr[1]
        transport._config = {
            "host": addr[0],
            "port": addr[1],
            "accepted": True,
        }

        return transport

    def set_keepalive(self, enable: bool = True, idle: int = 60,
                      interval: int = 10, count: int = 5) -> None:
        """
        Configure TCP keepalive.

        Args:
            enable: Enable keepalive
            idle: Seconds before sending keepalive probes
            interval: Seconds between probes
            count: Number of probes before dropping connection
        """
        if not self._socket:
            return

        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1 if enable else 0)

        if enable:
            # Linux-specific keepalive options
            try:
                self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, idle)
                self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval)
                self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, count)
            except (AttributeError, OSError):
                pass  # Not available on all platforms
