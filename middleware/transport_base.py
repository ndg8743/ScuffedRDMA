"""
Abstract base class for transport implementations.

All transports (TCP, RoCE, TTPoe) implement this interface to provide
a unified API for the middleware layer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
import time


class TransportType(Enum):
    """Supported transport types."""
    TCP = "tcp"
    ROCE = "roce"
    TTPOE = "ttpoe"


@dataclass
class TransportMetrics:
    """Container for transport performance metrics."""
    # Latency measurements (in seconds)
    min_latency: float = 0.0
    max_latency: float = 0.0
    avg_latency: float = 0.0
    latency_samples: int = 0

    # Throughput measurements
    bytes_sent: int = 0
    bytes_received: int = 0
    start_time: float = field(default_factory=time.time)

    # CPU usage (percentage)
    cpu_usage: float = 0.0

    # Error tracking
    send_errors: int = 0
    recv_errors: int = 0

    @property
    def elapsed_time(self) -> float:
        """Time since metrics collection started."""
        return time.time() - self.start_time

    @property
    def send_bandwidth_mbps(self) -> float:
        """Send bandwidth in Mbps."""
        elapsed = self.elapsed_time
        if elapsed > 0:
            return (self.bytes_sent * 8) / (elapsed * 1_000_000)
        return 0.0

    @property
    def recv_bandwidth_mbps(self) -> float:
        """Receive bandwidth in Mbps."""
        elapsed = self.elapsed_time
        if elapsed > 0:
            return (self.bytes_received * 8) / (elapsed * 1_000_000)
        return 0.0

    def update_latency(self, latency: float) -> None:
        """Update latency statistics with a new sample."""
        self.latency_samples += 1
        if self.latency_samples == 1:
            self.min_latency = latency
            self.max_latency = latency
            self.avg_latency = latency
        else:
            self.min_latency = min(self.min_latency, latency)
            self.max_latency = max(self.max_latency, latency)
            # Running average
            self.avg_latency = (
                self.avg_latency * (self.latency_samples - 1) + latency
            ) / self.latency_samples

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "latency": {
                "min_us": self.min_latency * 1_000_000,
                "max_us": self.max_latency * 1_000_000,
                "avg_us": self.avg_latency * 1_000_000,
                "samples": self.latency_samples,
            },
            "throughput": {
                "bytes_sent": self.bytes_sent,
                "bytes_received": self.bytes_received,
                "send_bandwidth_mbps": self.send_bandwidth_mbps,
                "recv_bandwidth_mbps": self.recv_bandwidth_mbps,
                "elapsed_sec": self.elapsed_time,
            },
            "cpu_usage_percent": self.cpu_usage,
            "errors": {
                "send": self.send_errors,
                "recv": self.recv_errors,
            },
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.min_latency = 0.0
        self.max_latency = 0.0
        self.avg_latency = 0.0
        self.latency_samples = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.start_time = time.time()
        self.cpu_usage = 0.0
        self.send_errors = 0
        self.recv_errors = 0


class TransportBase(ABC):
    """
    Abstract base class for transport implementations.

    All transport types must implement these methods to provide
    a consistent interface for the middleware layer.
    """

    def __init__(self, name: str, transport_type: TransportType):
        """
        Initialize transport base.

        Args:
            name: Human-readable transport name
            transport_type: Type of transport (TCP, RoCE, TTPoe)
        """
        self.name = name
        self.transport_type = transport_type
        self.metrics = TransportMetrics()
        self._connected = False
        self._config: Dict[str, Any] = {}

    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected

    @abstractmethod
    def connect(self, host: str, port: int, **kwargs) -> bool:
        """
        Establish connection to remote host.

        Args:
            host: Remote hostname or IP address
            port: Remote port number
            **kwargs: Transport-specific connection options

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection and release resources."""
        pass

    @abstractmethod
    def send(self, data: bytes) -> int:
        """
        Send data over the transport.

        Args:
            data: Bytes to send

        Returns:
            Number of bytes sent

        Raises:
            ConnectionError: If not connected
            IOError: If send fails
        """
        pass

    @abstractmethod
    def recv(self, size: int, timeout: Optional[float] = None) -> bytes:
        """
        Receive data from the transport.

        Args:
            size: Maximum number of bytes to receive
            timeout: Optional timeout in seconds

        Returns:
            Received bytes

        Raises:
            ConnectionError: If not connected
            IOError: If receive fails
            TimeoutError: If timeout expires
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this transport is available on the system.

        Returns:
            True if transport can be used, False otherwise
        """
        pass

    def get_latency(self) -> float:
        """
        Get average measured latency in seconds.

        Returns:
            Average latency in seconds, or 0.0 if no measurements
        """
        return self.metrics.avg_latency

    def get_bandwidth(self) -> float:
        """
        Get measured bandwidth in Mbps.

        Returns:
            Combined send/receive bandwidth in Mbps
        """
        return self.metrics.send_bandwidth_mbps + self.metrics.recv_bandwidth_mbps

    def get_metrics(self) -> TransportMetrics:
        """Get current performance metrics."""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics.reset()

    def get_config(self) -> Dict[str, Any]:
        """Get transport configuration."""
        return {
            "name": self.name,
            "type": self.transport_type.value,
            "connected": self._connected,
            **self._config,
        }

    def set_config(self, **kwargs) -> None:
        """Set transport-specific configuration options."""
        self._config.update(kwargs)

    def ping(self, count: int = 10) -> Optional[float]:
        """
        Measure round-trip latency with ping-pong test.

        Args:
            count: Number of ping-pong iterations

        Returns:
            Average round-trip time in seconds, or None if failed
        """
        if not self._connected:
            return None

        latencies = []
        ping_data = b"PING" + (b"\x00" * 60)  # 64 byte ping packet

        for _ in range(count):
            start = time.perf_counter()
            try:
                self.send(ping_data)
                self.recv(64, timeout=1.0)
                latency = time.perf_counter() - start
                latencies.append(latency)
                self.metrics.update_latency(latency)
            except (IOError, TimeoutError):
                continue

        if latencies:
            return sum(latencies) / len(latencies)
        return None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure disconnection."""
        self.disconnect()
        return False

    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"<{self.__class__.__name__} ({self.transport_type.value}) [{status}]>"
