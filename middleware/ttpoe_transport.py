"""
Tesla TTPoe Transport Implementation.

Time-Triggered Protocol over Ethernet from Tesla's Dojo supercomputer.
Provides ultra-low latency (~1-2us) transport via kernel modules.
"""

import os
import subprocess
import time
import ctypes
import socket
from typing import Optional, Dict, Any, List

from .transport_base import TransportBase, TransportType


class TTPoeTransport(TransportBase):
    """
    TTPoe transport using Tesla's kernel modules.

    Uses modttpoe.ko and optionally modttpip.ko for ultra-low latency
    communication. Expected latency: ~1-2us.

    Note: Requires kernel modules to be built and loaded. This transport
    exposes a character device interface for data transfer.
    """

    # Module paths (relative to ttpoe source directory)
    MODTTPOE = "modttpoe/modttpoe.ko"
    MODTTPIP = "modttpip/modttpip.ko"

    # procfs interface
    PROC_STATE = "/proc/net/ttpoe/state"
    PROC_STATS = "/proc/net/ttpoe/stats"

    # Character device
    CHAR_DEVICE = "/dev/ttpoe"

    def __init__(self, device: str = "eth0", ttpoe_dir: Optional[str] = None):
        """
        Initialize TTPoe transport.

        Args:
            device: Network interface to use
            ttpoe_dir: Path to ttpoe source directory (for module loading)
        """
        super().__init__("Tesla TTPoe", TransportType.TTPOE)
        self._device = device
        self._ttpoe_dir = ttpoe_dir or os.environ.get('TTPOE_DIR', '/opt/ttpoe')
        self._fd: Optional[int] = None
        self._remote_mac: Optional[str] = None
        self._virtual_circuit: int = 0
        self._modules_loaded: bool = False
        self._use_socket_fallback: bool = False

        # Fallback TCP socket for testing without kernel module
        self._fallback_socket: Optional[socket.socket] = None

    def is_available(self) -> bool:
        """
        Check if TTPoe is available on this system.

        Checks for:
        1. TTPoe kernel module loaded OR module files exist
        2. Character device available (if module loaded)
        """
        # Check if module is already loaded
        if self._check_module_loaded():
            return True

        # Check if module files exist
        modttpoe_path = os.path.join(self._ttpoe_dir, self.MODTTPOE)
        if os.path.exists(modttpoe_path):
            return True

        return False

    def _check_module_loaded(self) -> bool:
        """Check if TTPoe kernel module is loaded."""
        try:
            result = subprocess.run(
                ['lsmod'],
                capture_output=True,
                text=True
            )
            return 'modttpoe' in result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def load_modules(self, dst_mac: Optional[str] = None,
                     virtual_circuit: int = 0,
                     verbose: int = 1) -> bool:
        """
        Load TTPoe kernel modules.

        Args:
            dst_mac: Destination MAC address (for point-to-point)
            virtual_circuit: Virtual circuit ID
            verbose: Debug verbosity level (0-3)

        Returns:
            True if modules loaded successfully
        """
        if self._check_module_loaded():
            self._modules_loaded = True
            return True

        modttpoe_path = os.path.join(self._ttpoe_dir, self.MODTTPOE)

        if not os.path.exists(modttpoe_path):
            return False

        try:
            cmd = ['insmod', modttpoe_path, f'dev={self._device}', f'verbose={verbose}']

            if dst_mac:
                cmd.append(f'dst={dst_mac}')
            if virtual_circuit:
                cmd.append(f'vc={virtual_circuit}')

            subprocess.run(cmd, check=True)
            self._modules_loaded = True
            self._remote_mac = dst_mac
            self._virtual_circuit = virtual_circuit

            return True

        except subprocess.CalledProcessError as e:
            return False

    def unload_modules(self) -> bool:
        """Unload TTPoe kernel modules."""
        if not self._check_module_loaded():
            self._modules_loaded = False
            return True

        try:
            subprocess.run(['rmmod', 'modttpoe'], check=True)
            self._modules_loaded = False
            return True
        except subprocess.CalledProcessError:
            return False

    def connect(self, host: str, port: int, **kwargs) -> bool:
        """
        Establish TTPoe connection.

        Args:
            host: Remote hostname or IP (used for MAC resolution)
            port: Port number (used for virtual circuit mapping)
            **kwargs:
                dst_mac: Explicit destination MAC (overrides host resolution)
                virtual_circuit: Virtual circuit ID
                verbose: Module debug level
                use_fallback: Use TCP fallback if module unavailable

        Returns:
            True if connected successfully
        """
        dst_mac = kwargs.get('dst_mac')
        virtual_circuit = kwargs.get('virtual_circuit', self._virtual_circuit)
        verbose = kwargs.get('verbose', 1)
        use_fallback = kwargs.get('use_fallback', True)

        # Resolve MAC address if not provided
        if not dst_mac:
            dst_mac = self._resolve_mac(host)

        # Try to load modules if not already loaded
        if not self._modules_loaded and not self._check_module_loaded():
            if not self.load_modules(dst_mac, virtual_circuit, verbose):
                if use_fallback:
                    return self._connect_fallback(host, port, **kwargs)
                raise ConnectionError("Failed to load TTPoe modules")

        # Open character device
        try:
            if os.path.exists(self.CHAR_DEVICE):
                self._fd = os.open(self.CHAR_DEVICE, os.O_RDWR)
            else:
                if use_fallback:
                    return self._connect_fallback(host, port, **kwargs)
                raise ConnectionError(f"TTPoe device {self.CHAR_DEVICE} not found")

            self._connected = True
            self._config.update({
                "device": self._device,
                "host": host,
                "port": port,
                "dst_mac": dst_mac,
                "virtual_circuit": virtual_circuit,
                "mode": "ttpoe",
            })

            return True

        except OSError as e:
            if use_fallback:
                return self._connect_fallback(host, port, **kwargs)
            raise ConnectionError(f"Failed to open TTPoe device: {e}")

    def _connect_fallback(self, host: str, port: int, **kwargs) -> bool:
        """Connect using TCP fallback when TTPoe is unavailable."""
        try:
            self._fallback_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._fallback_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self._fallback_socket.connect((host, port))

            self._connected = True
            self._use_socket_fallback = True
            self._config.update({
                "device": self._device,
                "host": host,
                "port": port,
                "mode": "tcp_fallback",
            })

            return True

        except socket.error as e:
            raise ConnectionError(f"TTPoe fallback connect failed: {e}")

    def _resolve_mac(self, host: str) -> Optional[str]:
        """Resolve IP address to MAC address using ARP."""
        try:
            # Ping to populate ARP cache
            subprocess.run(
                ['ping', '-c', '1', '-W', '1', host],
                capture_output=True
            )

            # Read ARP cache
            result = subprocess.run(
                ['arp', '-n', host],
                capture_output=True,
                text=True
            )

            # Parse MAC from output
            for line in result.stdout.split('\n'):
                if host in line:
                    parts = line.split()
                    for part in parts:
                        if ':' in part and len(part) == 17:
                            return part

        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return None

    def disconnect(self) -> None:
        """Close TTPoe connection."""
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None

        if self._fallback_socket:
            try:
                self._fallback_socket.close()
            except socket.error:
                pass
            self._fallback_socket = None

        self._connected = False
        self._use_socket_fallback = False

    def send(self, data: bytes) -> int:
        """
        Send data over TTPoe.

        Args:
            data: Bytes to send

        Returns:
            Number of bytes sent
        """
        if not self._connected:
            raise ConnectionError("Not connected")

        if self._use_socket_fallback and self._fallback_socket:
            return self._send_fallback(data)

        if self._fd is None:
            raise ConnectionError("TTPoe device not open")

        try:
            start = time.perf_counter()
            sent = os.write(self._fd, data)
            latency = time.perf_counter() - start

            self.metrics.bytes_sent += sent
            self.metrics.update_latency(latency)

            return sent

        except OSError as e:
            self.metrics.send_errors += 1
            raise IOError(f"TTPoe send failed: {e}")

    def _send_fallback(self, data: bytes) -> int:
        """Send using TCP fallback."""
        try:
            start = time.perf_counter()
            self._fallback_socket.sendall(data)
            latency = time.perf_counter() - start

            self.metrics.bytes_sent += len(data)
            self.metrics.update_latency(latency)

            return len(data)

        except socket.error as e:
            self.metrics.send_errors += 1
            raise IOError(f"TTPoe fallback send failed: {e}")

    def recv(self, size: int, timeout: Optional[float] = None) -> bytes:
        """
        Receive data over TTPoe.

        Args:
            size: Maximum bytes to receive
            timeout: Optional timeout in seconds

        Returns:
            Received bytes
        """
        if not self._connected:
            raise ConnectionError("Not connected")

        if self._use_socket_fallback and self._fallback_socket:
            return self._recv_fallback(size, timeout)

        if self._fd is None:
            raise ConnectionError("TTPoe device not open")

        try:
            # Note: Character device doesn't support select() easily
            # In production, use poll/epoll or async I/O
            start = time.perf_counter()
            data = os.read(self._fd, size)
            latency = time.perf_counter() - start

            self.metrics.bytes_received += len(data)
            self.metrics.update_latency(latency)

            return data

        except OSError as e:
            self.metrics.recv_errors += 1
            raise IOError(f"TTPoe recv failed: {e}")

    def _recv_fallback(self, size: int, timeout: Optional[float]) -> bytes:
        """Receive using TCP fallback."""
        try:
            import select

            if timeout is not None:
                ready = select.select([self._fallback_socket], [], [], timeout)
                if not ready[0]:
                    raise TimeoutError(f"TTPoe fallback recv timeout after {timeout}s")

            start = time.perf_counter()
            data = self._fallback_socket.recv(size)
            latency = time.perf_counter() - start

            if not data:
                raise IOError("Connection closed")

            self.metrics.bytes_received += len(data)
            self.metrics.update_latency(latency)

            return data

        except socket.error as e:
            self.metrics.recv_errors += 1
            raise IOError(f"TTPoe fallback recv failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get TTPoe statistics from procfs."""
        stats = {}

        try:
            if os.path.exists(self.PROC_STATS):
                with open(self.PROC_STATS, 'r') as f:
                    for line in f:
                        if ':' in line:
                            key, value = line.strip().split(':', 1)
                            stats[key.strip()] = value.strip()
        except (IOError, OSError):
            pass

        return stats

    def get_state(self) -> str:
        """Get TTPoe connection state from procfs."""
        try:
            if os.path.exists(self.PROC_STATE):
                with open(self.PROC_STATE, 'r') as f:
                    return f.read().strip()
        except (IOError, OSError):
            pass

        return "unknown"

    @staticmethod
    def build_modules(ttpoe_dir: str) -> bool:
        """
        Build TTPoe kernel modules.

        Args:
            ttpoe_dir: Path to ttpoe source directory

        Returns:
            True if build successful
        """
        try:
            subprocess.run(
                ['make', 'all'],
                cwd=ttpoe_dir,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def run_tests(ttpoe_dir: str, target: int = 2, verbose: bool = True) -> bool:
        """
        Run TTPoe unit tests.

        Args:
            ttpoe_dir: Path to ttpoe source directory
            target: Test target level
            verbose: Enable verbose output

        Returns:
            True if tests pass
        """
        try:
            cmd = [os.path.join(ttpoe_dir, 'tests/run.sh'), f'--target={target}']
            if verbose:
                cmd.append('-v')

            subprocess.run(cmd, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def configure_peer(self, peer_mac: str, peer_ip: Optional[str] = None,
                       virtual_circuit: int = 0) -> bool:
        """
        Configure a TTPoe peer.

        Args:
            peer_mac: Peer MAC address
            peer_ip: Optional peer IP (for gateway module)
            virtual_circuit: Virtual circuit ID

        Returns:
            True if configuration successful
        """
        # In production, this would write to procfs or use ioctl
        self._remote_mac = peer_mac
        self._virtual_circuit = virtual_circuit

        self._config.update({
            "peer_mac": peer_mac,
            "peer_ip": peer_ip,
            "virtual_circuit": virtual_circuit,
        })

        return True
