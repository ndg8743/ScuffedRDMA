"""Check for the stall of FabricBlobChannel blobs larger than one slot (multi-chunk) on the libfabric tcp
provider in loopback. First seen 2026-10-26 while executing notebook 03 (8 MiB blobs, nslots=4, slot_mb=4:
receiver never completed; on repeat, 5 MiB/4 slots and 8 MiB/8 slots failed while 8 MiB/4 slots passed).

Cause, found 2026-11-26: send() posted its chunks and returned, and this script's sender then makes no
further call. The tcp provider of libfabric 1.17 has no progress thread (tcpx_tx_queue_insert): a write
goes out during the call that posts it as far as the socket accepts it, and the rest, like every write
posted behind an unfinished one, waits for the next call that reads a completion queue. With the receiver
draining, the first chunk usually went out in full and a later one did not, so blobs of one chunk passed.
send() now waits until its writes have completed locally, and this script passes. It fails on a tree from
before that change.

    python3 benchmarks/fabric/blob_multichunk_check.py [--provider tcp] [--repeat 3]
    python3 benchmarks/fabric/blob_multichunk_check.py --provider verbs --addr <IP of the RDMA interface>
"""
import argparse, os, sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from middleware.fabric.pool import FabricBlobChannel


def pair(port, provider, nslots, slot_mb, addr="127.0.0.1", ep_type="msg"):
    box = {}
    th = threading.Thread(target=lambda: box.setdefault("s", FabricBlobChannel.listen(
        port, addr, provider=provider, ep_type=ep_type, nslots=nslots, slot_mb=slot_mb)))
    th.start(); time.sleep(0.3)
    c = FabricBlobChannel.connect(addr, port, provider=provider, ep_type=ep_type, nslots=nslots, slot_mb=slot_mb)
    th.join()
    return c, box["s"]


def one(provider, nslots, slot_mb, size, timeout, port, addr="127.0.0.1", ep_type="msg"):
    a, b = pair(port, provider, nslots, slot_mb, addr, ep_type)
    try:
        payload = os.urandom(size); out = {}
        def rx():
            try: out["r"] = b.recv(timeout=timeout)
            except Exception as e: out["e"] = repr(e)
        t = threading.Thread(target=rx, daemon=True); t.start()
        t0 = time.perf_counter()
        try: a.send("k", payload, timeout=timeout)
        except Exception as e: out["se"] = repr(e)
        t.join(timeout + 5)
        ok = "r" in out and out["r"][1] == payload
        return ok, time.perf_counter() - t0, {k: v for k, v in out.items() if k != "r"}
    finally:
        a.close(); b.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="tcp"); ap.add_argument("--repeat", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=15.0); ap.add_argument("--slot-mb", type=int, default=4)
    ap.add_argument("--addr", default="127.0.0.1", help="address both sides use; for verbs the IP of the RDMA interface")
    ap.add_argument("--ep-type", default="msg", choices=["msg", "rdm"])
    args = ap.parse_args()
    cases = [(4, 1 << 20), (4, 5 << 20), (4, 8 << 20), (8, 8 << 20), (8, 16 << 20)]
    port = 32100 + os.getpid() % 300
    fails = 0
    for r in range(args.repeat):
        for nslots, size in cases:
            port += 1
            ok, dt, info = one(args.provider, nslots, args.slot_mb, size, args.timeout, port, args.addr, args.ep_type)
            chunks = -(-size // (args.slot_mb * (1 << 20) - 64 - 1))
            print(f"rep {r} provider={args.provider} nslots={nslots} size={size >> 20:>2} MiB chunks={chunks} -> {'ok' if ok else 'FAIL'} {dt:6.2f}s {info if not ok else ''}")
            fails += not ok
    print("failures:", fails)
    sys.exit(1 if fails else 0)
