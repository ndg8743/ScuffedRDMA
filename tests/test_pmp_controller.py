import pytest

from middleware.rdma_tensor_cache.dual_qp_pool import QueueSelection
from middleware.rdma_tensor_cache.pmp_controller import PMPController, StorageDecision


# ---- existing two-arm behavior -------------------------------------------

def test_hot_congested_goes_cold():
    p = PMPController()
    assert p.decide(hot_depth=5, cold_depth=0) == QueueSelection.COLD_QP


def test_cold_congested_goes_hot():
    p = PMPController()
    assert p.decide(hot_depth=0, cold_depth=5) == QueueSelection.HOT_QP


def test_deadband_keeps_last_decision():
    p = PMPController(deadband=1e9)
    # initial last decision is COLD; huge deadband never switches
    assert p.decide(0, 50) == QueueSelection.COLD_QP
    p2 = PMPController(deadband=0.1)
    assert p2.decide(0, 1) == QueueSelection.HOT_QP
    # S == 0 is inside the deadband: stay HOT
    assert p2.decide(0, 0) == QueueSelection.HOT_QP


def test_switching_function_sign_matches_formula():
    p = PMPController(mu_hot=10.0, mu_cold=10.0, alpha=1.0, beta=1.0, deadband=0.0)
    p.decide(3, 2)
    e = p.history[-1]
    assert e.switching_function == pytest.approx(3 * 10.0 - 2 * 10.0)
    assert e.decision == QueueSelection.COLD_QP


def test_stats_and_reset():
    p = PMPController()
    p.decide(5, 0)
    p.decide(0, 5)
    s = p.get_stats()
    assert s["total_decisions"] == 2 and s["switches"] == 1
    p.decide_with_storage(0, 0, 0.99)
    p.reset()
    assert p.get_stats()["total_decisions"] == 0
    assert p.get_storage_stats()["total_decisions"] == 0


# ---- storage arm ----------------------------------------------------------

def test_no_pressure_equals_two_arm():
    a, b = PMPController(), PMPController()
    for hd, cd in [(5, 0), (0, 5), (1, 1), (0, 0), (3, 7)]:
        two = a.decide(hd, cd)
        three = b.decide_with_storage(hd, cd, gpu_mem_util=0.5, spill_depth=0)
        assert three == StorageDecision.from_queue(two)
    assert all(e.decision != StorageDecision.SPILL for e in b.storage_history)


def test_pressure_normalization():
    p = PMPController(u0=0.8)
    assert p.pressure(0.5) == 0.0
    assert p.pressure(0.9) == pytest.approx(0.5)
    assert p.pressure(1.5) == 1.0


def test_high_pressure_spills_when_queues_busy():
    p = PMPController(u0=0.85, gamma=50000.0)
    d = p.decide_with_storage(hot_depth=4, cold_depth=10, gpu_mem_util=0.99, spill_depth=0)
    assert d == StorageDecision.SPILL
    e = p.storage_history[-1]
    assert e.sigma_spill < min(e.sigma_hot, e.sigma_cold)


def test_deep_spill_queue_stops_spilling():
    p = PMPController(u0=0.85, gamma=50000.0, mu_spill=500.0, delta=1.0)
    d = p.decide_with_storage(hot_depth=4, cold_depth=10, gpu_mem_util=0.99, spill_depth=10_000)
    assert d != StorageDecision.SPILL


def test_storage_hysteresis():
    p = PMPController(u0=0.5, gamma=1000.0, deadband=1e6, mu_spill=1.0)
    first = p.decide_with_storage(5, 5, gpu_mem_util=1.0, spill_depth=0)
    assert first == StorageDecision.SPILL
    # hot now cheapest, but within the (huge) deadband: keep SPILL
    assert p.decide_with_storage(0, 5, gpu_mem_util=1.0, spill_depth=10) == StorageDecision.SPILL


def test_bad_watermark():
    with pytest.raises(ValueError):
        PMPController(u0=1.0)
