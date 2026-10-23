"""Completion-status checking in the pyverbs dual QP pool (no RDMA device needed)."""
from types import SimpleNamespace

import pytest

from middleware.rdma_tensor_cache import dual_qp_pool as dq


class _CQ:
    def __init__(self, wcs):
        self._wcs = list(wcs)

    def poll(self, num_entries=1):
        if not self._wcs:
            return 0, []
        return 1, [self._wcs.pop(0)]


def _qpe(wcs):
    return SimpleNamespace(cq=_CQ(wcs), outstanding=len(wcs))


def test_success_completion_passes():
    pool = object.__new__(dq.DualQPPool)
    assert pool._poll_busy(_qpe([SimpleNamespace(status=0)]), timeout=0.5) >= 1
    assert pool._poll_sleep(_qpe([SimpleNamespace(status=0)]), timeout=0.5, sleep_us=1) >= 1


@pytest.mark.parametrize("status,name", [(5, "IBV_WC_WR_FLUSH_ERR"), (12, "IBV_WC_RETRY_EXC_ERR"), (10, "IBV_WC_REM_ACCESS_ERR")])
def test_error_completion_raises_not_fast_success(status, name):
    pool = object.__new__(dq.DualQPPool)
    with pytest.raises(dq.RDMACompletionError) as ei:
        pool._poll_busy(_qpe([SimpleNamespace(status=status, vendor_err=0x81, wr_id=7)]), timeout=0.5)
    assert name in str(ei.value) and ei.value.label == "hot"
    with pytest.raises(dq.RDMACompletionError):
        pool._poll_sleep(_qpe([SimpleNamespace(status=status)]), timeout=0.5, sleep_us=1)


def test_error_completion_counts_qp_error_event():
    from middleware import telemetry
    before = telemetry.default().snapshot()["classes"].get("cold", {}).get("events", {}).get("qp_error", 0)
    with pytest.raises(dq.RDMACompletionError):
        dq.check_completion(SimpleNamespace(status=5), "cold")
    after = telemetry.default().snapshot()["classes"]["cold"]["events"]["qp_error"]
    assert after == before + 1
