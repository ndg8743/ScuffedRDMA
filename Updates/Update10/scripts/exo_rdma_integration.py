"""EXO framework RDMA integration: discovery, transport, topology."""
import subprocess
from typing import Optional, Dict
from transports import TransportSelector, NCCLConfig


class RDMADiscovery:
    @staticmethod
    def get_rdma_devices() -> list[str]:
        result = subprocess.run(['rdma', 'link', 'show'],
                                capture_output=True)
        # Parse device names from output...

    @classmethod
    def get_best_interface(cls) -> Optional['RDMAInterface']:
        """Priority: mlx5_* (hardware) > rxe* (soft-RoCE)"""
        interfaces = cls.discover_all()
        for iface in interfaces:
            if iface.device.startswith('mlx5_'):
                return iface
        for iface in interfaces:
            if iface.device.startswith('rxe'):
                return iface
        return interfaces[0] if interfaces else None


class RDMATransport:
    def connect(self, peer_node_id: str, peer_host: str,
                peer_port: int) -> bool:
        selector = TransportSelector('roce')
        self._transport = selector.get_transport(
            device=self._interface)
        self._transport.connect(peer_host, peer_port)
        return True

    def get_nccl_config(self) -> Dict[str, str]:
        if not self.is_available:
            return NCCLConfig.for_tcp().to_env()
        return NCCLConfig.for_softroce(
            device=self._interface).to_env()


class RDMATopologyManager:
    def __init__(self, node_id, topology):
        self.node_id = node_id
        self.topology = topology
        self._local_interface = \
            RDMADiscovery.get_best_interface()

    def discover_and_update(self) -> int:
        return update_topology_with_rdma(
            self.topology, self.node_id)

    def get_rdma_peers(self) -> list:
        return [conn.sink for conn in
                self.topology.out_edges(self.node_id)
                if isinstance(conn.edge, RDMAConnection)]
