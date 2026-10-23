import json

import pytest

from middleware.policy import PolicyConfigError, PolicyEngine, load_policy_file
from middleware.rdma_tensor_cache.dual_qp_pool import QueueSelection
from middleware.rdma_tensor_cache.wfa_classifier import WFAClassifier
from middleware.telemetry import SignalVector


def eng(rules, default=None, **kw):
    return PolicyEngine({"version": 1, "rules": rules,
                         "default": default or {"route": "cold", "compress": False}}, **kw)


def sig(**kw):
    kw.setdefault("size_bytes", 1024)
    return SignalVector(**kw)


# ---- node types -------------------------------------------------------------

def test_threshold_ops():
    for op, val, expect in [("<", 2048, True), ("<=", 1024, True), (">", 1024, False),
                            (">=", 1024, True), ("==", 1024, True), ("!=", 1024, False)]:
        e = eng([{"name": "r", "when": {"threshold": {"field": "size_bytes", "op": op, "value": val}},
                  "then": {"route": "hot"}}])
        assert (e.decide(sig()).route == "hot") is expect, op


def test_in_and_or_not_const():
    rules = [{"name": "r", "when": {"and": [
        {"in": {"field": "role", "values": ["kv"]}},
        {"or": [{"false": True}, {"threshold": {"field": "seq_len", "op": ">", "value": 10}}]},
        {"not": {"in": {"field": "phase", "values": ["prefill"]}}},
        {"true": True},
    ]}, "then": {"route": "hot"}}]
    e = eng(rules)
    assert e.decide(sig(role="kv", seq_len=100, phase="decode")).route == "hot"
    assert e.decide(sig(role="kv", seq_len=100, phase="prefill")).route == "cold"
    assert e.decide(sig(role="kv", seq_len=1, phase="decode")).route == "cold"


def test_context_and_derived_fields():
    e = eng([{"name": "r", "when": {"and": [
        {"threshold": {"field": "gpu_mem_util", "op": ">=", "value": 0.9}},
        {"threshold": {"field": "log2_size", "op": ">=", "value": 20}}]},
        "then": {"route": "spill"}}])
    assert e.decide(sig(size_bytes=1 << 20), {"gpu_mem_util": 0.95}).route == "spill"
    assert e.decide(sig(size_bytes=1 << 19), {"gpu_mem_util": 0.95}).route == "cold"


def test_classifier_leaf_static_and_callable():
    clf = WFAClassifier()
    e = eng([{"name": "r", "when": {"classifier": {"name": "wfa", "equals": "hot"}},
              "then": {"route": "hot"}}], classifiers={"wfa": clf})
    assert e.decide(sig(size_bytes=100, tensor_id="a")).route == "hot"
    assert e.decide(sig(size_bytes=10 << 20, tensor_id="b")).route == "cold"
    calls = []

    def f(s):
        calls.append(s)
        return QueueSelection.HOT_QP

    e2 = eng([{"name": "a", "when": {"classifier": {"name": "f", "equals": "cold"}}, "then": {"compress": True}},
              {"name": "b", "when": {"classifier": {"name": "f", "equals": "hot"}}, "then": {"route": "hot"}}],
             classifiers={"f": f})
    d = e2.decide(sig())
    assert d.route == "hot" and d.compress is False
    assert len(calls) == 1  # memoized within one decide()


def test_unregistered_classifier_is_false_or_strict_error():
    rules = [{"name": "r", "when": {"classifier": {"name": "wfa", "equals": "hot"}}, "then": {"route": "hot"}}]
    assert eng(rules).decide(sig()).route == "cold"
    with pytest.raises(PolicyConfigError):
        eng(rules, strict=True).decide(sig())
    with pytest.raises(PolicyConfigError, match="not registered"):
        eng(rules, classifiers={"other": lambda s: "hot"})


# ---- rule semantics ------------------------------------------------------------

def test_priority_and_field_ownership():
    rules = [
        {"name": "low", "priority": 1, "when": {"true": True}, "then": {"route": "spill", "compress": True}},
        {"name": "high", "priority": 10, "when": {"true": True}, "then": {"route": "hot"}},
    ]
    d = eng(rules).decide(sig())
    assert d.route == "hot" and d.compress is True
    assert d.rules == {"route": "high", "compress": "low"}


def test_same_priority_keeps_file_order():
    rules = [{"name": "a", "when": {"true": True}, "then": {"route": "hot"}},
             {"name": "b", "when": {"true": True}, "then": {"route": "spill"}}]
    assert eng(rules).decide(sig()).route == "hot"


def test_final_stops_and_default_fills():
    rules = [{"name": "a", "priority": 5, "when": {"true": True}, "then": {"route": "hot"}, "final": True},
             {"name": "b", "priority": 1, "when": {"true": True}, "then": {"compress": True}}]
    d = eng(rules).decide(sig())
    assert d.route == "hot" and d.compress is False and d.rules["compress"] == "default"
    assert "  => final" in d.explanation


def test_short_circuit_and_explanation():
    e = eng([{"name": "r", "when": {"and": [{"false": True}, {"threshold": {"field": "nope", "op": "<", "value": 1}}]},
              "then": {"route": "hot"}}], strict=True)
    d = e.decide(sig())  # strict, but the missing field is never reached
    assert d.route == "cold"
    text = d.explain()
    assert "[rule r p=0]" in text and "- and" in text and "nope" not in text


def test_missing_field_nonstrict_and_strict():
    rules = [{"name": "r", "when": {"threshold": {"field": "link_util", "op": ">", "value": 0.5}}, "then": {"route": "hot"}}]
    d = eng(rules).decide(sig())
    assert d.route == "cold" and any("link_util missing" in l for l in d.explanation)
    with pytest.raises(PolicyConfigError, match="link_util"):
        eng(rules, strict=True).decide(sig())


def test_route_field_sees_decision_so_far():
    rules = [{"name": "a", "priority": 2, "when": {"true": True}, "then": {"route": "spill"}},
             {"name": "b", "priority": 1, "when": {"in": {"field": "route", "values": ["spill"]}},
              "then": {"compress": True}}]
    assert eng(rules).decide(sig()).compress is True


# ---- config validation --------------------------------------------------------------

@pytest.mark.parametrize("cfg,msg", [
    ({"rules": [{"name": "r", "when": {"treshold": {}}, "then": {"route": "hot"}}]}, "unknown node type 'treshold'"),
    ({"rules": [{"name": "r", "when": {"and": []}, "then": {"route": "hot"}}]}, "non-empty list"),
    ({"rules": [{"name": "r", "when": {"threshold": {"field": "x", "op": "~", "value": 1}}, "then": {"route": "hot"}}]}, "op"),
    ({"rules": [{"name": "r", "when": {"true": True}, "then": {"route": "warp"}}]}, "route"),
    ({"rules": [{"name": "r", "when": {"true": True}, "then": {"compress": "yes"}}]}, "compress"),
    ({"rules": [{"name": "r", "when": {"true": True}, "then": {"route": "hot", "x": 1}}]}, "unknown action keys"),
    ({"rules": [{"name": "r", "when": {"true": True}}]}, "missing"),
    ({"rules": [{"name": "r", "when": {"true": True}, "then": {"route": "hot"}},
                {"name": "r", "when": {"true": True}, "then": {"route": "hot"}}]}, "duplicate"),
    ({"rules": [{"name": "r", "priority": "high", "when": {"true": True}, "then": {"route": "hot"}}]}, "priority"),
    ({"rules": [{"name": "r", "when": {"in": {"field": "role", "values": "kv"}}, "then": {"route": "hot"}}]}, "list"),
    ({"rules": [{"name": "r", "when": {"classifier": {"name": "w", "equals": "tepid"}}, "then": {"route": "hot"}}]}, "hot/warm/cold"),
    ({"version": 2, "rules": []}, "version"),
    ({"rules": "nope"}, "rules"),
    ({"default": {"route": "hot"}, "rules": []}, "default"),
])
def test_bad_configs(cfg, msg):
    with pytest.raises(PolicyConfigError, match=msg):
        PolicyEngine(cfg)


def test_error_path_points_at_node():
    cfg = {"rules": [{"name": "ok", "when": {"true": True}, "then": {"route": "hot"}},
                     {"name": "bad", "when": {"and": [{"true": True}, {"bogus": 1}]}, "then": {"route": "hot"}}]}
    with pytest.raises(PolicyConfigError, match=r"\$\.rules\[1\]\.when\.and\[1\]"):
        PolicyEngine(cfg)


# ---- shipped default policy ----------------------------------------------------------

def test_default_policy_routes():
    e = PolicyEngine.default_policy(classifiers={"wfa": WFAClassifier()})
    ctx_idle = {"gpu_mem_util": 0.5, "link_util": 0.1}
    assert e.decide(sig(role="metadata", size_bytes=200), ctx_idle).route == "hot"
    assert e.decide(sig(role="kv", phase="decode", size_bytes=64 << 10), ctx_idle).route == "hot"
    assert e.decide(sig(role="kv", phase="prefill", size_bytes=8 << 20), ctx_idle).route == "cold"
    d = e.decide(sig(role="kv", phase="prefill", size_bytes=8 << 20), {"gpu_mem_util": 0.95, "link_util": 0.9})
    assert (d.route, d.compress) == ("spill", True)
    d = e.decide(sig(role="kv", phase="prefill", size_bytes=8 << 20), {"gpu_mem_util": 0.5, "link_util": 0.9})
    assert (d.route, d.compress) == ("cold", True)
    # decode traffic is never spilled even under pressure
    assert e.decide(sig(role="kv", phase="decode", size_bytes=1 << 20), {"gpu_mem_util": 0.99, "link_util": 0.0}).route == "cold"


def test_load_policy_file_json_and_yaml(tmp_path):
    cfg = {"rules": [{"name": "r", "when": {"true": True}, "then": {"route": "hot"}}]}
    j = tmp_path / "p.json"
    j.write_text(json.dumps(cfg))
    assert PolicyEngine.from_file(j).decide(sig()).route == "hot"
    yaml = pytest.importorskip("yaml")
    y = tmp_path / "p.yaml"
    y.write_text(yaml.safe_dump(cfg))
    assert load_policy_file(y) == cfg
