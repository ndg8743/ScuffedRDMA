"""
Rule-Node Expression Trees: boolean routing policy for libscuffedrdma (thesis component 3).

Modeled on the vLLM Semantic Router's rule composition: each rule is a
boolean expression tree over signals, rules are tried in priority order,
and the first rule to set a decision field owns it. Here the signals are a
SignalVector (middleware/telemetry.py) plus a context dict (GPU memory
utilization, link utilization, anything the caller measures), and the
decision is a route (hot / cold / spill) and a compress flag.

Config (dict, JSON, or YAML when PyYAML is installed):

    {"version": 1, "name": "...",
     "default": {"route": "cold", "compress": false},
     "rules": [
        {"name": "control-hot", "priority": 100,
         "when": {"in": {"field": "role", "values": ["metadata", "token"]}},
         "then": {"route": "hot"},
         "final": false}
     ]}

Node types inside "when":
    {"and": [node, ...]}        all true (short-circuits on first false)
    {"or":  [node, ...]}        any true (short-circuits on first true)
    {"not": node}
    {"threshold": {"field": f, "op": "<|<=|>|>=|==|!=", "value": v}}
    {"in": {"field": f, "values": [...]}}
    {"classifier": {"name": n, "equals": "hot|warm|cold"}}   calls a registered classifier
    {"true": true} / {"false": true}                        constants (tests, catch-alls)
"then" is the ACTION node: {"route": "hot|cold|spill", "compress": bool} (either key optional).

Fields resolve from the context dict first, then SignalVector attributes,
then derived fields: log2_size, route (decision so far, else default).
A missing field makes its leaf false and is recorded in the explanation;
PolicyEngine(strict=True) raises instead.

Rule evaluation order: priority descending, then file order. A rule that
matches fills only decision fields not yet set; "final": true stops
evaluation after it. Unset fields take the default. Classifier leaves are
called at most once per decide() (their state changes are not repeated).
A classifier leaf whose name is not registered is false (strict: error);
when classifiers are registered, unknown names are rejected at load time.
"""

from __future__ import annotations

import json
import math
import operator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Union

from ..telemetry import SignalVector

ROUTES = ("hot", "cold", "spill")
OPS: Dict[str, Callable[[Any, Any], bool]] = {
    "<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge,
    "==": operator.eq, "!=": operator.ne,
}
NODE_KEYS = ("and", "or", "not", "threshold", "in", "classifier", "true", "false")


class PolicyConfigError(ValueError):
    """Bad policy config. Message starts with the JSON path of the offending node."""


class MissingField(KeyError):
    pass


# ---------------------------------------------------------------------------
# Evaluation context
# ---------------------------------------------------------------------------

@dataclass
class EvalContext:
    sig: SignalVector
    ctx: Mapping[str, Any]
    decision: Dict[str, Any]
    default: Dict[str, Any]
    classifiers: Mapping[str, Callable[[SignalVector], str]]
    strict: bool
    trace: List[str] = field(default_factory=list)
    _clf_cache: Dict[str, str] = field(default_factory=dict)

    def field(self, name: str) -> Any:
        if name in self.ctx:
            return self.ctx[name]
        if hasattr(self.sig, name):
            return getattr(self.sig, name)
        if name == "log2_size":
            return math.log2(max(self.sig.size_bytes, 1))
        if name == "route":
            return self.decision.get("route", self.default.get("route"))
        if name == "compress":
            return self.decision.get("compress", self.default.get("compress"))
        raise MissingField(name)

    def classify(self, name: str) -> str:
        if name not in self._clf_cache:
            self._clf_cache[name] = str(self.classifiers[name](self.sig)).lower()
        return self._clf_cache[name]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

class Node:
    path: str = ""

    def eval(self, ec: EvalContext, depth: int = 0) -> bool:
        raise NotImplementedError

    def _log(self, ec: EvalContext, depth: int, ok: bool, what: str) -> bool:
        ec.trace.append(f"{'  ' * depth}{'+' if ok else '-'} {what}")
        return ok


@dataclass
class And(Node):
    children: List[Node]
    path: str = ""

    def eval(self, ec, depth=0):
        idx = len(ec.trace)
        ec.trace.append("")
        ok = True
        for c in self.children:
            if not c.eval(ec, depth + 1):
                ok = False
                break
        ec.trace[idx] = f"{'  ' * depth}{'+' if ok else '-'} and"
        return ok


@dataclass
class Or(Node):
    children: List[Node]
    path: str = ""

    def eval(self, ec, depth=0):
        idx = len(ec.trace)
        ec.trace.append("")
        ok = False
        for c in self.children:
            if c.eval(ec, depth + 1):
                ok = True
                break
        ec.trace[idx] = f"{'  ' * depth}{'+' if ok else '-'} or"
        return ok


@dataclass
class Not(Node):
    child: Node
    path: str = ""

    def eval(self, ec, depth=0):
        idx = len(ec.trace)
        ec.trace.append("")
        ok = not self.child.eval(ec, depth + 1)
        ec.trace[idx] = f"{'  ' * depth}{'+' if ok else '-'} not"
        return ok


@dataclass
class Const(Node):
    value: bool
    path: str = ""

    def eval(self, ec, depth=0):
        return self._log(ec, depth, self.value, str(self.value).lower())


def _get(ec: EvalContext, name: str, depth: int, node: Node) -> Any:
    try:
        return ec.field(name)
    except MissingField:
        if ec.strict:
            raise PolicyConfigError(f"{node.path}: field {name!r} not in signal or context")
        ec.trace.append(f"{'  ' * depth}- {name} missing")
        return MissingField


@dataclass
class Threshold(Node):
    fld: str
    op: str
    value: Any
    path: str = ""

    def eval(self, ec, depth=0):
        v = _get(ec, self.fld, depth, self)
        if v is MissingField:
            return False
        try:
            ok = bool(OPS[self.op](v, self.value))
        except TypeError:
            ok = False
        return self._log(ec, depth, ok, f"{self.fld}={_fmt(v)} {self.op} {_fmt(self.value)}")


@dataclass
class In(Node):
    fld: str
    values: Sequence[Any]
    path: str = ""

    def eval(self, ec, depth=0):
        v = _get(ec, self.fld, depth, self)
        if v is MissingField:
            return False
        ok = v in self.values
        return self._log(ec, depth, ok, f"{self.fld}={_fmt(v)} in {list(self.values)}")


@dataclass
class Classifier(Node):
    name: str
    equals: str
    path: str = ""

    def eval(self, ec, depth=0):
        if self.name not in ec.classifiers:
            if ec.strict:
                raise PolicyConfigError(f"{self.path}: classifier {self.name!r} is not registered")
            return self._log(ec, depth, False, f"classifier {self.name} not registered")
        got = ec.classify(self.name)
        ok = got == self.equals
        return self._log(ec, depth, ok, f"classifier {self.name} -> {got} (want {self.equals})")


@dataclass
class Action:
    route: Optional[str] = None
    compress: Optional[bool] = None

    def fields(self) -> Dict[str, Any]:
        return {k: v for k, v in (("route", self.route), ("compress", self.compress)) if v is not None}


@dataclass
class Rule:
    name: str
    priority: int
    when: Node
    then: Action
    final: bool = False
    order: int = 0


@dataclass
class Decision:
    route: str
    compress: bool
    rules: Dict[str, str]           # decision field -> rule that set it ("default" otherwise)
    explanation: List[str]

    def explain(self) -> str:
        return "\n".join(self.explanation)


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.4g}"
    return repr(v) if isinstance(v, str) else str(v)


# ---------------------------------------------------------------------------
# Parsing / validation
# ---------------------------------------------------------------------------

def _parse_node(d: Any, path: str, classifier_names: Optional[Sequence[str]]) -> Node:
    if not isinstance(d, Mapping) or len(d) != 1:
        raise PolicyConfigError(f"{path}: a node is an object with exactly one key from {NODE_KEYS}")
    (k, v), = d.items()
    if k in ("and", "or"):
        if not isinstance(v, list) or not v:
            raise PolicyConfigError(f"{path}.{k}: expects a non-empty list")
        kids = [_parse_node(c, f"{path}.{k}[{i}]", classifier_names) for i, c in enumerate(v)]
        return (And if k == "and" else Or)(kids, path=path)
    if k == "not":
        return Not(_parse_node(v, f"{path}.not", classifier_names), path=path)
    if k in ("true", "false"):
        return Const(k == "true", path=path)
    if k == "threshold":
        if not isinstance(v, Mapping) or not {"field", "op", "value"} <= set(v):
            raise PolicyConfigError(f"{path}.threshold: needs field, op, value")
        if v["op"] not in OPS:
            raise PolicyConfigError(f"{path}.threshold.op: {v['op']!r} not one of {list(OPS)}")
        return Threshold(str(v["field"]), v["op"], v["value"], path=path)
    if k == "in":
        if not isinstance(v, Mapping) or "field" not in v or not isinstance(v.get("values"), list):
            raise PolicyConfigError(f"{path}.in: needs field and a list of values")
        return In(str(v["field"]), tuple(v["values"]), path=path)
    if k == "classifier":
        if not isinstance(v, Mapping) or "name" not in v or "equals" not in v:
            raise PolicyConfigError(f"{path}.classifier: needs name and equals")
        if v["equals"] not in ("hot", "warm", "cold"):
            raise PolicyConfigError(f"{path}.classifier.equals: {v['equals']!r} not hot/warm/cold")
        if classifier_names is not None and v["name"] not in classifier_names:
            raise PolicyConfigError(f"{path}.classifier.name: {v['name']!r} is not registered "
                                    f"(have {sorted(classifier_names)})")
        return Classifier(str(v["name"]), str(v["equals"]), path=path)
    raise PolicyConfigError(f"{path}: unknown node type {k!r} (expected one of {NODE_KEYS})")


def _parse_action(d: Any, path: str) -> Action:
    if not isinstance(d, Mapping) or not d:
        raise PolicyConfigError(f"{path}: action needs route and/or compress")
    extra = set(d) - {"route", "compress"}
    if extra:
        raise PolicyConfigError(f"{path}: unknown action keys {sorted(extra)}")
    route = d.get("route")
    if route is not None and route not in ROUTES:
        raise PolicyConfigError(f"{path}.route: {route!r} not one of {ROUTES}")
    comp = d.get("compress")
    if comp is not None and not isinstance(comp, bool):
        raise PolicyConfigError(f"{path}.compress: must be true or false")
    return Action(route=route, compress=comp)


def parse_policy(cfg: Mapping[str, Any], classifier_names: Optional[Sequence[str]] = None):
    if not isinstance(cfg, Mapping):
        raise PolicyConfigError("$: policy must be an object")
    if cfg.get("version", 1) != 1:
        raise PolicyConfigError(f"$.version: unsupported {cfg.get('version')!r}")
    default = _parse_action(cfg.get("default", {"route": "cold", "compress": False}), "$.default")
    if default.route is None or default.compress is None:
        raise PolicyConfigError("$.default: must set both route and compress")
    rules_cfg = cfg.get("rules")
    if not isinstance(rules_cfg, list):
        raise PolicyConfigError("$.rules: expects a list")
    rules, seen = [], set()
    for i, r in enumerate(rules_cfg):
        p = f"$.rules[{i}]"
        if not isinstance(r, Mapping):
            raise PolicyConfigError(f"{p}: rule must be an object")
        missing = {"name", "when", "then"} - set(r)
        if missing:
            raise PolicyConfigError(f"{p}: missing {sorted(missing)}")
        if r["name"] in seen:
            raise PolicyConfigError(f"{p}.name: duplicate rule name {r['name']!r}")
        seen.add(r["name"])
        pr = r.get("priority", 0)
        if not isinstance(pr, int) or isinstance(pr, bool):
            raise PolicyConfigError(f"{p}.priority: must be an integer")
        rules.append(Rule(name=str(r["name"]), priority=pr,
                          when=_parse_node(r["when"], f"{p}.when", classifier_names),
                          then=_parse_action(r["then"], f"{p}.then"),
                          final=bool(r.get("final", False)), order=i))
    rules.sort(key=lambda r: (-r.priority, r.order))
    return str(cfg.get("name", "policy")), default, rules


def load_policy_file(path: Union[str, Path]) -> Dict[str, Any]:
    p = Path(path)
    text = p.read_text()
    if p.suffix in (".yaml", ".yml"):
        try:
            import yaml  # optional
        except ImportError as e:  # pragma: no cover
            raise PolicyConfigError(f"{p}: PyYAML not installed; use JSON") from e
        return yaml.safe_load(text)
    return json.loads(text)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

ClassifierLike = Any


def adapt_classifier(clf: ClassifierLike) -> Callable[[SignalVector], str]:
    """Wrap WFAClassifier, LearnedWFA, or a callable(sig) -> str|QueueSelection into sig -> 'hot'|'warm'|'cold'."""
    from ..rdma_tensor_cache.dual_qp_pool import QueueSelection

    def norm(v: Any) -> str:
        if isinstance(v, QueueSelection):
            return "hot" if v == QueueSelection.HOT_QP else "cold"
        return str(v).lower()

    if hasattr(clf, "predict_state"):            # LearnedWFA
        return lambda sig: clf.predict_state(sig)
    if hasattr(clf, "classify") and hasattr(clf, "phase"):   # static WFAClassifier
        return lambda sig: norm(clf.classify(sig.tensor_id or sig.role, sig.size_bytes,
                                             sig.layer_idx if sig.layer_idx >= 0 else None))
    if callable(clf):
        return lambda sig: norm(clf(sig))
    raise TypeError(f"cannot use {type(clf).__name__} as a policy classifier")


class PolicyEngine:
    def __init__(self, config: Mapping[str, Any], classifiers: Optional[Mapping[str, ClassifierLike]] = None,
                 strict: bool = False):
        self.classifiers = {k: adapt_classifier(v) for k, v in (classifiers or {}).items()}
        self.name, self.default, self.rules = parse_policy(
            config, classifier_names=list(self.classifiers) if self.classifiers else None)
        self.strict = strict
        self.config = dict(config)

    @classmethod
    def from_file(cls, path: Union[str, Path], **kw) -> "PolicyEngine":
        return cls(load_policy_file(path), **kw)

    @classmethod
    def default_policy(cls, **kw) -> "PolicyEngine":
        return cls.from_file(Path(__file__).with_name("default_policy.json"), **kw)

    def decide(self, sig: SignalVector, context: Optional[Mapping[str, Any]] = None) -> Decision:
        dflt = self.default.fields()
        ec = EvalContext(sig=sig, ctx=dict(context or {}), decision={}, default=dflt,
                         classifiers=self.classifiers, strict=self.strict)
        owners: Dict[str, str] = {}
        for r in self.rules:
            if all(k in ec.decision for k in ("route", "compress")):
                ec.trace.append(f"[stop] all fields decided before {r.name}")
                break
            ec.trace.append(f"[rule {r.name} p={r.priority}]")
            if r.when.eval(ec, 1):
                newly = {k: v for k, v in r.then.fields().items() if k not in ec.decision}
                ec.decision.update(newly)
                for k in newly:
                    owners[k] = r.name
                ec.trace.append(f"  => matched, sets {newly or 'nothing new'}")
                if r.final:
                    ec.trace.append("  => final")
                    break
        for k, v in dflt.items():
            if k not in ec.decision:
                ec.decision[k] = v
                owners[k] = "default"
        return Decision(route=ec.decision["route"], compress=bool(ec.decision["compress"]),
                        rules=owners, explanation=ec.trace)

    def decide_many(self, sigs: Sequence[SignalVector], context: Optional[Mapping[str, Any]] = None) -> List[Decision]:
        return [self.decide(s, context) for s in sigs]
