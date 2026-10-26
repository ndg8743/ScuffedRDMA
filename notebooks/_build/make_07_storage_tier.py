"""Build notebooks/07_storage_tier.ipynb."""
from nbtools import build

PARAMS = '''MODE = "local"            # "local" | "cluster"
RESULTS_SUBDIR = "storage_tier"
SPILL_DIR = "/tmp/scuffed-spill" if MODE == "local" else "/mnt/nvme/scuffed-spill"   # cluster: a directory on the NVMe under test
O_DIRECT = MODE == "cluster"
FSYNC = True
BLOCK_KB = 64 if MODE == "local" else 1568          # 1568 KiB matches the Update 6 block (3-bit, 256 tokens, 32 heads, dim 128, unpacked)
BLOCK_SIZES_KB = [16, 64] if MODE == "local" else [256, 1568, 4096]
COALESCE = [1, 2, 5, 10, 20, 50]
BATCHES = 5 if MODE == "local" else 50'''

CELLS = [
("md", r"""## Math: the storage tier and the spill decision

**Section 12, the NVMe tier.** `StorageTier` spills KV blocks to one backing file with coalesced writes (one `pwrite` + `fdatasync` per batch of `coalesce` blocks), batched contiguous reads, a CRC-32 on every read, a free list of extents, and optional `O_DIRECT`. Four properties are argued in [docs/explained/12](../docs/explained/12-storage-tier.md): every write is aligned ($a = 4096$ divides offset, length and address, so `O_DIRECT` never rejects one); the free list never hands out overlapping space (invariants I1–I3 preserved by first-fit allocation and merge-on-release); corruption is detected (CRC-32 catches every burst error up to 32 bits and all but $2^{-32}$ of longer ones); and the cost of a coalesced write of $n$ blocks of $B$ bytes follows

$$
t(n) = a + n\,b, \qquad \text{throughput}(n) = \frac{nB}{a + nb} \xrightarrow{n \to \infty} \frac{B}{b},
$$

with $a$ the fixed cost of a write-plus-sync and $b$ the per-block cost. The first cell fits $a, b$ to the Update 6 sweep on server 2's NVMe ($B = 1568$ KiB) and plots the fit: it matches $n = 10, 20, 50$ and the asymptote (about 839 MB/s), and misses $n = 1$, which was faster than a constant fixed cost allows. The sweep below adds batch sizes and repeats so the next cluster run can separate the effects.

**Section 10, the spill choice.** Above a GPU-memory watermark $u_0$ the PMP controller adds a third option with switching coefficient

$$
\sigma_S = \delta\, q_S\, \mu_S - \gamma\, p, \qquad p = \frac{\max(0, u - u_0)}{1 - u_0},
$$

against $\sigma_H = \alpha q_H C\mu_H$ and $\sigma_C = \beta q_C C\mu_C$; the Hamiltonian is linear on the simplex $u_H + u_C + u_S = 1$, so the minimum is at a vertex and the smallest coefficient wins (bang-bang with three options). Below the watermark $\sigma_S = +\infty$ and the two-queue rule is unchanged. The pressure term $\gamma p$ is what makes spill win as memory fills; the figure in section 2 sweeps it. (The two-queue rule's sign problem from notebook 04 is inherited here.)

Local mode writes small blocks under `/tmp`; those numbers say nothing about NVMe. Cluster mode: set `SPILL_DIR` to a directory on the drive under test."""),
("code", """import numpy as np
from middleware.rdma_tensor_cache.storage_tier import StorageTier, IntegrityError, benchmark_coalescing
from middleware.rdma_tensor_cache.pmp_controller import PMPController, StorageDecision
from middleware.policy import PolicyEngine
from middleware.telemetry import SignalVector, Telemetry
Path(SPILL_DIR).mkdir(parents=True, exist_ok=True)"""),
("md", "### 0. The coalescing cost model fitted to the Update 6 sweep (model figure)"),
("code", """prev_path = ROOT / "benchmarks" / "results" / "test_arch" / "chimera_storage_spill.json"
prev = json.loads(prev_path.read_text())
n = np.array([r["coalesce"] for r in prev["coalesce_results"]], dtype=float)
t_us = np.array([r["write_us"] for r in prev["coalesce_results"]])
Bk = prev["single_block_kb"] * 1024
A = np.vstack([np.ones_like(n), n]).T
(a_us, b_us), *_ = np.linalg.lstsq(A, t_us, rcond=None)
asym = Bk / (b_us * 1e-6) / 1e6
print(f"fit: a = {a_us/1e3:.2f} ms, b = {b_us/1e3:.2f} ms per block, asymptote B/b = {asym:.0f} MB/s")
for ni, ti in zip(n, t_us):
    print(f"  n={ni:3.0f}: measured {ti/1e3:8.2f} ms, model {(a_us + b_us*ni)/1e3:8.2f} ms  ({(ti - a_us - b_us*ni)/ti*100:+.1f}%)")
nn = np.linspace(1, 60, 200)
figf, ax = plt.subplots(1, 2, figsize=(10, 3.2))
ax[0].plot(n, t_us / 1e3, "o", color=C["spill"], label="measured (server 2 NVMe, Update 6)"); ax[0].plot(nn, (a_us + b_us * nn) / 1e3, color=C["ink"], lw=1, label=f"fit a + n b, a={a_us/1e3:.1f} ms, b={b_us/1e3:.2f} ms")
ax[0].set_xlabel("blocks per write n"); ax[0].set_ylabel("write + fdatasync time (ms)"); ax[0].legend(); ax[0].set_title("coalesced write time")
ax[1].plot(n, [r["write_mbps"] for r in prev["coalesce_results"]], "o", color=C["spill"], label="measured write MB/s")
ax[1].plot(nn, nn * Bk / ((a_us + b_us * nn) * 1e-6) / 1e6, color=C["ink"], lw=1, label="model nB/(a+nb)"); ax[1].axhline(asym, color=C["muted"], ls="--", lw=1)
ax[1].text(2, asym * 1.01, f"asymptote {asym:.0f} MB/s", fontsize=7, color=C["muted"]); ax[1].set_xscale("log"); ax[1].set_xlabel("blocks per write n"); ax[1].set_ylabel("MB/s"); ax[1].legend(); ax[1].set_title("throughput")
fig("12_coalescing_fit", model=True, caption="least squares on four points; the n=1 miss is the open question in the write-up")"""),
("md", "### 1. Functional check: spill, retrieve, corruption detection, free-list reuse"),
("code", """tel = Telemetry()
t = StorageTier(SPILL_DIR, coalesce=4, o_direct=O_DIRECT, telemetry=tel)
print("O_DIRECT:", t.o_direct_reason)
blocks = {f"req7:L{l}": np.random.default_rng(l).integers(0, 256, 50_000, dtype=np.uint8).tobytes() for l in range(10)}
futs = [t.spill(k, v) for k, v in blocks.items()]
t.flush(); [f.result() for f in futs]
assert all(t.retrieve(k).result() == v for k, v in blocks.items())
assert t.retrieve_batch(list(blocks)) == blocks
off = t.extent("req7:L3").offset
with open(t.path, "r+b") as f:
    f.seek(off + 5); f.write(b"\\x00" if blocks["req7:L3"][5] else b"\\x01")
try:
    t.retrieve("req7:L3").result(); print("corruption NOT detected")
except IntegrityError as e:
    print("corruption detected:", e)
t.delete("req7:L3"); t.spill("small", b"x" * 100); t.flush()
print("reused freed slot:", t.extent("small").offset == off)
print(t.stats())
print("telemetry storage:", {k: v for k, v in tel.snapshot()["classes"]["storage"].items() if k in ("ops", "bytes", "p50_us", "p99_us")})
t.close(remove=True)"""),
("md", "### 2. Who decides to spill (model figure)\n\nAbove the watermark `u0`, spill competes with the hot and cold queues through `sigma_S = delta * q_S * mu_S - gamma * p`. Below it, the two-queue decision is unchanged."),
("code", """pmp = PMPController(u0=0.85)
grid_u = np.linspace(0.5, 1.0, 101)
grid_qs = [0, 50, 100, 200]
figs, ax = plt.subplots(1, 2, figsize=(10, 3.2))
for qs, col in zip(grid_qs, (C["ok"], C["gold"], C["hot"], C["bad"])):
    pmp.reset()
    dec = [pmp.decide_with_storage(hot_depth=4, cold_depth=10, gpu_mem_util=u, spill_depth=qs) for u in grid_u]
    ax[0].step(grid_u, [{"hot": 2, "cold": 1, "spill": 0}[d.value] for d in dec], where="post", color=col, label=f"spill queue depth {qs}")
ax[0].set_yticks([0, 1, 2]); ax[0].set_yticklabels(["spill", "cold", "hot"]); ax[0].set_xlabel("GPU memory utilization u"); ax[0].axvline(0.85, color=C["muted"], ls=":", lw=1)
ax[0].set_title("decision vs memory pressure (hot depth 4, cold depth 10)"); ax[0].legend()
u = grid_u; p = np.clip((u - 0.85) / 0.15, 0, None)
ax[1].plot(u, pmp._alpha * 4 * pmp._mu_hot * np.ones_like(u), color=C["hot"], label="sigma_H"); ax[1].plot(u, pmp._beta * 10 * pmp._mu_cold * np.ones_like(u), color=C["cold"], label="sigma_C")
for qs, col in zip(grid_qs, (C["ok"], C["gold"], C["hot"], C["bad"])):
    ax[1].plot(u, pmp._delta * qs * pmp._mu_spill - pmp._gamma * p, color=col, ls="--", lw=1, label=f"sigma_S, q_S={qs}")
ax[1].set_xlabel("GPU memory utilization u"); ax[1].set_ylabel("switching coefficient"); ax[1].set_title("the smallest coefficient wins"); ax[1].legend(ncol=3, fontsize=6, loc="lower left")
fig("10_pmp_spill", model=True, caption="three-option bang-bang; the pressure term gamma*p pulls sigma_S below the others as u -> 1")
eng = PolicyEngine.default_policy()
for ctx in ({"gpu_mem_util": 0.6, "link_util": 0.2}, {"gpu_mem_util": 0.95, "link_util": 0.2}):
    d = eng.decide(SignalVector(size_bytes=8 << 20, role="kv", phase="prefill"), ctx)
    print(ctx, "->", d.route, "(rule:", d.rules["route"] + ")")"""),
("md", "### 3. Coalescing sweep (measured)"),
("code", """res = benchmark_coalescing(SPILL_DIR, block_bytes=BLOCK_KB * 1024, coalesce_list=COALESCE, batches=BATCHES,
                           o_direct=O_DIRECT, fsync=FSYNC, block_sizes=[b * 1024 for b in BLOCK_SIZES_KB],
                           meta={"bits": 3, "dim": 128, "seq_len": 256, "heads": 32})
print("O_DIRECT:", res["o_direct"])
for sw in res["sweeps"]:
    print(f"block {sw['single_block_kb']:.0f} KiB")
    for r in sw["coalesce_results"]:
        print(f"  coalesce={r['coalesce']:>3} payload={r['payload_kb']:>9.1f} KiB  write p50={r['write_us']:>9.0f} us "
              f"({r['write_mbps']:>7.1f} MB/s, p99 {r['write_p99_us']:.0f})  read p50={r['read_us']:>9.0f} us ({r['read_mbps']:>7.1f} MB/s)")"""),
("code", """figx, axes = plt.subplots(1, 2, figsize=(10, 3.2))
for sw in res["sweeps"]:
    c = [r["coalesce"] for r in sw["coalesce_results"]]
    axes[0].plot(c, [r["write_mbps"] for r in sw["coalesce_results"]], marker="o", label=f"{sw['single_block_kb']:.0f} KiB")
    axes[1].plot(c, [r["read_mbps"] for r in sw["coalesce_results"]], marker="o", label=f"{sw['single_block_kb']:.0f} KiB")
pc = [r["coalesce"] for r in prev["coalesce_results"]]
axes[0].plot(pc, [r["write_mbps"] for r in prev["coalesce_results"]], "k--", marker="x", label="Update 6, server 2 (file per write)")
axes[1].plot(pc, [r["read_mbps"] for r in prev["coalesce_results"]], "k--", marker="x", label="Update 6, server 2 (file per write)")
for ax, t_ in zip(axes, ("write (pwrite + fdatasync)", "read (one pread per batch)")):
    ax.set_xscale("log"); ax.set_xlabel("coalesce depth"); ax.set_ylabel("MB/s"); ax.set_title(t_); ax.legend()
plt.suptitle(f"{HOST} ({MODE})")
fig("12_storage_sweep", caption="local mode: /tmp on this host, not NVMe")
save("storage_spill", {**res, "coalescing_fit_update6": {"a_ms": a_us / 1e3, "b_ms_per_block": b_us / 1e3, "asymptote_MBps": asym}})"""),
]

if __name__ == "__main__":
    print(build("07_storage_tier.ipynb", "07 · Storage tier: KV spill and retrieve, and the spill decision",
                "The coalescing cost model fitted to the Update 6 NVMe sweep, the functional checks (alignment, free list, CRC), the PMP three-option spill choice, and a coalescing sweep through StorageTier.",
                PARAMS, CELLS, sections=[(12, "NVMe storage tier", "12-storage-tier.md"), (10, "PMP bang-bang controller: hot, cold or spill", "10-pmp-controller.md")]))
