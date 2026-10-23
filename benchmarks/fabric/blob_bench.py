#!/usr/bin/env python3
"""
Cross-node blob throughput: FabricBlobChannel (libfabric dual endpoint) vs
TcpBlobChannel, KV-sized blobs, as the vLLM connector uses them.

    server (e.g. server 2):  python3 benchmarks/fabric/blob_bench.py --role server --transport fabric --provider verbs --port 31700
    client (e.g. server 1): python3 benchmarks/fabric/blob_bench.py --role client --host <server ip> --transport fabric --provider verbs --port 31700 --out r.json

The server echoes one 8-byte ack per blob so the client measures end-to-end
delivery, not just local posting.
"""
import argparse
import json
import os
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from middleware.fabric.channel import TcpBlobChannel  # noqa: E402


def open_channel(a):
    if a.transport == "tcp":
        return TcpBlobChannel.listen(a.port) if a.role == "server" else TcpBlobChannel.connect(a.host, a.port)
    from middleware.fabric.pool import FabricBlobChannel
    kw = dict(provider=a.provider, ep_type=a.ep_type, nslots=a.nslots, slot_mb=a.slot_mb)
    if a.domain:
        kw["domain"] = a.domain
    if a.role == "server":
        return FabricBlobChannel.listen(a.port, a.bind, **kw)
    return FabricBlobChannel.connect(a.host, a.port, **kw)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--role", choices=["server", "client"], required=True)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--bind", default="0.0.0.0")
    p.add_argument("--port", type=int, default=31700)
    p.add_argument("--transport", choices=["tcp", "fabric"], default="fabric")
    p.add_argument("--provider", default="verbs")
    p.add_argument("--ep-type", default="msg")
    p.add_argument("--domain", default=None)
    p.add_argument("--nslots", type=int, default=8)
    p.add_argument("--slot-mb", type=int, default=4)
    p.add_argument("--sizes", default="4096,65536,1048576,8388608,33554432")
    p.add_argument("--reps", type=int, default=50)
    p.add_argument("--out", default=None)
    a = p.parse_args()
    sizes = [int(x) for x in a.sizes.split(",")]
    ch = open_channel(a)
    res = []
    try:
        for sz in sizes:
            if a.role == "server":
                for _ in range(a.reps):
                    k, v = ch.recv(timeout=300)
                    ch.send("ack/" + k, len(v).to_bytes(8, "little"), hot=True)
                continue
            payload = os.urandom(sz)
            lat = []
            t0 = time.perf_counter()
            for i in range(a.reps):
                t1 = time.perf_counter()
                ch.send(f"b{sz}/{i}", payload, hot=sz <= 4096)
                k, v = ch.recv(timeout=300)
                assert int.from_bytes(v, "little") == sz, (k, v)
                lat.append((time.perf_counter() - t1) * 1e6)
            dt = time.perf_counter() - t0
            lat.sort()
            res.append({"blob_bytes": sz, "reps": a.reps, "MBps": sz * a.reps / dt / 1e6,
                        "p50_us": lat[len(lat) // 2], "p99_us": lat[min(len(lat) - 1, int(len(lat) * 0.99))]})
            print(json.dumps(res[-1]), flush=True)
    finally:
        ch.close()
    if a.role == "client":
        out = {"tool": "blob_bench", "host": socket.gethostname(), "transport": a.transport, "provider": a.provider,
               "ep_type": a.ep_type, "results": res, "args": vars(a)}
        if a.out:
            Path(a.out).write_text(json.dumps(out, indent=2))
        else:
            print(json.dumps(out))


if __name__ == "__main__":
    main()
