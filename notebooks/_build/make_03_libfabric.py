from nbtools import build
from _fabric_params import PARAMS, COMMON

cells = [
("md", """Update 7, next step 4, and the core of Update 8: the dual QP pool built on libfabric, compared against the
native libibverbs pool on identical payloads.

* **Same benchmark code.** `sv_bench` is `sf_bench.c` linked against `libscuffedverbs` (the same API implemented
  on raw ibverbs RC QPs), so any difference is the library, not the harness.
* **Endpoint types.** libfabric lets each class pick its endpoint: `FI_EP_MSG` maps onto an RC QP on the verbs
  provider; `FI_EP_RDM` goes through `ofi_rxm` (connection management, eager/rendezvous protocol switching,
  its own progress engine). The hot-RDM + cold-MSG split is the combination Update 7 proposed.
* **Completion objects.** Hot TX completions through `fi_cntr` with selective completion vs a CQ; cold TX CQ
  with a wait object (`fi_cq_sread`) vs busy polling.
* **Application level.** `FabricBlobChannel` (the transport the vLLM connector uses) vs `TcpBlobChannel` for
  KV-sized blobs."""),
("code", COMMON),
("md", "## 1. Hot-path latency: libibverbs vs libfabric verbs MSG vs verbs;ofi_rxm RDM"),
("code", '''SIZES = "8,64,256,1024,4096,16384,65536" if CLUSTER else "64,4096,65536"
raw, lat = [], []
for st in STACKS:
    d = runner.try_pair(st["tool"], st["args"] + ["-m", "sig", "-M", "cq", "-n", str(N), "-w", str(W), "-S", SIZES, "--perf"], env=ENV, **PAIR)
    raw.append(d); lat += runner.rows_sig(d, st["label"])
lat = pd.DataFrame(lat); lat'''),
("md", "## 2. Cold-path bandwidth"),
("code", '''BW_SIZES = "4K,64K,256K,1M,4M,16M" if CLUSTER else "64K,1M"
bw = []
for st in STACKS:
    for wait in (False, True):
        a = st["args"] + ["-m", "bw", "-n", str(max(200, N // 20)), "-S", BW_SIZES, "-W", "16"] + (["--cold-wait"] if wait else [])
        d = runner.try_pair(st["tool"], a, env=ENV, **PAIR); raw.append(d)
        for r in d.get("results", []):
            bw.append({"label": st["label"], "cold_wait": wait, **r})
        if "error" in d: bw.append({"label": st["label"], "cold_wait": wait, "error": d["error"][:200]})
bw = pd.DataFrame(bw); bw'''),
("md", "## 3. libfabric configuration matrix (endpoint types, counters, wait objects) under mixed traffic"),
("code", '''prov = "verbs" if CLUSTER else "tcp"
rdm_prov = "verbs;ofi_rxm" if CLUSTER else "tcp;ofi_rxm"
dom = ["-d", DOMAIN] if CLUSTER else []
MATRIX = {
    "MSG/MSG (RC/RC)": ["-p", prov, "-t", "msg"],
    "RDM/RDM": ["-p", rdm_prov, "-t", "rdm"],
    "hot RDM + cold MSG": ["--hot-prov", rdm_prov, "--hot-ep", "rdm", "--cold-prov", prov, "--cold-ep", "msg"],
    "MSG/MSG, hot fi_cntr": ["-p", prov, "-t", "msg", "--hot-cntr"],
    "MSG/MSG, cold wait obj": ["-p", prov, "-t", "msg", "--cold-wait"],
    "MSG single EP (baseline)": ["-p", prov, "-t", "msg", "-s"],
}
mat = []
for lab, a in MATRIX.items():
    for cold in (False, True):
        args = a + dom + ["-m", "hol", "-n", str(N), "-w", str(W), "-W", "8"] + PIN + ([] if cold else ["--no-cold"])
        d = runner.try_pair("sf_bench", args, env=ENV, **PAIR); raw.append(d)
        mat.append(runner.rows_hol(d, lab))
mat = pd.DataFrame(mat); mat'''),
("md", "## 4. Application level: FabricBlobChannel vs TcpBlobChannel"),
("code", '''import threading, time as _t
from middleware.fabric.channel import TcpBlobChannel
from middleware.fabric.pool import FabricBlobChannel
BLOBS = [4096, 65536, 1 << 20, 8 << 20]
REPS = 50 if CLUSTER else 10
def blob_bench(make_pair, label):
    out = []
    a, b = make_pair()
    try:
        for sz in BLOBS:
            payload = os.urandom(sz)
            done = threading.Event()
            def rx():
                for _ in range(REPS): b.recv(timeout=120)
                done.set()
            t = threading.Thread(target=rx); t.start()
            t0 = _t.perf_counter()
            for i in range(REPS): a.send(f"k{i}", payload, hot=sz <= 4096)
            done.wait(300); dt = _t.perf_counter() - t0; t.join()
            out.append({"label": label, "blob_bytes": sz, "MBps": sz * REPS / dt / 1e6, "ms_per_blob": dt / REPS * 1e3})
    finally:
        a.close(); b.close()
    return out
def pair(make_s, make_c):
    box = {}
    th = threading.Thread(target=lambda: box.setdefault("s", make_s())); th.start(); _t.sleep(0.3)
    c = make_c(); th.join(); return c, box["s"]
if CLUSTER:
    print("cluster: run benchmarks/fabric/blob_bench.py on both nodes (server on PEER) for cross-node numbers;"
          " in-process numbers below are loopback on this host only")
port = 31500 + os.getpid() % 300
app = blob_bench(lambda: pair(lambda: TcpBlobChannel.listen(port, "127.0.0.1"), lambda: TcpBlobChannel.connect("127.0.0.1", port)), "TcpBlobChannel loopback")
fp = "tcp" if not CLUSTER else "verbs"
app += blob_bench(lambda: pair(lambda: FabricBlobChannel.listen(port + 1, "127.0.0.1", provider=fp, ep_type="msg", nslots=4, slot_mb=4),
                               lambda: FabricBlobChannel.connect("127.0.0.1", port + 1, provider=fp, ep_type="msg", nslots=4, slot_mb=4)),
                  f"FabricBlobChannel {fp} MSG loopback")
app = pd.DataFrame(app); app'''),
("code", '''save("libfabric_vs_libibverbs", {"latency": lat.to_dict("records"), "bandwidth": bw.to_dict("records"),
                                    "matrix": mat.to_dict("records"), "blob": app.to_dict("records"), "raw": raw})
fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
ok = lat.dropna(subset=["p50_us"]) if "p50_us" in lat else lat
for lab, g in ok.groupby("label"):
    ax[0].plot(g["size"], g["p50_us"], marker="o", label=f"{lab} p50"); ax[0].plot(g["size"], g["p99_us"], ls="--", alpha=.6)
ax[0].set_xscale("log", base=2); ax[0].set_yscale("log"); ax[0].set_xlabel("bytes"); ax[0].set_ylabel("one-way us (dashed p99)"); ax[0].legend(fontsize=7); ax[0].grid(alpha=.3)
okb = bw.dropna(subset=["MBps"]) if "MBps" in bw else bw
for (lab, wait), g in okb.groupby(["label", "cold_wait"]):
    ax[1].plot(g["size"], g["MBps"], marker="o", label=f"{lab}{' wait' if wait else ''}")
ax[1].set_xscale("log", base=2); ax[1].set_xlabel("bytes"); ax[1].set_ylabel("MB/s"); ax[1].legend(fontsize=7); ax[1].grid(alpha=.3)
plt.tight_layout()'''),
("code", '''# LaTeX table fragment for the update (cluster runs only)
if CLUSTER:
    t = ok.pivot_table(index="size", columns="label", values="p50_us")
    tex = t.to_latex(float_format="%.2f", caption="Hot-path one-way latency p50 ($\\\\mu$s), cq signaling", label="tab:fabric-lat")
    (RESULTS / f"{HOST}_latency_table.tex").write_text(tex); print(tex)'''),
("md", "## 5. Telemetry export (what Prometheus scrapes from a worker)"),
("code", '''from middleware import telemetry
print(telemetry.default().prometheus_text()[:1500])'''),
]
build("03_libfabric_vs_libibverbs.ipynb", "03 · libfabric vs libibverbs",
      "The dual pool on libfabric (verbs MSG, verbs;ofi_rxm RDM, mixed) against the native libibverbs pool, same harness.",
      PARAMS + 'RESULTS_SUBDIR = "fabric"\n', cells)
