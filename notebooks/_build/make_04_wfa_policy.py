"""Build notebooks/04_wfa_and_policy.ipynb."""
from nbtools import build

PARAMS = '''MODE = "local"            # "local" | "cluster"
RESULTS_SUBDIR = "wfa_policy"
SEED = 0
N_TRAIN = 6000 if MODE == "local" else 60000     # events per training trace (two traces, two model shapes)
N_TEST = 4000 if MODE == "local" else 40000
EPOCHS = 300
SIGNAL_GLOB = "benchmarks/results/**/*signals*.jsonl"   # real telemetry dumps, cluster mode'''

CELLS = [
("md", """## What this notebook checks

Thesis components 2 and 3: the WFA classifier with learned transition weights (`middleware/rdma_tensor_cache/wfa_learner.py`) and the Rule-Node Expression Tree policy (`middleware/policy/`).

Training and evaluation traces are **synthetic** (`SyntheticTraceGenerator`). The oracle label per transfer is defined in `oracle_label()`:

| label | traffic |
|---|---|
| hot | token ids, scheduler metadata, decode KV deltas up to 256 KiB |
| warm | decode prefix fetches over 256 KiB, prefill chunks up to 64 KiB |
| cold | prefill KV over 64 KiB, weights, SSM state snapshots |

Accuracy numbers here only show the learner and the harness work against that oracle. They are not testbed measurements. In cluster mode the last section replays real signal dumps if any exist under `benchmarks/results/`."""),
("code", """import numpy as np
import matplotlib.pyplot as plt
from middleware.rdma_tensor_cache.wfa_learner import (
    LearnedWFA, ModelShape, SyntheticTraceGenerator, evaluate, evaluate_static, PHI_NAMES, STATES,
    from_telemetry, latency_label)
from middleware.rdma_tensor_cache.wfa_classifier import WFAClassifier
from middleware.policy import PolicyEngine
from middleware.telemetry import SignalVector, Telemetry"""),
("md", "### Train on two model shapes"),
("code", """mix = {"prefill": 0.3, "decode": 0.3, "control": 0.2, "bursty": 0.1, "chunked": 0.1}
train = [
    SyntheticTraceGenerator(seed=SEED + 1).generate(N_TRAIN, mix),
    SyntheticTraceGenerator(seed=SEED + 2, model=ModelShape(layers=24, kv_heads=4, head_dim=128)).generate(N_TRAIN, mix),
]
model = LearnedWFA(epochs=EPOCHS, seed=SEED).fit(train)
plt.figure(figsize=(5, 3)); plt.plot(model.loss_history); plt.yscale("log")
plt.xlabel("epoch"); plt.ylabel("cross entropy + L2"); plt.title("LearnedWFA training"); plt.show()
print("final loss", model.loss_history[-1])"""),
("md", "### Held-out mixes: learned WFA vs static threshold WFAClassifier\n\nHeld-out traces use a third model shape (32 layers, head_dim 128) and different pattern mixes."),
("code", """heldout = {
    "base": None,
    "decode-heavy": {"decode": 0.8, "control": 0.2},
    "prefill-heavy": {"prefill": 0.8, "control": 0.1, "weights": 0.1},
    "bursty": {"bursty": 0.7, "chunked": 0.3},
}
rows = []
evals = {}
for i, (name, m) in enumerate(heldout.items()):
    tr = [SyntheticTraceGenerator(seed=SEED + 100 + i, model=ModelShape(layers=32, kv_heads=8, head_dim=128)).generate(N_TEST, m)]
    e, s = evaluate(model, tr), evaluate_static(tr, WFAClassifier())
    evals[name] = (e, s)
    rows.append((name, e["n"], e["state_accuracy"], e["routing_accuracy"], e["hot_precision"], e["hot_recall"],
                 s["routing_accuracy"], s["hot_precision"], s["hot_recall"]))
hdr = ("mix", "n", "learned state acc", "learned route acc", "learned hot P", "learned hot R",
       "static route acc", "static hot P", "static hot R")
print(" | ".join(hdr))
for r in rows:
    print(" | ".join([r[0], str(r[1])] + [f"{x:.4f}" for x in r[2:]]))"""),
("code", """fig, axes = plt.subplots(1, len(evals), figsize=(4 * len(evals), 3.4))
for ax, (name, (e, s)) in zip(axes, evals.items()):
    cm = np.asarray(e["confusion_states"], dtype=float)
    cmn = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    ax.imshow(cmn, vmin=0, vmax=1, cmap="Greens")
    for a in range(3):
        for b in range(3):
            ax.text(b, a, int(cm[a, b]), ha="center", va="center", fontsize=8)
    ax.set_xticks(range(3)); ax.set_xticklabels(STATES); ax.set_yticks(range(3)); ax.set_yticklabels(STATES)
    ax.set_xlabel("predicted"); ax.set_ylabel("oracle"); ax.set_title(name)
plt.suptitle("LearnedWFA confusion (row-normalized color, raw counts)"); plt.tight_layout(); plt.show()
for name, (e, s) in evals.items():
    print(name, "static binary confusion [[tn, fp], [fn, tp]] =", s["confusion_binary"])"""),
("md", "### What the weights learned\n\nFor each current state, the logit margin of going **hot** versus **cold**, per standardized feature."),
("code", """W = np.asarray(model.W)
names = list(PHI_NAMES) + ["bias"]
margin = W[:, STATES.index("hot"), :] - W[:, STATES.index("cold"), :]
fig, ax = plt.subplots(figsize=(8, 3))
im = ax.imshow(margin, cmap="RdBu_r", vmin=-np.abs(margin).max(), vmax=np.abs(margin).max(), aspect="auto")
ax.set_yticks(range(3)); ax.set_yticklabels([f"from {s}" for s in STATES])
ax.set_xticks(range(len(names))); ax.set_xticklabels(names, rotation=60, ha="right", fontsize=8)
plt.colorbar(im, label="hot - cold logit"); plt.title("LearnedWFA transition weights"); plt.tight_layout(); plt.show()
wpath = RESULTS / f"{HOST}_learned_wfa_weights.json"
model.save(str(wpath)); print("weights ->", wpath)"""),
("md", "### Default policy on a mixed trace\n\n`middleware/policy/default_policy.json` with the learned WFA registered as classifier `wfa`. Context (GPU memory and link utilization) is swept to show the spill and compress rules fire."),
("code", """engine = PolicyEngine.default_policy(classifiers={"wfa": model})
trace = SyntheticTraceGenerator(seed=SEED + 7).generate(2000, {"bursty": 0.5, "chunked": 0.3, "decode": 0.2})
contexts = {"idle": {"gpu_mem_util": 0.5, "link_util": 0.1},
            "link busy": {"gpu_mem_util": 0.5, "link_util": 0.9},
            "gpu full + link busy": {"gpu_mem_util": 0.95, "link_util": 0.9}}
from collections import Counter
policy_summary = {}
for cname, ctx in contexts.items():
    model.reset()
    ds = engine.decide_many([s for s, _ in trace], ctx)
    routes = Counter(d.route for d in ds)
    comp = sum(d.compress for d in ds)
    owners = Counter(d.rules["route"] for d in ds)
    policy_summary[cname] = {"routes": dict(routes), "compressed": comp, "route_owner": dict(owners)}
    print(f"{cname:22s} routes={dict(routes)} compressed={comp}")
    print("   route set by:", dict(owners))"""),
("code", """model.reset()
examples = [
    SignalVector(size_bytes=48, role="token", phase="decode", tensor_id="tok:1"),
    SignalVector(size_bytes=96 << 10, role="kv", phase="decode", tensor_id="kv:9:3", layer_idx=3, seq_len=2048),
    SignalVector(size_bytes=6 << 20, role="kv", phase="prefill", tensor_id="kv:10:0", layer_idx=0, seq_len=4096),
]
for s in examples:
    d = engine.decide(s, contexts["gpu full + link busy"])
    print(f"--- size={s.size_bytes} role={s.role} phase={s.phase} -> route={d.route} compress={d.compress}")
    print(d.explain())"""),
("md", "### Cluster mode: replay real signal dumps\n\nRecord signals on the cluster with `Telemetry.observe(SignalVector(...))` in the transport path, then dump them one JSON object per line:\n\n```python\nfrom dataclasses import asdict\nwith open(f\"benchmarks/results/telemetry/{host}_signals.jsonl\", \"w\") as f:\n    for s in tel.signals():\n        f.write(json.dumps(asdict(s)) + \"\\n\")\n```\n\nLabels for real traffic come from `latency_label(threshold_us)` (role plus measured completion latency), since there is no oracle."),
("code", """import glob, math
real = {}
files = sorted(glob.glob(str(ROOT / SIGNAL_GLOB), recursive=True)) if MODE == "cluster" else []
if not files:
    print("no signal dumps found" + (" (local mode skips this)" if MODE == "local" else f" under {SIGNAL_GLOB}"))
for fp in files:
    tel = Telemetry(node=Path(fp).stem)
    for line in open(fp):
        d = json.loads(line)
        d = {k: (float("nan") if v is None and k in ("completion_us", "inter_arrival_us") else v) for k, v in d.items()}
        tel.observe(SignalVector(**d))
    traces = from_telemetry(tel, latency_label(threshold_us=50.0))
    e, s = evaluate(model, traces), evaluate_static(traces, WFAClassifier())
    real[Path(fp).name] = {"learned": e, "static": s}
    print(Path(fp).name, "n=", e["n"], "learned route acc", round(e["routing_accuracy"], 4),
          "static route acc", round(s["routing_accuracy"], 4))"""),
("code", """save("wfa_policy", {
    "synthetic": True,
    "train_events": sum(len(t) for t in train), "epochs": EPOCHS, "seed": SEED,
    "heldout": {k: {"learned": v[0], "static": v[1]} for k, v in evals.items()},
    "policy": policy_summary, "real_signal_replays": real,
})"""),
]

if __name__ == "__main__":
    p = build("04_wfa_and_policy.ipynb", "04 · Learned WFA and routing policy",
              "Learned transition weights for the WFA classifier, compared with the static thresholds, and the Rule-Node Expression Tree policy on mixed traffic.",
              PARAMS, CELLS)
    print(p)
