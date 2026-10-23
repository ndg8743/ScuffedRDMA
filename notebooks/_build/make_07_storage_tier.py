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
("md", """## What this notebook checks

`middleware/rdma_tensor_cache/storage_tier.py`: KV spill / retrieve to local NVMe through one backing file, with coalesced writes (one `pwrite` + `fdatasync` per batch of `coalesce` blocks), contiguous batched reads, crc32 on every read, a free list, and optional O_DIRECT.

1. Functional check: spill, retrieve, corruption detection, free-list reuse.
2. PMP storage arm and the default policy deciding what to spill.
3. Coalescing sweep. Same JSON shape as the Update 6 run (`benchmarks/results/test_arch/chimera_storage_spill.json`), which used one file per write; this one goes through `StorageTier`.

Local mode writes small blocks under /tmp; those numbers say nothing about NVMe. Cluster mode: set `SPILL_DIR` to a directory on the drive under test."""),
("code", """import numpy as np
import matplotlib.pyplot as plt
from middleware.rdma_tensor_cache.storage_tier import StorageTier, IntegrityError, benchmark_coalescing
from middleware.rdma_tensor_cache.pmp_controller import PMPController, StorageDecision
from middleware.policy import PolicyEngine
from middleware.telemetry import SignalVector, Telemetry
Path(SPILL_DIR).mkdir(parents=True, exist_ok=True)"""),
("md", "### 1. Functional check"),
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
("md", "### 2. Who decides to spill\n\nPMP storage arm: above the GPU-memory watermark `u0`, spill competes with the hot and cold queues through `sigma_S = delta * q_S * mu_S - gamma * p`. Below it, the two-arm decision is unchanged."),
("code", """pmp = PMPController(u0=0.85)
grid_u = np.linspace(0.5, 1.0, 51)
grid_qs = [0, 50, 100, 200]
fig, ax = plt.subplots(figsize=(7, 3))
for qs in grid_qs:
    dec = [pmp.decide_with_storage(hot_depth=4, cold_depth=10, gpu_mem_util=u, spill_depth=qs) for u in grid_u]
    ax.step(grid_u, [{"hot": 2, "cold": 1, "spill": 0}[d.value] for d in dec], where="post", label=f"spill depth {qs}")
ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["spill", "cold", "hot"]); ax.set_xlabel("GPU memory utilization")
ax.set_title("PMP decision, hot depth 4, cold depth 10"); ax.legend(fontsize=7); plt.tight_layout(); plt.show()
eng = PolicyEngine.default_policy()
for ctx in ({"gpu_mem_util": 0.6, "link_util": 0.2}, {"gpu_mem_util": 0.95, "link_util": 0.2}):
    d = eng.decide(SignalVector(size_bytes=8 << 20, role="kv", phase="prefill"), ctx)
    print(ctx, "->", d.route, "(rule:", d.rules["route"] + ")")"""),
("md", "### 3. Coalescing sweep"),
("code", """res = benchmark_coalescing(SPILL_DIR, block_bytes=BLOCK_KB * 1024, coalesce_list=COALESCE, batches=BATCHES,
                           o_direct=O_DIRECT, fsync=FSYNC, block_sizes=[b * 1024 for b in BLOCK_SIZES_KB],
                           meta={"bits": 3, "dim": 128, "seq_len": 256, "heads": 32})
print("O_DIRECT:", res["o_direct"])
for sw in res["sweeps"]:
    print(f"block {sw['single_block_kb']:.0f} KiB")
    for r in sw["coalesce_results"]:
        print(f"  coalesce={r['coalesce']:>3} payload={r['payload_kb']:>9.1f} KiB  write p50={r['write_us']:>9.0f} us "
              f"({r['write_mbps']:>7.1f} MB/s, p99 {r['write_p99_us']:.0f})  read p50={r['read_us']:>9.0f} us ({r['read_mbps']:>7.1f} MB/s)")"""),
("code", """fig, axes = plt.subplots(1, 2, figsize=(10, 3.2))
for sw in res["sweeps"]:
    c = [r["coalesce"] for r in sw["coalesce_results"]]
    axes[0].plot(c, [r["write_mbps"] for r in sw["coalesce_results"]], marker="o", label=f"{sw['single_block_kb']:.0f} KiB")
    axes[1].plot(c, [r["read_mbps"] for r in sw["coalesce_results"]], marker="o", label=f"{sw['single_block_kb']:.0f} KiB")
prev_path = ROOT / "benchmarks" / "results" / "test_arch" / "chimera_storage_spill.json"
if prev_path.exists():
    prev = json.loads(prev_path.read_text())
    pc = [r["coalesce"] for r in prev["coalesce_results"]]
    axes[0].plot(pc, [r["write_mbps"] for r in prev["coalesce_results"]], "k--", marker="x", label="Update 6 chimera (file per write)")
    axes[1].plot(pc, [r["read_mbps"] for r in prev["coalesce_results"]], "k--", marker="x", label="Update 6 chimera (file per write)")
for ax, t_ in zip(axes, ("write (pwrite + fdatasync)", "read (one pread per batch)")):
    ax.set_xscale("log"); ax.set_xlabel("coalesce depth"); ax.set_ylabel("MB/s"); ax.set_title(t_); ax.legend(fontsize=7)
plt.suptitle(f"{HOST} ({MODE})"); plt.tight_layout(); plt.show()"""),
("code", """save("storage_spill", res)"""),
]

if __name__ == "__main__":
    print(build("07_storage_tier.ipynb", "07 · Storage tier: KV spill and retrieve",
                "Coalesced NVMe spill through StorageTier, the PMP storage arm, and the policy rule that triggers spills.",
                PARAMS, CELLS))
