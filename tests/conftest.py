import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _has_rdma_device() -> bool:
    return os.path.isdir("/sys/class/infiniband") and bool(os.listdir("/sys/class/infiniband"))


def pytest_collection_modifyitems(config, items):
    if _has_rdma_device():
        return
    skip = pytest.mark.skip(reason="no RDMA device on this host (/sys/class/infiniband empty)")
    for it in items:
        if "rdma" in it.keywords:
            it.add_marker(skip)
