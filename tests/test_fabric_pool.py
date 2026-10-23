"""
libscuffedfabric end to end on the providers available without RDMA
hardware (tcp MSG, tcp;ofi_rxm RDM, shm RDM), plus the native verbs build.
Verbs-provider and libibverbs runs are marked rdma and run on the cluster.
"""
import itertools
import json
import os
import shutil
import subprocess
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FAB = ROOT / "middleware" / "libscuffedfabric"
VRB = ROOT / "middleware" / "libscuffedverbs"

pytestmark = pytest.mark.skipif(shutil.which("fi_info") is None and not Path("/usr/include/rdma/fabric.h").exists(),
                                reason="libfabric not installed")

_port = itertools.count(23000 + (os.getpid() % 500) * 20)


def port():
    return next(_port)


@pytest.fixture(scope="module", autouse=True)
def built():
    from middleware.fabric import pool
    pool.build("fabric")
    yield


def _pair(make_server, make_client):
    box = {}

    def srv():
        try:
            box["s"] = make_server()
        except Exception as e:  # surfaced below
            box["err"] = e

    t = threading.Thread(target=srv)
    t.start()
    c = make_client()
    t.join(30)
    if "err" in box:
        raise box["err"]
    return box["s"], c


CONFIGS = [
    dict(provider="tcp", ep_type="msg"),
    dict(provider="tcp;ofi_rxm", ep_type="rdm"),
    dict(provider="shm", ep_type="rdm"),
    dict(provider="tcp", ep_type="msg", single_ep=True),
    dict(hot_provider="tcp;ofi_rxm", hot_ep="rdm", cold_provider="tcp", cold_ep="msg", provider=None),
    dict(provider="tcp", ep_type="msg", hot_cntr=True, cold_wait=True),
]


def _ids(cfg):
    return ",".join(f"{k}={v}" for k, v in cfg.items())


@pytest.mark.parametrize("cfg", CONFIGS, ids=_ids)
def test_pool_writedata_roundtrip(cfg):
    from middleware.fabric.pool import COLD, HOT, RX_DATA, FabricPool

    p = port()
    s, c = _pair(lambda: FabricPool(arena_mb=8, **cfg).listen(p, "127.0.0.1", 20000),
                 lambda: FabricPool(arena_mb=8, **cfg).connect("127.0.0.1", p, 20000))
    seen, stop = [], threading.Event()

    def target_progress():
        # the target drives its own progress, as a server would (rxm/shm need it)
        while not stop.is_set():
            for cls in (HOT, COLD):
                s.progress(cls)
                seen.extend((cls, e.kind, e.data) for e in s.poll_rx(cls))

    t = threading.Thread(target=target_progress, daemon=True)
    t.start()
    try:
        for cls in (HOT, COLD):
            c.buf[0:5] = b"hello"
            c.write(cls, 0, 5, 4096 * (cls + 1), imm=0xABC + cls)
            c.wait_tx(cls, timeout_ms=20000)
            # with one shared endpoint the target cannot tell classes apart: accept either
            want = {(k, RX_DATA, 0xABC + cls) for k in ((HOT, COLD) if cfg.get("single_ep") else (cls,))}
            for _ in range(2000):
                if want & set(seen):
                    break
                threading.Event().wait(0.005)
            assert want & set(seen), f"no remote CQ data on class {cls}"
            assert bytes(s.buf[4096 * (cls + 1): 4096 * (cls + 1) + 5]) == b"hello"
        assert "prov=" in s.describe(HOT) and "prov=" in c.describe(COLD)
    finally:
        stop.set()
        t.join(5)
        s.close()
        c.close()


@pytest.mark.parametrize("cfg", CONFIGS[:4], ids=_ids)
def test_blob_channel_sizes_and_classes(cfg):
    from middleware.fabric.pool import FabricBlobChannel, FabricPool

    p = port()
    mk = lambda: FabricPool(arena_mb=2 * 4 * 1 + 1, **cfg)  # noqa: E731
    s, c = _pair(lambda: FabricBlobChannel(mk().listen(p, "127.0.0.1", 20000), nslots=4, slot_bytes=1 << 20),
                 lambda: FabricBlobChannel(mk().connect("127.0.0.1", p, 20000), nslots=4, slot_bytes=1 << 20))
    blobs = [("meta/0", os.urandom(0), True), ("meta/1", os.urandom(17), True),
             ("req1/L0", os.urandom(4095), False), ("req1/L1", os.urandom((1 << 20) + 123), False),
             ("req2/L0", os.urandom(5 * (1 << 20) + 7), False), ("tok/9", os.urandom(64), True)]
    got = {}

    def rx():
        for _ in blobs:
            k, v = s.recv(timeout=60)
            got[k] = v

    t = threading.Thread(target=rx)
    t.start()
    for k, v, hot in blobs:
        c.send(k, v, hot=hot)
    t.join(90)
    try:
        assert set(got) == {k for k, _, _ in blobs}
        for k, v, _ in blobs:
            assert got[k] == v, k
        # reverse direction on the same channel
        s.send("back", b"xyz" * 1000, hot=False)
        assert c.recv(timeout=30) == ("back", b"xyz" * 1000)
    finally:
        s.close()
        c.close()


def test_blob_channel_reports_telemetry():
    from middleware.fabric.pool import FabricBlobChannel, FabricPool
    from middleware.telemetry import Telemetry

    tel = Telemetry(node="t")
    p = port()
    s, c = _pair(lambda: FabricBlobChannel(FabricPool("tcp", "msg", arena_mb=9, telemetry=tel).listen(p, "127.0.0.1"), nslots=4, slot_bytes=1 << 20),
                 lambda: FabricBlobChannel(FabricPool("tcp", "msg", arena_mb=9, telemetry=tel).connect("127.0.0.1", p), nslots=4, slot_bytes=1 << 20))
    try:
        c.send("a", b"x" * 100, hot=True)
        c.send("b", b"y" * 300000, hot=False)
        assert s.recv(10)[0] == "a" and s.recv(10)[0] == "b"
        snap = tel.snapshot()["classes"]
        assert snap["hot"]["ops"] == 1 and snap["cold"]["bytes"] == 300000
    finally:
        s.close()
        c.close()


def _bench(binary, mode, extra, timeout=120):
    p = port()
    args = ["-H", "127.0.0.1", "-P", str(p), "-m", mode] + extra
    srv = subprocess.Popen([str(binary), "-r", "server", *args, "-j", "/dev/null"], stderr=subprocess.PIPE, text=True)
    try:
        cli = subprocess.run([str(binary), "-r", "client", *args], capture_output=True, text=True, timeout=timeout)
        srv.wait(timeout=timeout)
    finally:
        if srv.poll() is None:
            srv.kill()
    assert cli.returncode == 0, cli.stderr + srv.stderr.read()
    return json.loads(cli.stdout)


@pytest.mark.parametrize("mech", ["cq", "flag", "sentinel", "read", "cntr"])
def test_sf_bench_sig_tcp(mech):
    d = _bench(FAB / "sf_bench", "sig", ["-M", mech, "-p", "tcp", "-t", "msg", "-n", "200", "-w", "10", "-S", "64,4096"])
    assert d["tool"] == "sf_bench" and d["mech"] == mech
    if "skipped" in d:
        assert mech in ("cntr", "sentinel")
        return
    assert [r["size"] for r in d["results"]] == [64, 4096]
    assert all(r["n"] == 200 and r["p50_us"] > 0 for r in d["results"])


def test_sf_bench_sig_shm_counter():
    d = _bench(FAB / "sf_bench", "sig", ["-M", "cntr", "-p", "shm", "-t", "rdm", "-n", "200", "-w", "10", "-S", "64"])
    assert "results" in d and d["results"][0]["n"] == 200


def test_sf_bench_bw_and_hol_single_vs_dual():
    bw = _bench(FAB / "sf_bench", "bw", ["-p", "tcp", "-t", "msg", "-n", "50", "-S", "256K", "-W", "8"])
    assert bw["results"][0]["MBps"] > 0
    for single in ([], ["-s"]):
        h = _bench(FAB / "sf_bench", "hol", ["-p", "shm", "-t", "rdm", "-n", "500", "-w", "20",
                                            "--cold-size", "262144", "-W", "4", *single])
        assert h["hot_rtt"]["n"] == 500
        assert h["cold"]["on"] == 1 and h["cold"]["ops"] > 0
        assert h["single_ep"] == (1 if single else 0)


def test_verbs_build_and_clean_error_without_device():
    r = subprocess.run(["make", "-C", str(VRB)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (VRB / "sv_bench").exists() and (VRB / "libscuffedverbs.so").exists()
    if os.path.isdir("/sys/class/infiniband") and os.listdir("/sys/class/infiniband"):
        pytest.skip("RDMA device present; covered by the rdma-marked test")
    out = subprocess.run([str(VRB / "sv_bench"), "-r", "server", "-H", "127.0.0.1", "-P", str(port()), "-m", "sig",
                          "--timeout-ms", "1000"], capture_output=True, text=True, timeout=30)
    assert out.returncode != 0 and "no RDMA devices" in out.stderr


@pytest.mark.rdma
@pytest.mark.parametrize("binary,extra", [
    (VRB / "sv_bench", []),
    (FAB / "sf_bench", ["-p", "verbs", "-t", "msg"]),
    (FAB / "sf_bench", ["-p", "verbs;ofi_rxm", "-t", "rdm"]),
])
def test_rdma_loopback_sig_and_hol(binary, extra):
    d = _bench(binary, "sig", ["-M", "cq", "-n", "500", "-w", "50", "-S", "64,4096", *extra])
    assert all(r["n"] == 500 for r in d["results"])
    h = _bench(binary, "hol", ["-n", "1000", "-w", "50", "--cold-size", "1048576", "-W", "8", *extra])
    assert h["hot_rtt"]["n"] == 1000 and h["cold"]["ops"] > 0


def test_nccl_plugin_builds_and_exports_v8():
    d = ROOT / "middleware" / "nccl_plugin"
    r = subprocess.run(["make", "-C", str(d)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    nm = subprocess.run(["nm", "-D", str(d / "libscuffed_nccl_net.so")], capture_output=True, text=True).stdout
    assert "ncclNetPlugin_v8" in nm
