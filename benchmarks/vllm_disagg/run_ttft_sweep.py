#!/usr/bin/env python3
"""
TTFT / ITL sweep against a vLLM OpenAI-compatible endpoint (a single server,
or the disagg proxy in middleware/vllm_plugin/proxy.py).

Prompts are random token-id lists (POST /v1/completions accepts list[int]),
so prompt length is exact. Each request streams; TTFT is request start to
the first SSE chunk carrying text, ITL is the gap between later chunks.

    python benchmarks/vllm_disagg/run_ttft_sweep.py --url http://localhost:8000 \
        --model ibm-granite/granite-3.3-2b-instruct --label scuffed-fabric-verbs \
        --prompt-lens 128,512,1024,2048,4096 --n 20 --max-tokens 64 \
        --out benchmarks/results/vllm_disagg/

    python benchmarks/vllm_disagg/run_ttft_sweep.py --selftest   # mock server, no vLLM

Stdlib only. Output JSON is tagged with hostname and UTC time.
"""

from __future__ import annotations

import argparse
import json
import random
import socket
import statistics
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional


def pct(xs: List[float], p: float) -> Optional[float]:
    if not xs:
        return None
    s = sorted(xs)
    k = (len(s) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def one_request(url: str, model: str, prompt: List[int], max_tokens: int, timeout: float) -> Dict[str, Any]:
    body = json.dumps({"model": model, "prompt": prompt, "max_tokens": max_tokens, "stream": True,
                       "temperature": 0.0, "ignore_eos": True}).encode()
    req = urllib.request.Request(url.rstrip("/") + "/v1/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    ttft = None
    stamps: List[float] = []
    prefill_ms = None
    err = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            h = resp.headers.get("X-Scuffed-Prefill-Ms")
            prefill_ms = float(h) if h else None
            for raw in resp:
                line = raw.decode(errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    j = json.loads(data)
                except json.JSONDecodeError:
                    continue
                ch = (j.get("choices") or [{}])[0]
                if ch.get("text"):
                    now = time.perf_counter()
                    if ttft is None:
                        ttft = (now - t0) * 1e3
                    stamps.append(now)
    except Exception as e:  # noqa: BLE001
        err = repr(e)
    e2e = (time.perf_counter() - t0) * 1e3
    itl = [(b - a) * 1e3 for a, b in zip(stamps, stamps[1:])]
    return {"prompt_len": len(prompt), "ttft_ms": ttft, "itl_ms": itl, "e2e_ms": e2e,
            "chunks": len(stamps), "proxy_prefill_ms": prefill_ms, "error": err}


def sweep(url: str, model: str, prompt_lens: List[int], n: int, max_tokens: int, concurrency: int = 1,
          warmup: int = 2, vocab: tuple = (1000, 30000), seed: int = 0, timeout: float = 600.0) -> Dict[str, Any]:
    rng = random.Random(seed)
    mk = lambda L: [rng.randrange(*vocab) for _ in range(L)]  # noqa: E731
    for _ in range(warmup):
        one_request(url, model, mk(min(prompt_lens)), 4, timeout)
    per_len = []
    for L in prompt_lens:
        prompts = [mk(L) for _ in range(n)]
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            rs = list(ex.map(lambda p: one_request(url, model, p, max_tokens, timeout), prompts))
        ok = [r for r in rs if r["error"] is None and r["ttft_ms"] is not None]
        ttft = [r["ttft_ms"] for r in ok]
        itl = [x for r in ok for x in r["itl_ms"]]
        pre = [r["proxy_prefill_ms"] for r in ok if r["proxy_prefill_ms"] is not None]
        per_len.append({
            "prompt_len": L, "n": n, "ok": len(ok), "errors": [r["error"] for r in rs if r["error"]][:5],
            "ttft_p50_ms": pct(ttft, 50), "ttft_p90_ms": pct(ttft, 90), "ttft_p99_ms": pct(ttft, 99),
            "ttft_mean_ms": statistics.fmean(ttft) if ttft else None,
            "itl_p50_ms": pct(itl, 50), "itl_p99_ms": pct(itl, 99),
            "proxy_prefill_p50_ms": pct(pre, 50),
            "raw": rs,
        })
        print(f"len={L:6d} ok={len(ok)}/{n} ttft p50={per_len[-1]['ttft_p50_ms']} p99={per_len[-1]['ttft_p99_ms']} "
              f"itl p50={per_len[-1]['itl_p50_ms']}", file=sys.stderr)
    return {"url": url, "model": model, "max_tokens": max_tokens, "concurrency": concurrency,
            "prompt_lens": prompt_lens, "results": per_len}


# ---------------------------------------------------------------- selftest --

def _mock_server(first_ms: float, gap_ms: float, tokens: int):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            n = int(self.headers.get("Content-Length", 0))
            json.loads(self.rfile.read(n))
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("X-Scuffed-Prefill-Ms", "1.0")
            self.end_headers()
            time.sleep(first_ms / 1e3)
            for i in range(tokens):
                if i:
                    time.sleep(gap_ms / 1e3)
                self.wfile.write(f"data: {json.dumps({'choices': [{'text': 'x'}]})}\n\n".encode())
                self.wfile.flush()
            self.wfile.write(b"data: [DONE]\n\n")

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def selftest(out: Optional[str] = None) -> Dict[str, Any]:
    """Measure a mock server with known delays; checks the measurement path, not vLLM."""
    first, gap = 40.0, 5.0
    srv = _mock_server(first, gap, tokens=8)
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    res = sweep(url, "mock", [16, 64], n=5, max_tokens=8, warmup=1)
    srv.shutdown()
    for r in res["results"]:
        assert r["ok"] == r["n"], r["errors"]
        assert first * 0.9 <= r["ttft_p50_ms"] <= first + 60, r["ttft_p50_ms"]
        assert gap * 0.8 <= r["itl_p50_ms"] <= gap + 30, r["itl_p50_ms"]
        assert r["proxy_prefill_p50_ms"] == 1.0
    res["label"] = "selftest-mock"
    res["mock"] = {"first_ms": first, "gap_ms": gap}
    if out:
        _write(res, out, "selftest-mock")
    print("selftest ok", file=sys.stderr)
    return res


def _write(res: Dict[str, Any], out: str, label: str) -> Path:
    host = socket.gethostname()
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    res = {"host": host, "utc": stamp, "label": label, **res}
    p = Path(out)
    if p.suffix != ".json":
        p.mkdir(parents=True, exist_ok=True)
        p = p / f"{host}_ttft_{label}_{stamp}.json"
    p.write_text(json.dumps(res, indent=2))
    print(f"wrote {p}", file=sys.stderr)
    return p


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--model", default="ibm-granite/granite-3.3-2b-instruct")
    ap.add_argument("--label", default="run")
    ap.add_argument("--prompt-lens", default="128,512,1024,2048,4096")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--out", default=None, help="directory or .json path")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest(a.out)
        return
    res = sweep(a.url, a.model, [int(x) for x in a.prompt_lens.split(",")], a.n, a.max_tokens,
                a.concurrency, a.warmup)
    res["label"] = a.label
    if a.out:
        _write(res, a.out, a.label)
    else:
        print(json.dumps(res))


if __name__ == "__main__":
    main()
