"""Transport base interface and implementations (TCP, RoCE, TTPoe)."""
import os
import socket
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TransportMetrics:
    min_latency: float = 0.0
    max_latency: float = 0.0
    avg_latency: float = 0.0
    bytes_sent: int = 0
    bytes_received: int = 0


class TransportBase(ABC):
    @abstractmethod
    def connect(self, host: str, port: int, **kwargs) -> bool:
        pass

    @abstractmethod
    def send(self, data: bytes) -> int:
        pass

    @abstractmethod
    def recv(self, size: int, timeout: float = None) -> bytes:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class TCPTransport(TransportBase):
    def connect(self, host: str, port: int, **kwargs) -> bool:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._socket.connect((host, port))
        return True

    def send(self, data: bytes) -> int:
        start = time.perf_counter()
        sent = self._socket.send(data)
        self.metrics.update_latency(time.perf_counter() - start)
        return sent

    def is_available(self) -> bool:
        return True  # TCP always available


class RoCETransport(TransportBase):
    def connect(self, host: str, port: int, **kwargs) -> bool:
        import pyverbs.device as d
        import pyverbs.qp as qp
        self._context = d.Context(name='rxe0')
        self._pd = pd.PD(self._context)
        self._qp = qp.QP(self._pd, qp_init)
        # Exchange QP info via TCP (out-of-band)
        remote_info = self._exchange_qp_info(host, port)
        self._transition_qp_to_rts(remote_info)
        return True

    def is_available(self) -> bool:
        return 'rdma_rxe' in subprocess.run(['lsmod']).stdout


class TTPoeTransport(TransportBase):
    def load_modules(self, dst_mac: str, verbose: int = 1) -> bool:
        subprocess.run(['insmod',
            f'{self._ttpoe_dir}/modttpoe/modttpoe.ko',
            f'dev={self._device}', f'dst={dst_mac}',
            f'verbose={verbose}'])
        return True

    def connect(self, host: str, port: int, **kwargs) -> bool:
        if not self._check_module_loaded():
            self.load_modules(kwargs.get('dst_mac'))
        self._fd = os.open('/dev/ttpoe', os.O_RDWR)
        return True

    def send(self, data: bytes) -> int:
        return os.write(self._fd, data)

    def is_available(self) -> bool:
        return os.path.exists(
            f'{self._ttpoe_dir}/modttpoe/modttpoe.ko')


class TransportSelector:
    def __init__(self, transport: str = None):
        self._transport = transport or \
            os.environ.get('SCUFFED_TRANSPORT', 'auto')

    def _auto_select(self) -> TransportBase:
        # Priority: TTPoe > Hardware RoCE > Soft-RoCE > TCP
        if TTPoeTransport().is_available():
            return TTPoeTransport()
        if RoCETransport().is_available():
            return RoCETransport()
        return TCPTransport()


class NCCLConfig:
    @classmethod
    def for_tcp(cls):
        return cls(ib_disable=True, net_gdr_level=0)

    @classmethod
    def for_softroce(cls, device='rxe0'):
        return cls(ib_hca=device, ib_gid_index=1,
                   net_gdr_level=0)

    @classmethod
    def for_hardware_roce(cls, hca='mlx5_0'):
        return cls(ib_hca=hca, net_gdr_level=5)
