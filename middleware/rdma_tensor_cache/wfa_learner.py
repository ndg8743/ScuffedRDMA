"""
Weighted finite automaton with learned transition weights (thesis component 2).

States: cold, warm, hot (one automaton instance per tensor id). The next
state depends on the current state and the SignalVector of the transfer:

    P(s' | s, x) = softmax_{s'}( W[s, s'] . phi(x) )

phi(x) is SignalVector.features() standardized with training statistics,
plus a bias and two phase-by-size interactions (log2 size x is_prefill,
log2 size x is_decode) so a single linear map can hold a different size
cutoff per phase. W has shape (3, 3, F) and is fit by full-batch gradient
descent (Adam) on cross entropy with L2, teacher forcing the previous
state from the labels. Routing: state hot -> HOT_QP, warm/cold -> COLD_QP.

Also here:
  SyntheticTraceGenerator   prefill sweeps, decode steps, control messages,
                            bursty mixes, chunked-prefill phase switches,
                            with an oracle label per transfer
  evaluate / evaluate_static  accuracy, hot precision/recall/F1, confusion
                              matrices for the learned WFA and the static
                              threshold WFAClassifier on the same traces
  from_telemetry            training rows from Telemetry.signals()

All synthetic results are synthetic. They show the learner and the
evaluation harness work; they are not measurements of the testbed.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import numpy as np

from ..telemetry import SignalVector, Telemetry
from .dual_qp_pool import QueueSelection

STATES = ("cold", "warm", "hot")
S_IDX = {s: i for i, s in enumerate(STATES)}

Label = str  # "cold" | "warm" | "hot"
Trace = List[Tuple[SignalVector, Label]]


def _key(sig: SignalVector) -> str:
    return sig.tensor_id or f"role:{sig.role}"


def oracle_label(sig: SignalVector) -> Label:
    """
    Ground-truth routing used by the synthetic generator.

    hot  : on the decode critical path and small enough to be latency bound
           (token ids, scheduler metadata, decode KV deltas up to 256 KiB)
    warm : recurring but not latency critical (decode prefix fetches over
           256 KiB, small prefill chunks up to 64 KiB)
    cold : bulk (prefill KV over 64 KiB, weights, SSM state snapshots)
    """
    if sig.role in ("token", "metadata"):
        return "hot"
    if sig.role in ("weight", "state"):
        return "cold"
    if sig.phase == "decode":
        return "hot" if sig.size_bytes <= 256 * 1024 else "warm"
    if sig.phase == "prefill":
        return "warm" if sig.size_bytes <= 64 * 1024 else "cold"
    return "warm" if sig.size_bytes <= 256 * 1024 else "cold"


# ---------------------------------------------------------------------------
# Synthetic traces
# ---------------------------------------------------------------------------

@dataclass
class ModelShape:
    layers: int = 40
    kv_heads: int = 8
    head_dim: int = 64
    dtype_bytes: int = 2

    @property
    def kv_bytes_per_token_layer(self) -> int:
        return 2 * self.kv_heads * self.head_dim * self.dtype_bytes


@dataclass
class SyntheticTraceGenerator:
    """
    Event-level synthetic traffic for one prefill/decode pair.

    Patterns (weights in `mix`):
      prefill   one request: layers 0..L-1 in order, KV block = seq_len tokens
      decode    one step: each layer gets a KV delta of `block_tokens` tokens,
                occasional prefix fetch (256 KiB - 4 MiB)
      control   bursts of token ids / scheduler metadata (32 B - 2 KiB)
      bursty    mixed prefill + decode + control with deep queues
      chunked   chunked prefill: prefill chunks interleaved with decode steps
    """

    seed: int = 0
    model: ModelShape = field(default_factory=ModelShape)
    seq_len_range: Tuple[int, int] = (128, 8192)
    block_tokens_range: Tuple[int, int] = (1, 64)
    prefix_fetch_prob: float = 0.25

    def __post_init__(self):
        self._rng = np.random.default_rng(self.seed)
        self._t = 0.0
        self._req = 0
        self._last_seen: Dict[str, float] = {}
        self._count: Dict[str, int] = {}

    # -- helpers ---------------------------------------------------------------
    def _tick(self, us: float) -> float:
        self._t += us * 1e-6
        return self._t

    def _sig(self, size: int, role: str, phase: str, tensor_id: str, layer: int,
             seq_len: int, qdepth: int, dt_us: float) -> SignalVector:
        t = self._tick(dt_us)
        n = self._count.get(tensor_id, 0) + 1
        self._count[tensor_id] = n
        last = self._last_seen.get(tensor_id)
        self._last_seen[tensor_id] = t
        ia = (t - last) * 1e6 if last is not None else float("nan")
        freq = 0.0 if last is None else min(1e6 / max(ia, 1.0), 1e5)
        return SignalVector(size_bytes=int(max(size, 1)), role=role, access_freq=freq,
                            tensor_id=tensor_id, layer_idx=layer, queue_depth=int(qdepth),
                            phase=phase, seq_len=int(seq_len), inter_arrival_us=ia,
                            timestamp=t)

    def _seq_len(self) -> int:
        lo, hi = self.seq_len_range
        return int(math.exp(self._rng.uniform(math.log(lo), math.log(hi))))

    # -- patterns ----------------------------------------------------------------
    def _prefill(self, qbase: int) -> Trace:
        self._req += 1
        r = self._req
        L = self.model.layers
        seq = self._seq_len()
        out: Trace = []
        out.append(self._emit(self._rng.integers(64, 512), "metadata", "prefill", f"meta:{r}", -1, seq, qbase, 5))
        for l in range(L):
            size = seq * self.model.kv_bytes_per_token_layer
            size = int(size * self._rng.uniform(0.9, 1.1))
            out.append(self._emit(size, "kv", "prefill", f"kv:{r}:{l}", l, seq, qbase + self._rng.integers(0, 4),
                                  self._rng.uniform(20, 200)))
        return out

    def _decode(self, qbase: int, steps: int) -> Trace:
        self._req += 1
        r = self._req
        L = self.model.layers
        seq = self._seq_len()
        out: Trace = []
        for _ in range(steps):
            out.append(self._emit(self._rng.integers(8, 64), "token", "decode", f"tok:{r}", -1, seq, qbase, 30))
            bt = int(self._rng.integers(*self.block_tokens_range))
            for l in range(L):
                size = bt * self.model.kv_bytes_per_token_layer
                out.append(self._emit(size, "kv", "decode", f"kv:{r}:{l}", l, seq, qbase + self._rng.integers(0, 3),
                                      self._rng.uniform(2, 20)))
                if self._rng.random() < self.prefix_fetch_prob / L:
                    pf = int(math.exp(self._rng.uniform(math.log(256 * 1024 + 1), math.log(4 << 20))))
                    out.append(self._emit(pf, "kv", "decode", f"prefix:{r}:{l}", l, seq, qbase + 2, 10))
            seq += bt
        return out

    def _control(self, qbase: int, n: int) -> Trace:
        out: Trace = []
        for i in range(n):
            role = "token" if self._rng.random() < 0.5 else "metadata"
            out.append(self._emit(self._rng.integers(32, 2048), role, "decode" if role == "token" else "unknown",
                                  f"{role}:{self._rng.integers(0, 16)}", -1, 0, qbase, self._rng.uniform(1, 50)))
        return out

    def _weights_or_state(self, qbase: int) -> Trace:
        role = "weight" if self._rng.random() < 0.5 else "state"
        size = int(math.exp(self._rng.uniform(math.log(64 * 1024), math.log(64 << 20))))
        return [self._emit(size, role, "unknown", f"{role}:{self._rng.integers(0, 8)}", -1, 0, qbase, 100)]

    def _emit(self, size, role, phase, tid, layer, seq, q, dt) -> Tuple[SignalVector, Label]:
        sig = self._sig(int(size), role, phase, tid, int(layer), int(seq), int(q), float(dt))
        return sig, oracle_label(sig)

    def generate(self, n_events: int, mix: Optional[Dict[str, float]] = None) -> Trace:
        mix = mix or {"prefill": 0.3, "decode": 0.4, "control": 0.2, "bursty": 0.05, "chunked": 0.05}
        names = list(mix)
        p = np.array([mix[k] for k in names], dtype=float)
        p = p / p.sum()
        out: Trace = []
        while len(out) < n_events:
            pat = names[int(self._rng.choice(len(names), p=p))]
            if pat == "prefill":
                out += self._prefill(qbase=int(self._rng.integers(0, 3)))
            elif pat == "decode":
                out += self._decode(qbase=int(self._rng.integers(0, 3)), steps=int(self._rng.integers(4, 33)))
            elif pat == "control":
                out += self._control(qbase=int(self._rng.integers(0, 3)), n=int(self._rng.integers(4, 32)))
            elif pat == "bursty":
                q = int(self._rng.integers(16, 64))
                out += self._control(q, int(self._rng.integers(8, 32)))
                out += self._prefill(q)
                out += self._decode(q, 2)
                out += self._weights_or_state(q)
            elif pat == "chunked":
                for _ in range(int(self._rng.integers(2, 5))):
                    saved = self.seq_len_range
                    self.seq_len_range = (64, 512)  # small chunks
                    out += self._prefill(1)
                    self.seq_len_range = saved
                    out += self._decode(1, 1)
            elif pat == "weights":
                out += self._weights_or_state(int(self._rng.integers(0, 3)))
            else:
                raise ValueError(f"unknown pattern {pat!r}")
        return out[:n_events]


# ---------------------------------------------------------------------------
# Learned WFA
# ---------------------------------------------------------------------------

def _phi_raw(sig: SignalVector) -> np.ndarray:
    f = sig.features()
    log2_size, is_prefill, is_decode = f[0], f[3], f[4]
    return np.array(f + [log2_size * is_prefill, log2_size * is_decode], dtype=np.float64)


PHI_NAMES = tuple(SignalVector.FEATURE_NAMES) + ("log2_size_x_prefill", "log2_size_x_decode")


class LearnedWFA:
    """Three-state WFA whose transition weights are learned from labeled traces."""

    def __init__(self, l2: float = 1e-3, lr: float = 0.05, epochs: int = 400, seed: int = 0):
        self.l2, self.lr, self.epochs, self.seed = l2, lr, epochs, seed
        self.W: Optional[np.ndarray] = None   # (3, 3, F+1) incl. bias
        self.mu: Optional[np.ndarray] = None
        self.sd: Optional[np.ndarray] = None
        self.loss_history: List[float] = []
        self._state: Dict[str, int] = {}

    # -- data -------------------------------------------------------------------
    @staticmethod
    def _rows(traces: Iterable[Trace]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        X, prev, y = [], [], []
        for tr in traces:
            state: Dict[str, int] = {}
            for sig, lab in tr:
                k = _key(sig)
                X.append(_phi_raw(sig))
                prev.append(state.get(k, S_IDX["cold"]))
                yi = S_IDX[lab]
                y.append(yi)
                state[k] = yi
        return np.asarray(X), np.asarray(prev, dtype=np.int64), np.asarray(y, dtype=np.int64)

    def _design(self, Xraw: np.ndarray) -> np.ndarray:
        Z = (Xraw - self.mu) / self.sd
        return np.hstack([Z, np.ones((Z.shape[0], 1))])

    # -- training ---------------------------------------------------------------
    def fit(self, traces: Sequence[Trace]) -> "LearnedWFA":
        Xraw, prev, y = self._rows(traces)
        if len(y) == 0:
            raise ValueError("no training rows")
        self.mu = Xraw.mean(axis=0)
        self.sd = Xraw.std(axis=0)
        self.sd[self.sd < 1e-9] = 1.0
        X = self._design(Xraw)
        n, F = X.shape
        rng = np.random.default_rng(self.seed)
        W = rng.normal(0, 0.01, size=(3, 3, F))
        m = np.zeros_like(W)
        v = np.zeros_like(W)
        b1, b2, eps = 0.9, 0.999, 1e-8
        Y = np.zeros((n, 3))
        Y[np.arange(n), y] = 1.0
        self.loss_history = []
        for t in range(1, self.epochs + 1):
            logits = np.einsum("nf,nkf->nk", X, W[prev])          # (n, 3)
            logits -= logits.max(axis=1, keepdims=True)
            P = np.exp(logits)
            P /= P.sum(axis=1, keepdims=True)
            loss = -np.log(P[np.arange(n), y] + 1e-12).mean() + 0.5 * self.l2 * (W ** 2).sum()
            self.loss_history.append(float(loss))
            G = (P - Y) / n                                       # (n, 3)
            grad = np.zeros_like(W)
            for s in range(3):
                idx = prev == s
                if idx.any():
                    grad[s] = G[idx].T @ X[idx]                   # (3, F)
            grad += self.l2 * W
            m = b1 * m + (1 - b1) * grad
            v = b2 * v + (1 - b2) * grad ** 2
            W -= self.lr * (m / (1 - b1 ** t)) / (np.sqrt(v / (1 - b2 ** t)) + eps)
        self.W = W
        self._state.clear()
        return self

    # -- inference --------------------------------------------------------------
    def _check(self):
        if self.W is None:
            raise RuntimeError("LearnedWFA is not fitted; call fit() or load()")

    def transition_probs(self, sig: SignalVector, state: Optional[str] = None) -> np.ndarray:
        self._check()
        s = S_IDX[state] if state is not None else self._state.get(_key(sig), S_IDX["cold"])
        x = self._design(_phi_raw(sig)[None, :])[0]
        z = self.W[s] @ x
        z -= z.max()
        p = np.exp(z)
        return p / p.sum()

    def predict_state(self, sig: SignalVector, update: bool = True) -> Label:
        p = self.transition_probs(sig)
        nxt = int(np.argmax(p))
        if update:
            self._state[_key(sig)] = nxt
        return STATES[nxt]

    def classify(self, sig: SignalVector) -> QueueSelection:
        return QueueSelection.HOT_QP if self.predict_state(sig) == "hot" else QueueSelection.COLD_QP

    def reset(self) -> None:
        self._state.clear()

    def feature_weights(self) -> Dict[str, Dict[str, List[float]]]:
        """W[s, s', :] keyed by current state then next state, feature order PHI_NAMES + bias."""
        self._check()
        return {STATES[s]: {STATES[k]: self.W[s, k].tolist() for k in range(3)} for s in range(3)}

    # -- persistence ------------------------------------------------------------
    def to_dict(self) -> dict:
        self._check()
        return {"format": "scuffed-learned-wfa/1", "states": list(STATES), "features": list(PHI_NAMES) + ["bias"],
                "W": self.W.tolist(), "mu": self.mu.tolist(), "sd": self.sd.tolist(),
                "l2": self.l2, "lr": self.lr, "epochs": self.epochs, "seed": self.seed}

    def save(self, path: str) -> str:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f)
        return path

    @classmethod
    def from_dict(cls, d: dict) -> "LearnedWFA":
        if d.get("format") != "scuffed-learned-wfa/1":
            raise ValueError("not a learned WFA weight file")
        m = cls(l2=d["l2"], lr=d["lr"], epochs=d["epochs"], seed=d["seed"])
        m.W = np.asarray(d["W"], dtype=np.float64)
        m.mu = np.asarray(d["mu"], dtype=np.float64)
        m.sd = np.asarray(d["sd"], dtype=np.float64)
        if m.W.shape != (3, 3, len(PHI_NAMES) + 1):
            raise ValueError(f"weight shape {m.W.shape} does not match features")
        return m

    @classmethod
    def load(cls, path: str) -> "LearnedWFA":
        with open(path) as f:
            return cls.from_dict(json.load(f))


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _binary_metrics(y_true_hot: np.ndarray, y_pred_hot: np.ndarray) -> Dict[str, float]:
    tp = int(np.sum(y_true_hot & y_pred_hot))
    fp = int(np.sum(~y_true_hot & y_pred_hot))
    fn = int(np.sum(y_true_hot & ~y_pred_hot))
    tn = int(np.sum(~y_true_hot & ~y_pred_hot))
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if (tp and prec + rec) else 0.0
    return {"routing_accuracy": (tp + tn) / max(tp + tn + fp + fn, 1), "hot_precision": prec,
            "hot_recall": rec, "hot_f1": f1, "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def evaluate(model: LearnedWFA, traces: Sequence[Trace]) -> Dict[str, object]:
    """Online evaluation: the model carries its own predicted state per tensor id."""
    model.reset()
    yt, yp = [], []
    for tr in traces:
        for sig, lab in tr:
            yt.append(S_IDX[lab])
            yp.append(S_IDX[model.predict_state(sig)])
    yt_a, yp_a = np.asarray(yt), np.asarray(yp)
    cm = np.zeros((3, 3), dtype=int)
    for a, b in zip(yt_a, yp_a):
        cm[a, b] += 1
    out = {"n": len(yt), "state_accuracy": float((yt_a == yp_a).mean()) if len(yt) else float("nan"),
           "confusion_states": cm.tolist(), "states": list(STATES)}
    out.update(_binary_metrics(yt_a == S_IDX["hot"], yp_a == S_IDX["hot"]))
    model.reset()
    return out


def evaluate_static(traces: Sequence[Trace], classifier=None) -> Dict[str, object]:
    """Binary routing metrics for the static threshold WFAClassifier on the same traces."""
    from .wfa_classifier import WFAClassifier
    clf = classifier or WFAClassifier()
    yt, yp = [], []
    for tr in traces:
        for sig, lab in tr:
            q = clf.classify(_key(sig), sig.size_bytes, sig.layer_idx if sig.layer_idx >= 0 else None)
            yt.append(lab == "hot")
            yp.append(q == QueueSelection.HOT_QP)
    yt_a, yp_a = np.asarray(yt, dtype=bool), np.asarray(yp, dtype=bool)
    out = {"n": len(yt)}
    out.update(_binary_metrics(yt_a, yp_a))
    out["confusion_binary"] = [[out["tn"], out["fp"]], [out["fn"], out["tp"]]]
    return out


# ---------------------------------------------------------------------------
# Telemetry bridge
# ---------------------------------------------------------------------------

LabelFn = Callable[[SignalVector], Union[str, bool, QueueSelection]]


def _norm_label(v: Union[str, bool, QueueSelection]) -> Label:
    if isinstance(v, QueueSelection):
        return "hot" if v == QueueSelection.HOT_QP else "cold"
    if isinstance(v, bool):
        return "hot" if v else "cold"
    v = str(v).lower()
    if v not in S_IDX:
        raise ValueError(f"label must be one of {STATES}, got {v!r}")
    return v


def from_telemetry(tel: Telemetry, label_fn: LabelFn = oracle_label) -> List[Trace]:
    """One trace (in arrival order) from the telemetry signal ring, labeled by label_fn."""
    sigs = sorted(tel.signals(), key=lambda s: s.timestamp)
    return [[(s, _norm_label(label_fn(s))) for s in sigs]]


def latency_label(threshold_us: float) -> LabelFn:
    """Label from measured completion latency: hot if the transfer completed under threshold_us
    on a hot-class QP (useful when replaying real telemetry without an oracle)."""
    def fn(s: SignalVector) -> Label:
        if s.role in ("token", "metadata"):
            return "hot"
        if not math.isnan(s.completion_us) and s.completion_us <= threshold_us and s.size_bytes <= 256 * 1024:
            return "hot"
        return "cold" if s.size_bytes > 64 * 1024 else "warm"
    return fn
