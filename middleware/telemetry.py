"""
Unified telemetry for libscuffedrdma.

One place where every transport (pyverbs dual QP pool, libfabric pool,
native C benchmarks via JSON import) reports what it saw, so the WFA
classifier, the policy tree, and the evaluation chapter all read the same
numbers.

Three things live here:

  SignalVector      one observation per transfer: transfer-intrinsic
                    (size, role, access frequency), transport-layer (QP
                    class, queue depth, completion latency), workload
                    context (phase, sequence length), temporal (inter-arrival).
  LatencyHistogram  log-bucketed latency histogram with exact percentiles
                    over a bounded reservoir. p50/p95/p99/p99.9 in microseconds.
  Telemetry         per-traffic-class counters (ops, bytes, errors, QP
                    error/reconnect, TCP fallback), latency histograms,
                    queue-depth gauges, a bounded signal ring for classifier
                    training, JSON snapshot, and Prometheus text exposition
                    (optionally served over HTTP on /metrics).

No third-party dependencies. Thread-safe.
"""

from __future__ import annotations

import bisect
import json
import math
import os
import random
import socket
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Deque, Dict, Iterable, List, Optional

# Event kinds counted per class. Anything else passed to event() is
# counted under its own name too, these are just the ones exported with
# HELP text.
EVENT_KINDS = {
    "qp_error": "QP moved to error state",
    "reconnect": "QP or endpoint re-established after an error",
    "tcp_fallback": "transfer fell back to TCP",
    "timeout": "completion not seen before deadline",
    "retry": "work request re-posted",
}


@dataclass
class SignalVector:
    """One per-transfer observation. Field groups follow the thesis signal space."""

    # transfer-intrinsic
    size_bytes: int
    role: str = "kv"              # kv, metadata, token, weight, state
    access_freq: float = 0.0      # accesses per second for this tensor id
    tensor_id: str = ""
    layer_idx: int = -1
    # transport-layer
    qp_class: str = ""            # hot / cold / single
    queue_depth: int = 0
    completion_us: float = float("nan")
    # workload context
    phase: str = "unknown"        # prefill / decode / unknown
    seq_len: int = 0
    # temporal / derived
    inter_arrival_us: float = float("nan")
    timestamp: float = field(default_factory=time.monotonic)

    def features(self) -> List[float]:
        """Numeric feature vector for learned classifiers (stable order)."""
        return [
            math.log2(max(self.size_bytes, 1)),
            float(self.access_freq),
            float(self.queue_depth),
            1.0 if self.phase == "prefill" else 0.0,
            1.0 if self.phase == "decode" else 0.0,
            math.log2(max(self.seq_len, 1)),
            0.0 if math.isnan(self.inter_arrival_us) else math.log2(max(self.inter_arrival_us, 1.0)),
            1.0 if self.role in ("metadata", "token") else 0.0,
        ]

    FEATURE_NAMES = (
        "log2_size", "access_freq", "queue_depth", "is_prefill",
        "is_decode", "log2_seq_len", "log2_inter_arrival_us", "is_control",
    )


class LatencyHistogram:
    """
    Log-spaced buckets (for Prometheus) plus a uniform reservoir (for exact-ish
    percentiles once the sample count exceeds the reservoir).
    """

    # 0.5 us .. ~16 s, factor sqrt(2): enough resolution for SoftRoCE and NVMe.
    DEFAULT_BOUNDS = tuple(0.5 * (2 ** (i / 2)) for i in range(0, 51))

    def __init__(self, bounds: Iterable[float] = DEFAULT_BOUNDS, reservoir: int = 65536,
                 seed: int = 0):
        self.bounds = tuple(sorted(bounds))
        self.counts = [0] * (len(self.bounds) + 1)
        self.n = 0
        self.total = 0.0
        self.min = math.inf
        self.max = -math.inf
        self._res: List[float] = []
        self._res_cap = reservoir
        self._rng = random.Random(seed)

    def add(self, v: float) -> None:
        if v != v:  # NaN
            return
        self.counts[bisect.bisect_left(self.bounds, v)] += 1
        self.n += 1
        self.total += v
        self.min = min(self.min, v)
        self.max = max(self.max, v)
        if len(self._res) < self._res_cap:
            self._res.append(v)
        else:
            j = self._rng.randrange(self.n)
            if j < self._res_cap:
                self._res[j] = v

    def extend(self, vs: Iterable[float]) -> None:
        for v in vs:
            self.add(v)

    def percentile(self, p: float) -> float:
        if not self._res:
            return float("nan")
        s = sorted(self._res)
        k = (len(s) - 1) * (p / 100.0)
        lo, hi = math.floor(k), math.ceil(k)
        if lo == hi:
            return s[int(k)]
        return s[lo] + (s[hi] - s[lo]) * (k - lo)

    @property
    def mean(self) -> float:
        return self.total / self.n if self.n else float("nan")

    def summary(self) -> Dict[str, float]:
        return {
            "count": self.n,
            "mean_us": self.mean,
            "min_us": self.min if self.n else float("nan"),
            "p50_us": self.percentile(50),
            "p95_us": self.percentile(95),
            "p99_us": self.percentile(99),
            "p999_us": self.percentile(99.9),
            "max_us": self.max if self.n else float("nan"),
        }


@dataclass
class ClassStats:
    ops: int = 0
    bytes: int = 0
    errors: int = 0
    events: Dict[str, int] = field(default_factory=dict)
    queue_depth: int = 0
    queue_depth_max: int = 0
    latency: LatencyHistogram = field(default_factory=LatencyHistogram)


class Telemetry:
    """Per-traffic-class telemetry. Classes are free-form strings (hot, cold, single, storage)."""

    def __init__(self, node: Optional[str] = None, signal_capacity: int = 100_000):
        self.node = node or socket.gethostname()
        self._lock = threading.Lock()
        self._classes: Dict[str, ClassStats] = {}
        self._signals: Deque[SignalVector] = deque(maxlen=signal_capacity)
        self._last_arrival: Dict[str, float] = {}
        self._t0 = time.time()
        self._server: Optional[ThreadingHTTPServer] = None

    def _cls(self, name: str) -> ClassStats:
        c = self._classes.get(name)
        if c is None:
            c = self._classes[name] = ClassStats()
        return c

    # ---- recording -------------------------------------------------------
    def record(self, cls: str, latency_us: float, nbytes: int = 0,
               queue_depth: Optional[int] = None) -> None:
        with self._lock:
            c = self._cls(cls)
            c.ops += 1
            c.bytes += int(nbytes)
            c.latency.add(float(latency_us))
            if queue_depth is not None:
                c.queue_depth = int(queue_depth)
                c.queue_depth_max = max(c.queue_depth_max, int(queue_depth))

    def record_many(self, cls: str, latencies_us: Iterable[float], nbytes_each: int = 0) -> None:
        with self._lock:
            c = self._cls(cls)
            for v in latencies_us:
                c.ops += 1
                c.bytes += int(nbytes_each)
                c.latency.add(float(v))

    def event(self, cls: str, kind: str, n: int = 1) -> None:
        with self._lock:
            c = self._cls(cls)
            c.events[kind] = c.events.get(kind, 0) + n
            if kind in ("qp_error", "timeout"):
                c.errors += n

    def set_queue_depth(self, cls: str, depth: int) -> None:
        with self._lock:
            c = self._cls(cls)
            c.queue_depth = int(depth)
            c.queue_depth_max = max(c.queue_depth_max, int(depth))

    def observe(self, sig: SignalVector) -> SignalVector:
        """Store a signal vector; fills inter_arrival_us per tensor id if unset."""
        with self._lock:
            key = sig.tensor_id or sig.role
            last = self._last_arrival.get(key)
            if last is not None and math.isnan(sig.inter_arrival_us):
                sig.inter_arrival_us = (sig.timestamp - last) * 1e6
            self._last_arrival[key] = sig.timestamp
            self._signals.append(sig)
            if sig.qp_class and not math.isnan(sig.completion_us):
                c = self._cls(sig.qp_class)
                c.ops += 1
                c.bytes += sig.size_bytes
                c.latency.add(sig.completion_us)
        return sig

    # ---- reading ---------------------------------------------------------
    def signals(self) -> List[SignalVector]:
        with self._lock:
            return list(self._signals)

    def classes(self) -> List[str]:
        with self._lock:
            return sorted(self._classes)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            out: Dict[str, Any] = {
                "node": self.node,
                "uptime_s": time.time() - self._t0,
                "classes": {},
            }
            for name, c in sorted(self._classes.items()):
                out["classes"][name] = {
                    "ops": c.ops,
                    "bytes": c.bytes,
                    "errors": c.errors,
                    "events": dict(c.events),
                    "queue_depth": c.queue_depth,
                    "queue_depth_max": c.queue_depth_max,
                    **c.latency.summary(),
                }
            return out

    def to_json(self, path: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.snapshot(), f, indent=2, default=_json_default)
        return path

    def prometheus_text(self, prefix: str = "scuffed") -> str:
        """Prometheus text exposition format 0.0.4."""
        snap_lines: List[str] = []
        with self._lock:
            items = sorted(self._classes.items())
            node = _esc(self.node)

            def series(metric: str, typ: str, help_: str, rows: List[str]) -> None:
                snap_lines.append(f"# HELP {prefix}_{metric} {help_}")
                snap_lines.append(f"# TYPE {prefix}_{metric} {typ}")
                snap_lines.extend(rows)

            series("ops_total", "counter", "Completed operations per traffic class",
                   [f'{prefix}_ops_total{{node="{node}",class="{_esc(n)}"}} {c.ops}' for n, c in items])
            series("bytes_total", "counter", "Bytes moved per traffic class",
                   [f'{prefix}_bytes_total{{node="{node}",class="{_esc(n)}"}} {c.bytes}' for n, c in items])
            ev_rows = []
            for n, c in items:
                for k in sorted(set(EVENT_KINDS) | set(c.events)):
                    ev_rows.append(f'{prefix}_events_total{{node="{node}",class="{_esc(n)}",kind="{_esc(k)}"}} {c.events.get(k, 0)}')
            series("events_total", "counter",
                   "QP error, reconnect, TCP fallback, timeout and retry events", ev_rows)
            series("queue_depth", "gauge", "Outstanding work requests at last sample",
                   [f'{prefix}_queue_depth{{node="{node}",class="{_esc(n)}"}} {c.queue_depth}' for n, c in items])
            hist_rows = []
            for n, c in items:
                h = c.latency
                cum = 0
                for b, cnt in zip(h.bounds, h.counts):
                    cum += cnt
                    hist_rows.append(f'{prefix}_completion_latency_us_bucket{{node="{node}",class="{_esc(n)}",le="{b:.6g}"}} {cum}')
                cum += h.counts[-1]
                hist_rows.append(f'{prefix}_completion_latency_us_bucket{{node="{node}",class="{_esc(n)}",le="+Inf"}} {cum}')
                hist_rows.append(f'{prefix}_completion_latency_us_sum{{node="{node}",class="{_esc(n)}"}} {h.total:.6f}')
                hist_rows.append(f'{prefix}_completion_latency_us_count{{node="{node}",class="{_esc(n)}"}} {h.n}')
            series("completion_latency_us", "histogram", "Completion latency in microseconds", hist_rows)
        return "\n".join(snap_lines) + "\n"

    # ---- HTTP exporter ---------------------------------------------------
    def serve(self, port: int = 9464, addr: str = "0.0.0.0") -> int:
        """Serve /metrics in a daemon thread. Returns the bound port (0 picks a free one)."""
        tel = self

        class _H(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                if self.path.rstrip("/") not in ("/metrics", ""):
                    self.send_response(404)
                    self.end_headers()
                    return
                body = tel.prometheus_text().encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        self._server = ThreadingHTTPServer((addr, port), _H)
        t = threading.Thread(target=self._server.serve_forever, daemon=True)
        t.start()
        return self._server.server_address[1]

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def reset(self) -> None:
        with self._lock:
            self._classes.clear()
            self._signals.clear()
            self._last_arrival.clear()
            self._t0 = time.time()


def _esc(s: str) -> str:
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _json_default(o: Any) -> Any:
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    if hasattr(o, "__dict__"):
        return asdict(o) if hasattr(o, "__dataclass_fields__") else o.__dict__
    return str(o)


# Process-wide default instance so transports can report without plumbing.
_default: Optional[Telemetry] = None


def default() -> Telemetry:
    global _default
    if _default is None:
        _default = Telemetry()
    return _default
