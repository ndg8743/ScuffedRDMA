"""NUMA-aware RDMA buffer pool using pyverbs."""
import numa
import pyverbs as pv
from pyverbs.pd import PD
from pyverbs.mr import MR


class RDMABufferPool:
    def __init__(self, ctx, size_mb=256, numa_node=0):
        self.pd = PD(ctx)
        numa.bind(numa_node)
        self.mr = MR(self.pd, size_mb * 1024 * 1024,
                     pv.enums.IBV_ACCESS_LOCAL_WRITE |
                     pv.enums.IBV_ACCESS_REMOTE_WRITE)

    def get_buffer(self, size):
        # Suballocate from registered region
        ...
