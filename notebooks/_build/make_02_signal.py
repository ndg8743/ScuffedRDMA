from nbtools import build
from _fabric_params import PARAMS, COMMON

cells = [
("md", r"""## Math: what each completion mechanism relies on

A one-sided RDMA write places bytes in the target's memory without involving the target's CPU, so the target needs some way to learn the bytes are there. Five mechanisms, and the ordering fact each one needs to be correct ([docs/explained/06](../docs/explained/06-completion-signaling.md)):

- **Fact 1 (in-order execution).** Operations posted on one reliable connection (RC queue pair, `FI_EP_MSG` endpoint) are executed by the target in the order they were posted. Guaranteed by the InfiniBand architecture for RC.
- **Fact 2 (completion after placement).** A write-with-immediate generates the target-side completion only after the data has been placed. Guaranteed (`fi_rma(3)`: remote CQ data is reported after the data is available).
- **Not guaranteed:** the order in which the *bytes of one message* become visible in memory. Packets of a multi-packet message may be placed out of order.

| mechanism | initiator posts | target detects by | needs | per-message cost |
|---|---|---|---|---|
| `cq` | `fi_writedata` (WRITE_WITH_IMM) | RX CQ entry with remote CQ data | Fact 2 | one posted receive consumed, one CQ poll |
| `flag` | one write, last 8 B = sequence number | spinning on that word | in-order placement of the last word: holds within one packet, not across packets | none (one cache line read) |
| `sentinel` | payload write, then an 8 B write | spinning on the sentinel | Fact 1 plus write-after-write ordering (`FI_ORDER_WAW`) | a second work request |
| `cntr` | one write | `FI_REMOTE_WRITE` counter | provider must count remote writes (probed; skipped if not) | counter read |
| `read` | write, then an 8 B RDMA read | initiator's read completion | Fact 1: the read is executed after the write, so its response proves placement | a round trip; this is the IBM Storage Scale write flush (`verbsRdmaWriteFlush = rdma-read`) |

The expected ordering of latencies is `flag` < `sentinel` ≈ `cntr` < `cq` < `read`, because each adds one more thing the NIC or the CPU must do per message. Whether that ordering holds, and by how much, is E5. `--perf` adds user-space instructions retired per post (`perf_event_open`), the per-operation overhead metric from Papadopoulou et al. A mechanism is worth adopting only if it moves p99 and is correct on the NIC in use."""),
("code", COMMON),
("md", "## Measured: one-way latency per mechanism and payload"),
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
figx, axes = plt.subplots(1, len(labels), figsize=(5 * len(labels), 3.6), squeeze=False)
for ax, lab in zip(axes[0], labels):
    for m, g in ok[ok.label == lab].groupby("mech"):
        ax.plot(g["size"], g["p99_us"], marker="o", label=f"{m} p99")
        ax.plot(g["size"], g["p50_us"], ls="--", alpha=.5)
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_title(f"{lab}  ({HOST}, {MODE})", fontsize=9)
    ax.set_xlabel("payload (B)"); ax.set_ylabel("us (solid p99, dashed p50)"); ax.legend()
fig("06_completion_measured", caption="E5; local mode is the tcp provider on one host")'''),
("code", '''# instructions retired per post, when perf counters are available
if "post_instructions_mean" in ok and ok["post_instructions_mean"].notna().any():
    piv = ok.pivot_table(index="mech", columns="label", values="post_instructions_mean")
    print(piv.round(0))
    figp, ax = plt.subplots(figsize=(5.5, 3))
    piv.plot.bar(ax=ax); ax.set_ylabel("instructions / post (mean)"); ax.set_title("per-operation overhead by mechanism")
    fig("06_completion_instructions")
else:
    print("no perf counters on this host (perf_event_open unavailable); instructions/post skipped")'''),
]
build("02_completion_signaling.ipynb", "02 · Completion signaling on the hot path",
      "CQ data vs flag-in-payload vs sentinel vs remote-write counter vs trailing READ, with per-post instruction counts: what each relies on, and what it costs.",
      PARAMS + 'RESULTS_SUBDIR = "fabric"\n', cells,
      sections=[(6, "How the receiver learns data arrived", "06-completion-signaling.md")])
