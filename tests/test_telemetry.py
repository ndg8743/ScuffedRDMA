import json
import math
import urllib.request

from middleware.telemetry import LatencyHistogram, SignalVector, Telemetry


def test_histogram_percentiles_exact_small():
    h = LatencyHistogram()
    h.extend(range(1, 101))
    assert h.n == 100
    assert abs(h.percentile(50) - 50.5) < 1e-9
    assert h.percentile(99) > 98
    assert h.summary()["max_us"] == 100


def test_histogram_ignores_nan():
    h = LatencyHistogram()
    h.add(float("nan"))
    assert h.n == 0 and math.isnan(h.percentile(50))


def test_per_class_and_events(tmp_path):
    t = Telemetry(node="n1")
    t.record_many("hot", [5, 6, 7], nbytes_each=64)
    t.record("cold", 900.0, nbytes=1 << 20, queue_depth=12)
    t.event("hot", "qp_error")
    t.event("hot", "reconnect")
    t.event("cold", "tcp_fallback")
    s = t.snapshot()
    assert s["classes"]["hot"]["ops"] == 3
    assert s["classes"]["hot"]["bytes"] == 192
    assert s["classes"]["hot"]["errors"] == 1
    assert s["classes"]["cold"]["queue_depth_max"] == 12
    p = t.to_json(str(tmp_path / "t.json"))
    assert json.load(open(p))["node"] == "n1"


def test_prometheus_text_and_http():
    t = Telemetry(node="n1")
    t.record("hot", 3.0, 64)
    t.event("hot", "reconnect")
    txt = t.prometheus_text()
    assert '# TYPE scuffed_completion_latency_us histogram' in txt
    assert 'scuffed_events_total{node="n1",class="hot",kind="reconnect"} 1' in txt
    assert 'le="+Inf"} 1' in txt
    port = t.serve(port=0, addr="127.0.0.1")
    try:
        body = urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=5).read().decode()
        assert "scuffed_ops_total" in body
    finally:
        t.stop()


def test_signal_vector_inter_arrival_and_features():
    t = Telemetry()
    a = t.observe(SignalVector(size_bytes=4096, tensor_id="k0", timestamp=1.0))
    b = t.observe(SignalVector(size_bytes=4096, tensor_id="k0", timestamp=1.001, qp_class="hot", completion_us=7.0))
    assert math.isnan(a.inter_arrival_us)
    assert abs(b.inter_arrival_us - 1000.0) < 1e-6
    assert len(b.features()) == len(SignalVector.FEATURE_NAMES)
    assert t.snapshot()["classes"]["hot"]["ops"] == 1
