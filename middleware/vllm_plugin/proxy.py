"""
Disaggregated prefill/decode proxy for ScuffedRdmaConnector (and NixlConnector
as a baseline). Modeled on vLLM's tests/v1/kv_connector/nixl_integration/
toy_proxy_server.py at the pinned commit.

Per request:
  1. POST to prefill with max_tokens=1, stream=false, and
     kv_transfer_params={"do_remote_decode": true, ..., "scuffed_xfer_id": <uuid>}
  2. take kv_transfer_params from the prefill response (ScuffedRdmaConnector
     returns {"do_remote_prefill": true, "scuffed_xfer_id": ..., ...})
  3. POST the original request plus those params to decode, stream the answer back.

Adds response header X-Scuffed-Prefill-Ms (proxy-side prefill round trip) so
TTFT can be split into prefill vs. transfer+decode.

    python -m middleware.vllm_plugin.proxy --prefill http://server1:8100 \
        --decode http://server2:8200 --port 8000 --mode scuffed

Needs fastapi, uvicorn, httpx (installed with vLLM).
"""

# No `from __future__ import annotations`: FastAPI must resolve the Request
# annotation on the route handlers, which are defined inside build_app.
import argparse
import itertools
import os
import time
import uuid
from typing import Any, Dict, List


def prefill_payload(req: Dict[str, Any], xfer_id: str, mode: str) -> Dict[str, Any]:
    p = dict(req)
    params = {"do_remote_decode": True, "do_remote_prefill": False, "remote_engine_id": None,
              "remote_block_ids": None, "remote_host": None, "remote_port": None}
    if mode == "scuffed":
        params["scuffed_xfer_id"] = xfer_id
    p["kv_transfer_params"] = params
    p["stream"] = False
    p["max_tokens"] = 1
    if "max_completion_tokens" in p:
        p["max_completion_tokens"] = 1
    p.pop("stream_options", None)
    return p


def decode_payload(req: Dict[str, Any], prefill_json: Dict[str, Any], xfer_id: str, mode: str) -> Dict[str, Any]:
    d = dict(req)
    kvp = (prefill_json or {}).get("kv_transfer_params") or {}
    if mode == "scuffed" and not kvp.get("scuffed_xfer_id"):
        kvp = {"do_remote_prefill": True, "do_remote_decode": False, "scuffed_xfer_id": xfer_id}
    if kvp:
        d["kv_transfer_params"] = kvp
    return d


def build_app(prefill: List[str], decode: List[str], mode: str = "scuffed", timeout: float = 600.0):
    import httpx
    from fastapi import FastAPI, Request
    from fastapi.responses import StreamingResponse

    app = FastAPI()
    pc = [httpx.AsyncClient(base_url=u.rstrip("/") + "/v1", timeout=timeout) for u in prefill]
    dc = [httpx.AsyncClient(base_url=u.rstrip("/") + "/v1", timeout=timeout) for u in decode]
    p_it, d_it = itertools.cycle(range(len(pc))), itertools.cycle(range(len(dc)))
    key = os.environ.get("OPENAI_API_KEY", "")

    async def handle(api: str, request: Request):
        req = await request.json()
        rid = str(uuid.uuid4())
        headers = {"X-Request-Id": rid}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        t0 = time.perf_counter()
        r = await pc[next(p_it)].post(api, json=prefill_payload(req, rid, mode), headers=headers)
        r.raise_for_status()
        pj = r.json()
        prefill_ms = (time.perf_counter() - t0) * 1e3
        body = decode_payload(req, pj, rid, mode)
        client = dc[next(d_it)]

        async def gen():
            async with client.stream("POST", api, json=body, headers=headers) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    yield chunk

        return StreamingResponse(gen(), media_type="application/json",
                                 headers={"X-Scuffed-Prefill-Ms": f"{prefill_ms:.3f}",
                                          "X-Scuffed-Xfer-Id": rid})

    @app.post("/v1/completions")
    async def completions(request: Request):
        return await handle("/completions", request)

    @app.post("/v1/chat/completions")
    async def chat(request: Request):
        return await handle("/chat/completions", request)

    @app.get("/healthcheck")
    async def health():
        return {"status": "ok", "mode": mode, "prefill": prefill, "decode": decode}

    return app


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prefill", nargs="+", required=True, help="prefill server base URL(s)")
    ap.add_argument("--decode", nargs="+", required=True, help="decode server base URL(s)")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--mode", choices=["scuffed", "nixl"], default="scuffed")
    a = ap.parse_args()
    import uvicorn
    uvicorn.run(build_app(a.prefill, a.decode, a.mode), host=a.host, port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
