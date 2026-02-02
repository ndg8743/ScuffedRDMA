"""
ScuffedRDMA Transport Middleware

Adaptive transport layer for distributed LLM inference supporting:
- TCP (baseline)
- Soft-RoCE (rxe0)
- Tesla TTPoe (modttpoe)

Usage:
    from middleware import TransportSelector

    # Select transport via environment or explicit choice
    ts = TransportSelector('tcp')  # or 'roce', 'ttpoe'
    transport = ts.get_transport()

    # Send/receive data
    transport.connect(host, port)
    transport.send(data)
    response = transport.recv(size)

    # Get NCCL configuration
    nccl_env = ts.get_nccl_config()
"""

from .transport_base import TransportBase, TransportMetrics
from .tcp_transport import TCPTransport
from .roce_transport import RoCETransport
from .ttpoe_transport import TTPoeTransport
from .selector import TransportSelector
from .nccl_config import NCCLConfig

__all__ = [
    'TransportBase',
    'TransportMetrics',
    'TCPTransport',
    'RoCETransport',
    'TTPoeTransport',
    'TransportSelector',
    'NCCLConfig',
]

__version__ = '0.1.0'
