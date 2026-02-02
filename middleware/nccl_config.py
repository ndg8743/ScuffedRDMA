"""
NCCL Configuration Management.

Manages NCCL environment variables for different transport backends.
NCCL (NVIDIA Collective Communications Library) uses these variables
to select transport and configure RDMA settings.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum


class NCCLTransport(Enum):
    """NCCL transport types."""
    TCP = "tcp"
    IB = "ib"          # InfiniBand / RoCE
    NET = "net"        # Network (auto-detect)
    SHM = "shm"        # Shared memory (intra-node)


@dataclass
class NCCLConfig:
    """
    NCCL configuration manager.

    Provides methods to configure NCCL for different transport backends:
    - TCP: Standard socket transport (baseline)
    - Soft-RoCE: RDMA over Ethernet using rxe0 device
    - Hardware RoCE: Native RDMA with Mellanox NICs
    - TTPoe: Custom transport (requires socket plugin)
    """

    # IB/RoCE settings
    ib_disable: bool = False
    ib_hca: Optional[str] = None
    ib_gid_index: Optional[int] = None
    ib_timeout: int = 22
    ib_retry_cnt: int = 7

    # Network settings
    net_gdr_level: Optional[int] = None
    net_gdr_read: int = 1

    # Socket settings
    socket_ifname: Optional[str] = None
    socket_nthreads: int = 4

    # Debug settings
    debug: str = "INFO"
    debug_subsys: Optional[str] = None

    # Performance tuning
    buffsize: int = 4194304  # 4MB
    nthreads: int = 256
    nsocks_perthread: int = 4

    # Algorithm selection
    algo: Optional[str] = None  # Ring, Tree, CollNet
    proto: Optional[str] = None  # Simple, LL, LL128

    # Additional settings
    extra: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def for_tcp(cls, interface: Optional[str] = None) -> 'NCCLConfig':
        """
        Create configuration for TCP transport.

        Args:
            interface: Optional network interface name

        Returns:
            NCCLConfig for TCP mode
        """
        config = cls(
            ib_disable=True,
            net_gdr_level=0,
            debug="INFO",
        )
        if interface:
            config.socket_ifname = interface
        return config

    @classmethod
    def for_softroce(cls, device: str = "rxe0") -> 'NCCLConfig':
        """
        Create configuration for Soft-RoCE transport.

        Args:
            device: RXE device name (default: rxe0)

        Returns:
            NCCLConfig for Soft-RoCE mode
        """
        return cls(
            ib_disable=False,
            ib_hca=device,
            ib_gid_index=1,  # RoCEv2 GID index
            net_gdr_level=0,  # No GPUDirect with Soft-RoCE
            debug="INFO",
        )

    @classmethod
    def for_hardware_roce(cls, hca: str = "mlx5_0",
                          enable_gdr: bool = True) -> 'NCCLConfig':
        """
        Create configuration for hardware RoCE (Mellanox).

        Args:
            hca: HCA device name (e.g., mlx5_0)
            enable_gdr: Enable GPUDirect RDMA

        Returns:
            NCCLConfig for hardware RoCE mode
        """
        config = cls(
            ib_disable=False,
            ib_hca=hca,
            ib_gid_index=3,  # RoCEv2 with proper GID
            net_gdr_read=1,
            debug="INFO",
        )
        if enable_gdr:
            config.net_gdr_level = 5
        return config

    @classmethod
    def for_ttpoe(cls, interface: str = "eth0") -> 'NCCLConfig':
        """
        Create configuration for TTPoe transport.

        TTPoe requires custom socket layer - this config disables
        NCCL's IB path and sets up for socket transport.

        Args:
            interface: Network interface for TTPoe

        Returns:
            NCCLConfig for TTPoe mode
        """
        return cls(
            ib_disable=True,
            socket_ifname=interface,
            net_gdr_level=0,
            debug="INFO",
            # TTPoe-specific settings
            extra={
                "NCCL_SOCKET_FAMILY": "AF_INET",
                "TTPOE_ENABLED": "1",
            }
        )

    def to_env(self) -> Dict[str, str]:
        """
        Convert configuration to environment variables.

        Returns:
            Dictionary of NCCL_* environment variables
        """
        env = {}

        # IB settings
        if self.ib_disable:
            env["NCCL_IB_DISABLE"] = "1"
        else:
            env["NCCL_IB_DISABLE"] = "0"

        if self.ib_hca:
            env["NCCL_IB_HCA"] = self.ib_hca

        if self.ib_gid_index is not None:
            env["NCCL_IB_GID_INDEX"] = str(self.ib_gid_index)

        env["NCCL_IB_TIMEOUT"] = str(self.ib_timeout)
        env["NCCL_IB_RETRY_CNT"] = str(self.ib_retry_cnt)

        # Network settings
        if self.net_gdr_level is not None:
            env["NCCL_NET_GDR_LEVEL"] = str(self.net_gdr_level)

        env["NCCL_NET_GDR_READ"] = str(self.net_gdr_read)

        # Socket settings
        if self.socket_ifname:
            env["NCCL_SOCKET_IFNAME"] = self.socket_ifname

        env["NCCL_SOCKET_NTHREADS"] = str(self.socket_nthreads)

        # Debug settings
        env["NCCL_DEBUG"] = self.debug
        if self.debug_subsys:
            env["NCCL_DEBUG_SUBSYS"] = self.debug_subsys

        # Performance tuning
        env["NCCL_BUFFSIZE"] = str(self.buffsize)
        env["NCCL_NTHREADS"] = str(self.nthreads)
        env["NCCL_NSOCKS_PERTHREAD"] = str(self.nsocks_perthread)

        # Algorithm selection
        if self.algo:
            env["NCCL_ALGO"] = self.algo
        if self.proto:
            env["NCCL_PROTO"] = self.proto

        # Extra settings
        env.update(self.extra)

        return env

    def apply(self) -> None:
        """Apply configuration to current process environment."""
        for key, value in self.to_env().items():
            os.environ[key] = value

    def to_shell_export(self) -> str:
        """
        Generate shell export commands.

        Returns:
            Shell script fragment with export statements
        """
        lines = ["# NCCL Configuration"]
        for key, value in sorted(self.to_env().items()):
            lines.append(f'export {key}="{value}"')
        return "\n".join(lines)

    def to_docker_env(self) -> List[str]:
        """
        Generate Docker -e flags.

        Returns:
            List of "-e KEY=VALUE" strings
        """
        return [f"-e {key}={value}" for key, value in self.to_env().items()]

    def to_compose_env(self) -> Dict[str, str]:
        """
        Generate docker-compose environment section.

        Returns:
            Dictionary suitable for compose environment block
        """
        return self.to_env()

    @staticmethod
    def detect_available_devices() -> Dict[str, List[str]]:
        """
        Detect available RDMA/network devices.

        Returns:
            Dictionary with 'rdma' and 'net' device lists
        """
        import subprocess

        devices = {
            'rdma': [],
            'net': [],
        }

        # Detect RDMA devices
        try:
            result = subprocess.run(
                ['rdma', 'link', 'show'],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if 'link' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        # Format: "link rxe0/1 state ACTIVE ..."
                        dev_name = parts[1].split('/')[0]
                        devices['rdma'].append(dev_name)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        # Detect network interfaces
        try:
            result = subprocess.run(
                ['ip', '-o', 'link', 'show'],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                parts = line.split(':')
                if len(parts) >= 2:
                    ifname = parts[1].strip().split('@')[0]
                    if ifname and ifname != 'lo':
                        devices['net'].append(ifname)
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        return devices

    @classmethod
    def auto_detect(cls) -> 'NCCLConfig':
        """
        Auto-detect best available transport.

        Priority:
        1. Hardware RoCE (mlx5_*)
        2. Soft-RoCE (rxe*)
        3. TCP fallback

        Returns:
            NCCLConfig for best available transport
        """
        devices = cls.detect_available_devices()

        # Check for Mellanox HCA
        for dev in devices['rdma']:
            if dev.startswith('mlx5_'):
                return cls.for_hardware_roce(hca=dev)

        # Check for Soft-RoCE
        for dev in devices['rdma']:
            if dev.startswith('rxe'):
                return cls.for_softroce(device=dev)

        # Fallback to TCP
        interface = devices['net'][0] if devices['net'] else None
        return cls.for_tcp(interface=interface)

    def __str__(self) -> str:
        """String representation showing transport mode."""
        if self.ib_disable:
            mode = "TCP"
        elif self.ib_hca and 'mlx5' in self.ib_hca:
            mode = f"Hardware RoCE ({self.ib_hca})"
        elif self.ib_hca and 'rxe' in self.ib_hca:
            mode = f"Soft-RoCE ({self.ib_hca})"
        else:
            mode = "IB/RoCE"

        return f"NCCLConfig[{mode}]"
