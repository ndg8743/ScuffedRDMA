import collections
import json

import numpy as np
import pytest

from middleware.rdma_tensor_cache.dual_qp_pool import QueueSelection
from middleware.rdma_tensor_cache.wfa_learner import (
    PHI_NAMES, STATES, LearnedWFA, ModelShape, SyntheticTraceGenerator, evaluate,
    evaluate_static, from_telemetry, latency_label, oracle_label,
)
from middleware.telemetry import SignalVector, Telemetry


@pytest.fixture(scope="module")
def fitted():
    mix = {"prefill": 0.3, "decode": 0.3, "control": 0.2, "bursty": 0.1, "chunked": 0.1}
    train = [SyntheticTraceGenerator(seed=1).generate(5000, mix),
             SyntheticTraceGenerator(seed=2, model=ModelShape(layers=24, kv_heads=4, head_dim=128)).generate(5000, mix)]
    return LearnedWFA(epochs=300, seed=0).fit(train)


def test_generator_deterministic_and_covers_states():
    a = SyntheticTraceGenerator(seed=3).generate(3000)
    b = SyntheticTraceGenerator(seed=3).generate(3000)
    assert [(s.size_bytes, s.tensor_id, l) for s, l in a] == [(s.size_bytes, s.tensor_id, l) for s, l in b]
    mixed = SyntheticTraceGenerator(seed=3).generate(4000, {"bursty": 0.5, "chunked": 0.3, "decode": 0.2})
    c = collections.Counter(l for _, l in mixed)
    assert set(c) == set(STATES)
    for s, l in mixed:
        assert l == oracle_label(s)


def test_generator_rejects_unknown_pattern():
    with pytest.raises(ValueError):
        SyntheticTraceGenerator().generate(10, {"nope": 1.0})


def test_fit_reduces_loss(fitted):
    assert fitted.loss_history[-1] < 0.25 * fitted.loss_history[0]
    assert fitted.W.shape == (3, 3, len(PHI_NAMES) + 1)


def test_heldout_accuracy_and_beats_static(fitted):
    test = [SyntheticTraceGenerator(seed=11, model=ModelShape(layers=32, head_dim=128)).generate(4000)]
    e = evaluate(fitted, test)
    s = evaluate_static(test)
    assert e["state_accuracy"] > 0.97
    assert e["hot_f1"] > 0.97
    assert e["routing_accuracy"] >= s["routing_accuracy"]
    assert np.asarray(e["confusion_states"]).sum() == e["n"] == 4000
    assert sum(sum(r) for r in s["confusion_binary"]) == s["n"]


def test_classify_tracks_state_per_tensor(fitted):
    fitted.reset()
    tok = SignalVector(size_bytes=40, role="token", phase="decode", tensor_id="tok:1")
    bulk = SignalVector(size_bytes=8 << 20, role="kv", phase="prefill", tensor_id="kv:1:0", seq_len=4096)
    assert fitted.classify(tok) == QueueSelection.HOT_QP
    assert fitted.classify(bulk) == QueueSelection.COLD_QP
    assert fitted._state["tok:1"] == STATES.index("hot")
    p = fitted.transition_probs(bulk, state="hot")
    assert p.shape == (3,) and abs(p.sum() - 1) < 1e-9
    fitted.reset()
    assert not fitted._state


def test_save_load_roundtrip(fitted, tmp_path):
    path = fitted.save(str(tmp_path / "w.json"))
    m2 = LearnedWFA.load(path)
    trace = SyntheticTraceGenerator(seed=5).generate(500)
    fitted.reset()
    a = [fitted.predict_state(s) for s, _ in trace]
    b = [m2.predict_state(s) for s, _ in trace]
    assert a == b
    assert set(fitted.feature_weights()) == set(STATES)


def test_load_rejects_bad_file(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"format": "other"}))
    with pytest.raises(ValueError):
        LearnedWFA.load(str(p))


def test_unfitted_raises():
    with pytest.raises(RuntimeError):
        LearnedWFA().classify(SignalVector(size_bytes=1))


def test_from_telemetry_and_labels():
    tel = Telemetry()
    for i, size in enumerate([64, 4 << 20, 32 << 10]):
        tel.observe(SignalVector(size_bytes=size, role="metadata" if size == 64 else "kv",
                                 phase="decode", tensor_id=f"t{i}", timestamp=float(i)))
    [trace] = from_telemetry(tel)
    assert [l for _, l in trace] == ["hot", "warm", "hot"]
    [trace_b] = from_telemetry(tel, lambda s: s.size_bytes < 1024)
    assert [l for _, l in trace_b] == ["hot", "cold", "cold"]
    [trace_q] = from_telemetry(tel, lambda s: QueueSelection.HOT_QP)
    assert {l for _, l in trace_q} == {"hot"}
    with pytest.raises(ValueError):
        from_telemetry(tel, lambda s: "lukewarm")
    fn = latency_label(20.0)
    assert fn(SignalVector(size_bytes=4096, completion_us=10.0)) == "hot"
    assert fn(SignalVector(size_bytes=1 << 20, completion_us=10.0)) == "cold"


def test_fit_rejects_empty():
    with pytest.raises(ValueError):
        LearnedWFA().fit([[]])
