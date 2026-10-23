import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _has_rdma_device() -> bool:
    return os.path.isdir("/sys/class/infiniband") and bool(os.listdir("/sys/class/infiniband"))


def _has_cuda() -> bool:
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


def pytest_collection_modifyitems(config, items):
    rdma, cuda = _has_rdma_device(), _has_cuda()
    skip_rdma = pytest.mark.skip(reason="no RDMA device on this host (/sys/class/infiniband empty)")
    skip_gpu = pytest.mark.skip(reason="no CUDA GPU (torch.cuda.is_available() is False)")
    for it in items:
        if "rdma" in it.keywords and not rdma:
            it.add_marker(skip_rdma)
        if "gpu" in it.keywords and not cuda:
            it.add_marker(skip_gpu)
