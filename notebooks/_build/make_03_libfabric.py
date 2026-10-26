from nbtools import build
from _fabric_params import PARAMS, COMMON

cells = [
("md", r"""## Math: one endpoint per class, and a credit window that never blocks the link

**Section 4, the dual pool.** The pool opens one endpoint per traffic class, each with its own transmit queue and completion objects, so nothing bulk is ever in front of a hot message in its own queue (section 2's $W_{\text{FIFO}}$ becomes the per-packet residual). Separate completion queues matter for the same reason: a CQ is read in order, so with $k$ cold completions queued ahead of a hot one the poller pays $k \cdot c_{\text{poll}}$ before it sees it; with a dedicated hot CQ that cost is independent of $k$. libfabric adds choices verbs does not expose directly: an `FI_EP_MSG` endpoint (connected, maps onto an RC queue pair) or `FI_EP_RDM` (reliable, unconnected, through `ofi_rxm`), counters (`fi_cntr`, with `FI_SELECTIVE_COMPLETION`) instead of a CQ for the hot class, and a wait object (`fi_cq_sread`) instead of busy polling for the cold class. `sv_bench` is the same benchmark source linked against `libscuffedverbs`, which implements the same API on raw RC queue pairs, so any difference between the two is the library.

**Section 5, the blob channel.** `FabricBlobChannel` carries key-value blobs over the pool with credits: each side registers $N$ receive slots of $B$ bytes (defaults $N = 8$, $B = 4$ MiB); the sender writes a chunk into a free slot at the peer with `fi_writedata`, and the receiver returns the slot with an 8-byte credit write after copying it out. Three properties are proved in [docs/explained/05](../docs/explained/05-blob-channel.md): a slot is never overwritten before it is consumed (a three-state invariant per slot), a staging buffer is never reused before its write completes, and a blob is delivered exactly when all its byte intervals have arrived (the intervals are consecutive and disjoint, the transport is reliable). What the window costs in throughput follows from Little's law. With $R$ the credit round trip (wire + receiver copy + credit write), at most $N$ chunks are in flight, so throughput $X$ satisfies

$$
N \;\ge\; X \cdot \frac{R}{B} \qquad\Longrightarrow\qquad X \;\le\; \frac{N B}{R},
$$

and the link rate $C$ is reachable only if the window covers the bandwidth-delay product, $NB \ge C R$. The next cell plots that bound: with 32 MiB in flight the channel is window-limited only when a credit takes longer than about 27 ms to come back on 10 Gb/s (2.7 ms on 100 Gb/s), far above a real credit round trip. So in E6, if `FabricBlobChannel` is slower than `TcpBlobChannel`, the cause is not the window."""),
("code", COMMON),
("md", "## 0. The credit window bound (model figure)"),
("code", '''import numpy as np
Nslots, Bslot = 8, 4 << 20
R = np.logspace(-5, -1, 200)                    # credit round trip, 10 us .. 100 ms
X = Nslots * Bslot / R                           # bytes per second
figm, ax = plt.subplots(figsize=(6, 3.2))
ax.plot(R * 1e3, X * 8 / 1e9, color=C["cold"], label=f"window bound NB/R, N={Nslots}, B={Bslot >> 20} MiB")
for rate, col in ((10, C["hot"]), (25, C["gold"]), (100, C["ok"])):
    ax.axhline(rate, color=col, ls="--", lw=1); ax.text(R[0] * 1e3 * 1.2, rate * 1.15, f"{rate} Gb/s link", color=col, fontsize=7)
    print(f"{rate:>3} Gb/s link is window-limited when the credit RTT exceeds {Nslots * Bslot * 8 / (rate * 1e9) * 1e3:.1f} ms")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("credit round trip R (ms)"); ax.set_ylabel("max throughput (Gb/s)")
ax.set_title("FabricBlobChannel: Little's-law throughput bound"); ax.legend()
fig("05_credit_window", model=True, caption="arithmetic from the defaults")'''),
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
("code", '''figx, ax = plt.subplots(1, 2, figsize=(11, 3.8))
ok = lat.dropna(subset=["p50_us"]) if "p50_us" in lat else lat
for lab, g in ok.groupby("label"):
    ax[0].plot(g["size"], g["p50_us"], marker="o", label=f"{lab} p50"); ax[0].plot(g["size"], g["p99_us"], ls="--", alpha=.6)
ax[0].set_xscale("log", base=2); ax[0].set_yscale("log"); ax[0].set_xlabel("bytes"); ax[0].set_ylabel("one-way us (dashed p99)"); ax[0].legend()
ax[0].set_title(f"hot path, cq signaling  ({HOST}, {MODE})")
okb = bw.dropna(subset=["MBps"]) if "MBps" in bw else bw
for (lab, wait), g in okb.groupby(["label", "cold_wait"]):
    ax[1].plot(g["size"], g["MBps"], marker="o", label=f"{lab}{' wait' if wait else ''}")
ax[1].set_xscale("log", base=2); ax[1].set_xlabel("bytes"); ax[1].set_ylabel("MB/s"); ax[1].legend(); ax[1].set_title("cold path, busy poll vs wait object")
fig("04_dualpool_latency_bw", caption="E1, E2")'''),
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
("code", '''okm = mat.dropna(subset=["hot_p99_us"]) if "hot_p99_us" in mat else mat
if len(okm):
    piv = okm.pivot_table(index="label", columns="cold_on", values="hot_p99_us")
    piv.columns = ["cold off", "cold on"] if list(piv.columns) == [0, 1] else piv.columns
    figm2, ax = plt.subplots(figsize=(7, 3.4))
    piv.plot.bar(ax=ax, color=[C["cold"], C["hot"]][: len(piv.columns)]); ax.set_yscale("log"); ax.set_ylabel("hot RTT p99 (us)")
    ax.set_title(f"libfabric configurations under a cold stream  ({HOST}, {MODE})"); ax.set_xlabel("")
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
    fig("04_dualpool_matrix", caption="E3, E4: which endpoint/completion combination keeps hot p99 flat under load")
else:
    print("no matrix rows completed")'''),
("md", "## 4. Application level: FabricBlobChannel vs TcpBlobChannel"),
("code", '''import threading, time as _t
from middleware.fabric.channel import TcpBlobChannel
from middleware.fabric.pool import FabricBlobChannel
BLOBS = [4096, 65536, 1 << 20, 8 << 20]
REPS = 50 if CLUSTER else 10
def blob_bench(make_pair, label):
    """One channel pair per blob size so a stalled size cannot poison the next one.
    A size that does not finish within the timeout is recorded with ok=False instead of hanging the notebook."""
    out = []
    for sz in BLOBS:
        a, b = make_pair()
        try:
            payload = os.urandom(sz)
            done, err = threading.Event(), {}
            def rx():
                try:
                    for _ in range(REPS): b.recv(timeout=20)
                    done.set()
                except Exception as e:
                    err["recv"] = repr(e)
            t = threading.Thread(target=rx, daemon=True); t.start()
            t0 = _t.perf_counter()
            import inspect
            skw = {"timeout": 20} if "timeout" in inspect.signature(a.send).parameters else {}
            try:
                for i in range(REPS): a.send(f"k{i}", payload, hot=sz <= 4096, **skw)
            except Exception as e:
                err["send"] = repr(e)
            ok = done.wait(30) and not err; dt = _t.perf_counter() - t0
            out.append({"label": label, "blob_bytes": sz, "ok": ok, "MBps": sz * REPS / dt / 1e6 if ok else float("nan"),
                        "ms_per_blob": dt / REPS * 1e3 if ok else float("nan"), "error": "; ".join(f"{k}: {v}" for k, v in err.items()) or ("timeout" if not ok else "")})
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
app = pd.DataFrame(app)
if not app.ok.all():
    print("NOTE: some blob sizes did not complete:", app[~app.ok][["label", "blob_bytes", "error"]].to_dict("records"))
    print("      multi-chunk blobs (larger than one slot) stall intermittently on the libfabric tcp provider loopback; see benchmarks/fabric/blob_multichunk_check.py")
app'''),
("code", '''figb, ax = plt.subplots(1, 2, figsize=(10, 3.4))
for lab, g in app[app.ok].groupby("label"):
    ax[0].plot(g.blob_bytes, g.MBps, marker="o", label=lab); ax[1].plot(g.blob_bytes, g.ms_per_blob, marker="o", label=lab)
for a_, yl in zip(ax, ("MB/s", "ms per blob")):
    a_.set_xscale("log", base=2); a_.set_yscale("log"); a_.set_xlabel("blob bytes"); a_.set_ylabel(yl); a_.legend()
ax[0].set_title(f"blob channel throughput  ({HOST}, {MODE})"); ax[1].set_title("time per blob")
fig("05_blob_channel", caption="E6 (loopback here; cross-node from benchmarks/fabric/blob_bench.py)")
save("libfabric_vs_libibverbs", {"latency": lat.to_dict("records"), "bandwidth": bw.to_dict("records"),
                                    "matrix": mat.to_dict("records"), "blob": app.to_dict("records"), "raw": raw})'''),
("code", '''# LaTeX table fragment for the update (cluster runs only)
if CLUSTER:
    t = ok.pivot_table(index="size", columns="label", values="p50_us")
    tex = t.to_latex(float_format="%.2f", caption="Hot-path one-way latency p50 ($\\\\mu$s), cq signaling", label="tab:fabric-lat")
    (RESULTS / f"{HOST}_latency_table.tex").write_text(tex); print(tex)'''),
("md", "## 5. Telemetry export (what Prometheus scrapes from a worker)"),
("code", '''from middleware import telemetry
print(telemetry.default().prometheus_text()[:1500])'''),
]
build("03_libfabric_vs_libibverbs.ipynb", "03 · The dual pool on libfabric vs libibverbs, and the blob channel",
      "The dual pool on libfabric (verbs MSG, verbs;ofi_rxm RDM, mixed) against the native libibverbs pool, same harness; the credit-window bound; FabricBlobChannel vs TcpBlobChannel.",
      PARAMS + 'RESULTS_SUBDIR = "fabric"\n', cells,
      sections=[(4, "The dual pool on libfabric", "04-dual-pool.md"), (5, "FabricBlobChannel: credits and one-sided writes", "05-blob-channel.md")])
