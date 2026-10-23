"""Build notebooks/05_scuffedquant.ipynb."""
from nbtools import build

PARAMS = '''MODE = "local"            # "local" | "cluster"
RESULTS_SUBDIR = "scuffedquant"
MODEL = "ibm-granite/granite-3.3-2b-instruct"
DEVICE = "cuda"            # cluster: cuda on Chimera / Cerberus
BITS = 3
QJL_DIM = 256
TOPK = 8
SEED = 0'''

CELLS = [
("md", """## What this notebook checks

scuffedQuant after the wire-format fix: indices bit-packed at `bits` bits per coordinate, the QJL residual sketch at one bit per projection, two fp32 norms, a 20-byte header. `CompressedKV.nbytes == len(pack())`.

1. Packed size per vector and compression ratios for head_dim 64 / 128, bits 2 / 3 / 4, qjl_dim 64 / 256, computed from real `pack()` output.
2. Pack / unpack round trip.
3. Top-8 attention overlap per layer, reported as mean ± std and min. Local mode uses synthetic KV (Gaussian with a few large-magnitude channels, a rough stand-in for real keys). Cluster mode loads the model and repeats the Update 4 measurement on its real KV cache.

Ratios against FP32 are twice the ratios against FP16. Granite 3.3-2B has head_dim 64, so 3-bit with a 256-bit sketch is 64 bytes per vector: 4.0x vs FP32, 2.0x vs FP16 (header excluded)."""),
("code", """import numpy as np
import matplotlib.pyplot as plt
from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant, CompressedKV"""),
("md", "### 1. Packed sizes"),
("code", """rows = []
rng = np.random.default_rng(SEED)
N = 1024
for d in (64, 128):
    x = rng.standard_normal((N, d)).astype(np.float32)
    for bits in (2, 3, 4):
        for qjl in (64, 256):
            sq = ScuffedQuant(dim=d, bits=bits, qjl_dim=qjl, seed=42)
            c = sq.compress(x)
            wire = c.pack()
            assert len(wire) == c.nbytes
            per_vec = (len(wire) - 20) / N
            rows.append({"head_dim": d, "bits": bits, "qjl_dim": qjl, "bytes_per_vector": per_vec,
                         "ratio_vs_fp16": d * 2 / per_vec, "ratio_vs_fp32": d * 4 / per_vec,
                         "unpacked_bytes_per_vector": (c.unpacked_nbytes) / N})
print(f"{'dim':>4} {'bits':>4} {'qjl':>4} {'B/vec':>7} {'vs fp16':>8} {'vs fp32':>8} {'unpacked B/vec':>15}")
for r in rows:
    print(f"{r['head_dim']:>4} {r['bits']:>4} {r['qjl_dim']:>4} {r['bytes_per_vector']:>7.1f} "
          f"{r['ratio_vs_fp16']:>8.2f} {r['ratio_vs_fp32']:>8.2f} {r['unpacked_bytes_per_vector']:>15.1f}")"""),
("md", "### 2. Round trip"),
("code", """sq = ScuffedQuant(dim=64, bits=BITS, qjl_dim=QJL_DIM, seed=42)
x = rng.standard_normal((257, 64)).astype(np.float32)
c = sq.compress(x)
c2 = CompressedKV.unpack(c.pack())
q = rng.standard_normal((4, 64)).astype(np.float32)
ok = (np.array_equal(c.indices, c2.indices) and np.array_equal(c.qjl_signs, c2.qjl_signs)
      and np.array_equal(sq.attention_scores(q, c), sq.attention_scores(q, c2)))
print("round trip exact:", ok, "| wire bytes:", len(c.pack()), "| unpacked bytes:", c.unpacked_nbytes)
assert ok"""),
("md", "### 3. Top-8 attention overlap per layer"),
("code", """def topk_overlap_per_layer(layers, sq, topk=TOPK):
    out = []
    for K in layers:                      # K: (heads, seq, head_dim)
        ov, e_q, e_n = [], [], []
        for h in range(K.shape[0]):
            keys = K[h]
            query = keys[-1:, :]
            comp = sq.compress(keys)
            exact = (query @ keys.T).squeeze()
            with_qjl = sq.attention_scores(query, comp).squeeze()
            naive = (query @ sq.decompress(comp).T).squeeze()
            k = min(topk, keys.shape[0])
            ov.append(len(set(np.argsort(-exact)[:k]) & set(np.argsort(-with_qjl)[:k])) / k)
            e_q.append(np.abs(exact - with_qjl).mean()); e_n.append(np.abs(exact - naive).mean())
        out.append({"topk_overlap": float(np.mean(ov)), "abs_err_qjl": float(np.mean(e_q)), "abs_err_naive": float(np.mean(e_n))})
    return out

def summarize(per_layer):
    v = np.array([l["topk_overlap"] for l in per_layer])
    return {"layers": len(v), "mean": float(v.mean()), "std": float(v.std(ddof=1)) if len(v) > 1 else 0.0,
            "min": float(v.min()), "max": float(v.max()),
            "qjl_helps": bool(np.mean([l["abs_err_qjl"] for l in per_layer]) < np.mean([l["abs_err_naive"] for l in per_layer]))}

source = "synthetic"
layers = None
if MODE == "cluster":
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        dev = DEVICE if (DEVICE == "cpu" or torch.cuda.is_available()) else "cpu"
        tok = AutoTokenizer.from_pretrained(MODEL)
        lm = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16 if dev == "cuda" else torch.float32, device_map=dev)
        prompt = ("The key-value cache in transformer inference trades memory for computation. Without it, each decode "
                  "step would recompute attention over the entire sequence, which is quadratic in sequence length. "
                  "With the cache, decode is linear: each new token only computes its own key and value projections.")
        with torch.no_grad():
            out = lm(**tok(prompt, return_tensors="pt").to(dev), use_cache=True)
        layers = [layer.keys[0].float().cpu().numpy() for layer in out.past_key_values.layers]
        source = MODEL
        del lm
    except Exception as e:
        print("model load failed, falling back to synthetic KV:", repr(e))
if layers is None:
    L, H, S, D = (8, 8, 128, 64) if MODE == "local" else (40, 8, 512, 64)
    layers = []
    for l in range(L):
        K = rng.standard_normal((H, S, D)).astype(np.float32)
        K[..., rng.choice(D, 3, replace=False)] *= 8.0      # a few outlier channels
        layers.append(K)
head_dim = layers[0].shape[-1]
sq = ScuffedQuant(dim=head_dim, bits=BITS, qjl_dim=QJL_DIM, seed=42)
per_layer = topk_overlap_per_layer(layers, sq)
summary = summarize(per_layer)
print("source:", source)
print(f"top-{TOPK} overlap: {summary['mean']*100:.1f}% ± {summary['std']*100:.1f}% over {summary['layers']} layers "
      f"(min {summary['min']*100:.1f}%), QJL lowers abs error: {summary['qjl_helps']}")
plt.figure(figsize=(7, 3))
plt.plot([l["topk_overlap"] for l in per_layer], marker="o", ms=3)
plt.axhline(summary["mean"], ls="--", lw=1)
plt.ylim(0, 1.02); plt.xlabel("layer"); plt.ylabel(f"top-{TOPK} overlap"); plt.title(f"scuffedQuant {BITS}-bit + {QJL_DIM}-bit QJL ({source})")
plt.tight_layout(); plt.show()"""),
("md", "### Earlier Update 4 run, re-summarized\n\n`benchmarks/results/scuffed_quant_llm.json` (Granite 3.3-2B, 3-bit, qjl_dim 256), reported as mean ± std per layer."),
("code", """prev_path = ROOT / "benchmarks" / "results" / "scuffed_quant_llm.json"
prev = None
if prev_path.exists():
    prev = json.loads(prev_path.read_text())
    ps = summarize(prev["layers"])
    print(f"{prev['model']}: top-8 {ps['mean']*100:.1f}% ± {ps['std']*100:.1f}% (min {ps['min']*100:.1f}%, {ps['layers']} layers), "
          f"bits={prev['bits']} qjl_dim={prev['qjl_dim']} head_dim={prev['head_dim']}")
    hd = prev["head_dim"]
    per_vec = (hd * prev["bits"] + prev["qjl_dim"]) / 8 + 8
    print(f"packed bytes/vector {per_vec:.0f}: {hd*4/per_vec:.2f}x vs FP32, {hd*2/per_vec:.2f}x vs FP16")
    print("note: that file's kv_compressed_bytes divides FP16 bytes by the FP32 ratio, so it is 2x too small.")
else:
    print("no earlier result file")"""),
("code", """save("scuffedquant", {
    "bits": BITS, "qjl_dim": QJL_DIM, "topk": TOPK, "kv_source": source,
    "packed_sizes": rows, "per_layer": per_layer, "summary": summary,
})"""),
]

if __name__ == "__main__":
    print(build("05_scuffedquant.ipynb", "05 · scuffedQuant wire format and accuracy",
                "Bit-packed wire size, round trip, and top-8 attention overlap per layer (mean ± std).",
                PARAMS, CELLS))
