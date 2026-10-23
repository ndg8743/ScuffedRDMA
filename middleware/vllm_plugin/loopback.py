"""
Connector transport check without vLLM: push a synthetic paged KV cache from
a producer WorkerSide to a consumer WorkerSide and verify it byte for byte.

Same code path as ScuffedRdmaConnector.save_kv_layer / start_load_kv
(take_blocks -> encode_kv -> KVSender -> BlobChannel -> KVReceiver ->
decode_kv -> put_blocks), with a model-shaped cache.

Single machine (two processes):
    python -m middleware.vllm_plugin.loopback --role both --transport tcp

Across nodes (start the consumer first):
    chimera$  python -m middleware.vllm_plugin.loopback --role consumer --port 14600 --transport fabric --provider verbs
    cerberus$ python -m middleware.vllm_plugin.loopback --role producer --peer chimera --port 14600 --transport fabric --provider verbs

A 16-token warmup request goes first (connection setup) and is not reported;
load_ms on the consumer is the wait for each request's layers to arrive, so
it also covers the producer's encode time.

Default shape is Granite 3.3-2B (40 layers, 8 KV heads, head_dim 64),
FlashAttention layout [2, num_blocks, 16, 8, 64]. Prints one JSON line.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import socket
import time
from typing import Any, Dict, List, Optional

import numpy as np

from middleware.telemetry import Telemetry

from .core import ConnectorConfig, CoreMetadata, ReqMeta, WorkerSide

GRANITE_33_2B = {"layers": 40, "kv_heads": 8, "head_dim": 64}


def _make_cache(n_layers: int, num_blocks: int, block_size: int, kv_heads: int, head_dim: int,
                dtype: str, fill: bool, seed: int = 0) -> Dict[str, Any]:
    shape = (2, num_blocks, block_size, kv_heads, head_dim)
    names = [f"model.layers.{i}.self_attn.attn" for i in range(n_layers)]
    try:
        import torch
        g = torch.Generator().manual_seed(seed)
        tdt = getattr(torch, dtype)
        if fill:
            return {n: torch.randn(shape, generator=g).to(tdt) for n in names}
        return {n: torch.zeros(shape, dtype=tdt) for n in names}
    except ImportError:
        npdt = np.float16 if dtype in ("bfloat16", "float16") else np.float32
        rng = np.random.default_rng(seed)
        if fill:
            return {n: rng.standard_normal(shape).astype(npdt) for n in names}
        return {n: np.zeros(shape, npdt) for n in names}


def _digest(cache: Dict[str, Any], block_ids: List[int]) -> str:
    h = hashlib.sha256()
    for n in cache:
        t = cache[n]
        sub = t[:, block_ids]
        if type(sub).__module__.startswith("torch"):
            import torch
            sub = sub.contiguous().view(torch.uint8).numpy()
        h.update(np.ascontiguousarray(sub).tobytes())
    return h.hexdigest()


WARMUP = "lb-warmup"


def _plan(prompt_lens: List[int], block_size: int, num_blocks: int, seed: int = 1):
    """First entry is a warmup request (connection setup, first-touch); it is not reported."""
    rng = np.random.default_rng(seed)
    out = []
    nb = -(-16 // block_size)
    out.append((WARMUP, 16, rng.choice(num_blocks, nb, replace=False).tolist(),
                rng.choice(num_blocks, nb, replace=False).tolist()))
    for i, n in enumerate(prompt_lens):
        nb = -(-n // block_size)
        src = rng.choice(num_blocks, size=nb, replace=False).tolist()
        dst = rng.choice(num_blocks, size=nb, replace=False).tolist()
        out.append((f"lb-{i}-{n}", n, src, dst))
    return out


def consumer(port: int, args: Dict[str, Any], result_q: Optional[Any] = None) -> Dict[str, Any]:
    tel = Telemetry(node=socket.gethostname())
    cfg = ConnectorConfig(is_producer=False, is_consumer=True, block_size=args["block_size"], port=port,
                          bind=args.get("bind", "0.0.0.0"), transport=args["transport"],
                          provider=args.get("provider"), ep_type=args.get("ep_type"),
                          load_timeout_s=args.get("timeout", 120.0))
    w = WorkerSide(cfg, tel=tel)
    cache = _make_cache(args["layers"], args["num_blocks"], args["block_size"], args["kv_heads"],
                        args["head_dim"], args["dtype"], fill=False)
    w.register_kv_caches(cache)
    per = []
    for xid, n, _src, dst in _plan(args["prompt_lens"], args["block_size"], args["num_blocks"]):
        t0 = time.perf_counter()
        written = w.start_load_kv(CoreMetadata([ReqMeta("d-" + xid, xid, dst, n, load=True)]))
        if xid == WARMUP:
            continue
        per.append({"xfer_id": xid, "prompt_len": n, "blocks_written": written,
                    "load_ms": (time.perf_counter() - t0) * 1e3, "digest": _digest(cache, dst)})
    out = {"role": "consumer", "transport": w._receiver.transport_used, "requests": per,
           "load_errors": sorted(w.get_block_ids_with_load_errors()), "telemetry": tel.snapshot()}
    w.shutdown()
    if result_q is not None:
        result_q.put(out)
    return out


def producer(peer: str, port: int, args: Dict[str, Any]) -> Dict[str, Any]:
    tel = Telemetry(node=socket.gethostname())
    cfg = ConnectorConfig(is_producer=True, is_consumer=False, block_size=args["block_size"], peer=peer,
                          port=port, transport=args["transport"], provider=args.get("provider"),
                          ep_type=args.get("ep_type"), compress=args.get("compress"))
    w = WorkerSide(cfg, tel=tel)
    cache = _make_cache(args["layers"], args["num_blocks"], args["block_size"], args["kv_heads"],
                        args["head_dim"], args["dtype"], fill=True)
    w.register_kv_caches(cache)
    per = []
    for xid, n, src, _dst in _plan(args["prompt_lens"], args["block_size"], args["num_blocks"]):
        meta = CoreMetadata([ReqMeta("p-" + xid, xid, src, n, load=False)])
        t0 = time.perf_counter()
        for name, layer in cache.items():
            w.save_kv_layer(name, layer, meta)
        w.wait_for_save()
        ok = w._sender.flush(timeout=args.get("timeout", 120.0))
        if xid == WARMUP:
            tel.reset()
            continue
        per.append({"xfer_id": xid, "prompt_len": n, "push_ms": (time.perf_counter() - t0) * 1e3,
                    "flushed": ok, "digest": _digest(cache, src)})
    snap = tel.snapshot()
    out = {"role": "producer", "transport": w._sender.transport_used, "requests": per, "telemetry": snap,
           "wire_bytes": sum(c.get("bytes", 0) for k, c in snap["classes"].items() if k in ("hot", "cold"))}
    w.shutdown()
    return out


def run_both(args: Dict[str, Any], port: Optional[int] = None) -> Dict[str, Any]:
    """Consumer in a child process, producer here, on 127.0.0.1."""
    if port is None:
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=consumer, args=(port, dict(args, bind="127.0.0.1"), q), daemon=True)
    p.start()
    prod = producer("127.0.0.1", port, args)
    cons = q.get(timeout=args.get("timeout", 120.0) + 60)
    p.join(timeout=30)
    match = [a["digest"] == b["digest"] for a, b in zip(prod["requests"], cons["requests"])]
    return {"port": port, "producer": prod, "consumer": cons, "all_match": all(match), "match": match}


def default_args(**over) -> Dict[str, Any]:
    a = dict(layers=GRANITE_33_2B["layers"], kv_heads=GRANITE_33_2B["kv_heads"],
             head_dim=GRANITE_33_2B["head_dim"], block_size=16, num_blocks=512, dtype="bfloat16",
             prompt_lens=[128, 512, 2048], transport="tcp", provider=None, ep_type=None,
             compress=None, timeout=120.0)
    a.update(over)
    return a


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--role", choices=["both", "producer", "consumer"], default="both")
    ap.add_argument("--peer", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=14600)
    ap.add_argument("--transport", choices=["tcp", "fabric"], default="tcp")
    ap.add_argument("--provider", default=None)
    ap.add_argument("--ep-type", default=None)
    ap.add_argument("--compress", choices=["scuffedquant"], default=None)
    ap.add_argument("--layers", type=int, default=GRANITE_33_2B["layers"])
    ap.add_argument("--kv-heads", type=int, default=GRANITE_33_2B["kv_heads"])
    ap.add_argument("--head-dim", type=int, default=GRANITE_33_2B["head_dim"])
    ap.add_argument("--num-blocks", type=int, default=512)
    ap.add_argument("--block-size", type=int, default=16)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--prompt-lens", default="128,512,2048")
    ap.add_argument("--timeout", type=float, default=120.0)
    a = ap.parse_args(argv)
    args = default_args(layers=a.layers, kv_heads=a.kv_heads, head_dim=a.head_dim, block_size=a.block_size,
                        num_blocks=a.num_blocks, dtype=a.dtype,
                        prompt_lens=[int(x) for x in a.prompt_lens.split(",")],
                        transport=a.transport, provider=a.provider, ep_type=a.ep_type,
                        compress=a.compress, timeout=a.timeout)
    if a.role == "both":
        out = run_both(args)
    elif a.role == "consumer":
        out = consumer(a.port, args)
    else:
        out = producer(a.peer, a.port, args)
    print(json.dumps(out, default=str))


if __name__ == "__main__":
    main()
