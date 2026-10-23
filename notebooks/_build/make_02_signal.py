from nbtools import build
from _fabric_params import PARAMS, COMMON

cells = [
("md", """Update 7, next step 3: how should the receiver learn that a hot write landed?

| mechanism | initiator | target detects by | cost / caveat |
|---|---|---|---|
| `cq` | `fi_writedata` / WRITE_WITH_IMM | polling the RX CQ for remote CQ data | consumes a posted receive per message |
| `flag` | plain write, last 8 B = sequence | spinning on memory | relies on in-order placement of the last bytes (holds per packet on RC; not a spec guarantee for multi-packet messages) |
| `sentinel` | payload write, then 8 B sentinel write | spinning on the sentinel | needs write-after-write ordering on the endpoint |
| `cntr` | plain write | `FI_REMOTE_WRITE` counter | libfabric only; providers that do not count remote writes are detected by a probe and skipped |
| `read` | write then 8 B read | (initiator) read completion | one-way delivery confirmation, the GPFS flush pattern; not a ping-pong |

`--perf` adds user-space instructions retired per post (perf_event_open), the per-operation overhead metric
from Papadopoulou et al. Adopt a mechanism only if it moves p99."""),
("code", COMMON),
("code", '''MECHS = ["cq", "flag", "sentinel", "cntr", "read"]
SIZES = "8,64,512,4096,16384" if CLUSTER else "64,4096"
raw, rows = [], []
for st in STACKS:
    for m in MECHS:
        d = runner.try_pair(st["tool"], st["args"] + ["-m", "sig", "-M", m, "-n", str(N), "-w", str(W), "-S", SIZES, "--perf"], env=ENV, **PAIR)
        raw.append(d); rows += runner.rows_sig(d, st["label"])
df = pd.DataFrame(rows)
df[[c for c in ["label", "mech", "size", "p50_us", "p99_us", "p999_us", "post_instructions_mean", "metric", "skipped", "error"] if c in df]]'''),
("code", '''save("completion_signaling", {"rows": rows, "raw": raw})
ok = df.dropna(subset=["p50_us"]) if "p50_us" in df else df
labels = list(dict.fromkeys(ok.label))
fig, axes = plt.subplots(1, len(labels), figsize=(6 * len(labels), 4.5), squeeze=False)
for ax, lab in zip(axes[0], labels):
    for m, g in ok[ok.label == lab].groupby("mech"):
        ax.plot(g["size"], g["p99_us"], marker="o", label=f"{m} p99")
        ax.plot(g["size"], g["p50_us"], ls="--", alpha=.5)
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_title(lab, fontsize=9)
    ax.set_xlabel("payload (B)"); ax.set_ylabel("us (solid p99, dashed p50)"); ax.grid(alpha=.3); ax.legend(fontsize=7)
plt.tight_layout()'''),
]
build("02_completion_signaling.ipynb", "02 · Completion signaling on the hot path",
      "CQ data vs flag-in-payload vs sentinel vs remote-write counter vs trailing READ, with per-post instruction counts.",
      PARAMS + 'RESULTS_SUBDIR = "fabric"\n', cells)
