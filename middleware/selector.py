"""
Transport Selector.

Main entry point for the middleware layer. Provides runtime selection
of transport backend based on environment, configuration, or availability.
"""

import os
from typing import Optional, Dict, Any, Type, List
from enum import Enum

from .transport_base import TransportBase, TransportType, TransportMetrics
from .tcp_transport import TCPTransport
from .roce_transport import RoCETransport
from .ttpoe_transport import TTPoeTransport
from .nccl_config import NCCLConfig


class TransportSelector:
    """
    Transport selector and factory.

    Provides unified interface for selecting and configuring transports
    for distributed LLM inference.

    Usage:
        # Select via environment variable (SCUFFED_TRANSPORT)
        selector = TransportSelector()

        # Or explicit selection
        selector = TransportSelector('roce')

        # Get transport instance
        transport = selector.get_transport()

        # Get NCCL configuration
        nccl_config = selector.get_nccl_config()

    Environment Variables:
        SCUFFED_TRANSPORT: Transport type (tcp, roce, ttpoe, auto)
        SCUFFED_ROCE_DEVICE: RoCE device name (default: rxe0)
        SCUFFED_TTPOE_DIR: TTPoe source directory
        SCUFFED_TTPOE_DEVICE: TTPoe network interface
    """

    # Transport class registry
    _transports: Dict[str, Type[TransportBase]] = {
        'tcp': TCPTransport,
        'roce': RoCETransport,
        'ttpoe': TTPoeTransport,
    }

    def __init__(self, transport: Optional[str] = None):
        """
        Initialize transport selector.

        Args:
            transport: Transport type ('tcp', 'roce', 'ttpoe', 'auto', None)
                      If None, reads from SCUFFED_TRANSPORT env var
        """
        self._transport_name = transport or os.environ.get('SCUFFED_TRANSPORT', 'auto')
        self._transport_name = self._transport_name.lower()
        self._transport: Optional[TransportBase] = None
        self._nccl_config: Optional[NCCLConfig] = None

        # Device configuration from environment
        self._roce_device = os.environ.get('SCUFFED_ROCE_DEVICE', 'rxe0')
        self._ttpoe_dir = os.environ.get('SCUFFED_TTPOE_DIR', '/opt/ttpoe')
        self._ttpoe_device = os.environ.get('SCUFFED_TTPOE_DEVICE', 'eth0')

    @property
    def transport_name(self) -> str:
        """Get selected transport name."""
        return self._transport_name

    def get_transport(self, **kwargs) -> TransportBase:
        """
        Get transport instance.

        Args:
            **kwargs: Transport-specific configuration options

        Returns:
            Configured transport instance
        """
        if self._transport is not None:
            return self._transport

        if self._transport_name == 'auto':
            self._transport = self._auto_select(**kwargs)
        elif self._transport_name == 'tcp':
            self._transport = TCPTransport()
        elif self._transport_name == 'roce':
            self._transport = RoCETransport(device=kwargs.get('device', self._roce_device))
        elif self._transport_name == 'ttpoe':
            self._transport = TTPoeTransport(
                device=kwargs.get('device', self._ttpoe_device),
                ttpoe_dir=kwargs.get('ttpoe_dir', self._ttpoe_dir)
            )
        else:
            raise ValueError(f"Unknown transport: {self._transport_name}")

        return self._transport

    def _auto_select(self, **kwargs) -> TransportBase:
        """
        Auto-select best available transport.

        Priority:
        1. TTPoe (if modules available)
        2. Hardware RoCE (Mellanox)
        3. Soft-RoCE (rxe0)
        4. TCP (always available)
        """
        # Try TTPoe
        ttpoe = TTPoeTransport(
            device=kwargs.get('device', self._ttpoe_device),
            ttpoe_dir=kwargs.get('ttpoe_dir', self._ttpoe_dir)
        )
        if ttpoe.is_available():
            self._transport_name = 'ttpoe'
            return ttpoe

        # Try RoCE
        roce = RoCETransport(device=kwargs.get('device', self._roce_device))
        if roce.is_available():
            self._transport_name = 'roce'
            return roce

        # Fallback to TCP
        self._transport_name = 'tcp'
        return TCPTransport()

    def get_nccl_config(self) -> NCCLConfig:
        """
        Get NCCL configuration for selected transport.

        Returns:
            NCCLConfig instance for the transport
        """
        if self._nccl_config is not None:
            return self._nccl_config

        # Resolve auto if needed
        if self._transport_name == 'auto':
            self.get_transport()

        if self._transport_name == 'tcp':
            self._nccl_config = NCCLConfig.for_tcp()
        elif self._transport_name == 'roce':
            self._nccl_config = NCCLConfig.for_softroce(device=self._roce_device)
        elif self._transport_name == 'ttpoe':
            self._nccl_config = NCCLConfig.for_ttpoe(interface=self._ttpoe_device)
        else:
            self._nccl_config = NCCLConfig.for_tcp()

        return self._nccl_config

    def get_config(self) -> Dict[str, Any]:
        """
        Get full configuration dictionary.

        Returns:
            Configuration for transport and NCCL
        """
        transport = self.get_transport()
        nccl = self.get_nccl_config()

        return {
            'transport': {
                'name': self._transport_name,
                'type': transport.transport_type.value,
                'available': transport.is_available(),
                'config': transport.get_config(),
            },
            'nccl': {
                'env': nccl.to_env(),
            },
        }

    def apply_nccl_config(self) -> None:
        """Apply NCCL configuration to current process environment."""
        self.get_nccl_config().apply()

    def get_shell_exports(self) -> str:
        """
        Get shell export commands for configuration.

        Returns:
            Shell script fragment
        """
        lines = [
            f"# ScuffedRDMA Transport: {self._transport_name}",
            f'export SCUFFED_TRANSPORT="{self._transport_name}"',
            "",
        ]
        lines.append(self.get_nccl_config().to_shell_export())
        return "\n".join(lines)

    @classmethod
    def list_transports(cls) -> List[Dict[str, Any]]:
        """
        List all available transports and their status.

        Returns:
            List of transport info dictionaries
        """
        transports = []

        for name, transport_cls in cls._transports.items():
            try:
                transport = transport_cls()
                available = transport.is_available()
            except Exception:
                available = False

            transports.append({
                'name': name,
                'available': available,
                'class': transport_cls.__name__,
            })

        return transports

    @classmethod
    def register_transport(cls, name: str, transport_cls: Type[TransportBase]) -> None:
        """
        Register a custom transport.

        Args:
            name: Transport name (for selection)
            transport_cls: Transport class
        """
        cls._transports[name.lower()] = transport_cls

    def benchmark_all(self, host: str, port: int,
                      iterations: int = 100,
                      message_size: int = 4096) -> Dict[str, TransportMetrics]:
        """
        Benchmark all available transports.

        Args:
            host: Remote host for connection
            port: Remote port
            iterations: Number of test iterations
            message_size: Size of test messages

        Returns:
            Dictionary mapping transport name to metrics
        """
        results = {}
        test_data = b'X' * message_size

        for name, transport_cls in self._transports.items():
            try:
                transport = transport_cls()
                if not transport.is_available():
                    continue

                transport.connect(host, port)
                transport.reset_metrics()

                for _ in range(iterations):
                    transport.send(test_data)
                    transport.recv(message_size)

                results[name] = transport.get_metrics()
                transport.disconnect()

            except Exception as e:
                # Skip transports that fail
                pass

        return results

    def __str__(self) -> str:
        return f"TransportSelector[{self._transport_name}]"

    def __repr__(self) -> str:
        return f"TransportSelector(transport='{self._transport_name}')"


def get_selector(transport: Optional[str] = None) -> TransportSelector:
    """
    Convenience function to get a transport selector.

    Args:
        transport: Transport type or None for auto

    Returns:
        TransportSelector instance
    """
    return TransportSelector(transport)


def get_transport(transport: Optional[str] = None, **kwargs) -> TransportBase:
    """
    Convenience function to get a transport instance.

    Args:
        transport: Transport type or None for auto
        **kwargs: Transport-specific options

    Returns:
        Transport instance
    """
    return TransportSelector(transport).get_transport(**kwargs)


def get_nccl_config(transport: Optional[str] = None) -> NCCLConfig:
    """
    Convenience function to get NCCL configuration.

    Args:
        transport: Transport type or None for auto

    Returns:
        NCCLConfig instance
    """
    return TransportSelector(transport).get_nccl_config()
