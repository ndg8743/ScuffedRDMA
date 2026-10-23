from nbtools import build
from _fabric_params import PARAMS, COMMON

cells = [
("md", """**Claim under test:** a small latency-critical transfer that shares a queue pair (endpoint) with bulk
transfers waits behind them (head-of-line blocking); splitting hot and cold traffic onto separate QPs /
endpoints removes that wait.

**Method.** `sf_bench -m hol` / `sv_bench -m hol`: the client streams bulk RDMA writes on the cold class
(window `-W`, size `--cold-size`) while the hot class ping-pongs small writes with immediate data. Hot
round-trip percentiles are measured with the cold stream off and on, with both classes on one endpoint
(`-s`, the baseline) and on separate endpoints (the dual pool). Same binary, same payloads, same timing for
native libibverbs and libfabric; only the library under it changes.

**Read it as:** the claim holds on a stack if dual-endpoint hot p99 under cold load stays near the unloaded
p99 while single-endpoint hot p99 grows with cold message size. If both grow, the bottleneck is below the
QP (the NIC or rxe's single kernel thread), which is itself a result worth reporting.

**Retraction.** The 8 µs cross-node figure from Update 4 (`benchmarks/results/dual_qp_remote_benchmark.json`)
came from a pool that did not check `wc.status`; 8 MB writes "completed" in about 8 µs, which 10GbE cannot do.
The pool now raises on error and flush completions. The last section re-runs that benchmark."""),
("code", COMMON),
("code", '''HOT_SIZES = [64, 4096]
COLD_SIZES = [256 * 1024, 1 << 20, 4 << 20] if CLUSTER else [256 * 1024, 1 << 20]
raw, rows = [], []
for st in STACKS:
    for single in (False, True):
        tag = "single EP" if single else "dual EP"
        for hot in HOT_SIZES:
            base = st["args"] + ["-m", "hol", "-n", str(N), "-w", str(W), "--hot-size", str(hot), "-W", "8"] + PIN + (["-s"] if single else [])
            d = runner.try_pair(st["tool"], base + ["--no-cold"], env=ENV, **PAIR)
            raw.append(d); rows.append(runner.rows_hol(d, f"{st['label']} | {tag}"))
            for cs in COLD_SIZES:
                d = runner.try_pair(st["tool"], base + ["--cold-size", str(cs)], env=ENV, **PAIR)
                raw.append(d); rows.append(runner.rows_hol(d, f"{st['label']} | {tag}"))
df = pd.DataFrame(rows)
df'''),
("code", '''save("hol_blocking", {"rows": rows, "raw": raw})
ok = df[df.get("error").isna()] if "error" in df else df
fig, axes = plt.subplots(1, len(HOT_SIZES), figsize=(7 * len(HOT_SIZES), 4.5), squeeze=False)
for ax, hot in zip(axes[0], HOT_SIZES):
    sub = ok[ok.hot_size == hot]
    for lab, g in sub.groupby("label"):
        g = g.sort_values(["cold_on", "cold_size"])
        x = ["off" if not c else f"{s >> 10} KiB" for c, s in zip(g.cold_on, g.cold_size)]
        ax.plot(x, g.hot_p99_us, marker="o", label=lab)
    ax.set_yscale("log"); ax.set_xlabel("cold stream"); ax.set_ylabel("hot RTT p99 (us)")
    ax.set_title(f"hot {hot} B"); ax.grid(alpha=.3)
axes[0][0].legend(fontsize=7)
plt.tight_layout()'''),
("code", '''# HOL penalty: loaded p99 / unloaded p99, single vs dual, per stack and cold size
pen = []
for lab, g in ok.groupby("label"):
    for hot, gh in g.groupby("hot_size"):
        un = gh[gh.cold_on == 0].hot_p99_us
        if un.empty: continue
        for _, r in gh[gh.cold_on == 1].iterrows():
            pen.append({"label": lab, "hot_size": hot, "cold_size": r.cold_size, "p99_ratio": r.hot_p99_us / un.iloc[0], "cold_MBps": r.cold_MBps})
pd.DataFrame(pen)'''),
("md", """## Re-run of the Update 4 pyverbs benchmark (cluster only)

`benchmarks/benchmark_dual_qp_remote.py` drives the Python pool. With the completion-status fix, a failed
write now raises instead of looking fast. Run it to replace the retracted number."""),
("code", '''if CLUSTER:
    out = RESULTS / f"{HOST}_dual_qp_remote_rerun.json"
    print("on the server node (PEER):")
    print(f"  python3 benchmarks/benchmark_dual_qp_remote.py --role server --device {DOMAIN}")
    r = sh(f"python3 benchmarks/benchmark_dual_qp_remote.py --role client --host {PEER_IP} --device {DOMAIN} --output {out}", check=False)
else:
    print("cluster mode only (needs pyverbs and an RDMA device on both nodes)")'''),
]
build("01_hol_blocking.ipynb", "01 · Head-of-line blocking: single vs dual endpoint",
      "Hot-class latency under a cold bulk stream, one endpoint vs two, on native libibverbs and libfabric.",
      PARAMS + 'RESULTS_SUBDIR = "fabric"\n', cells)
