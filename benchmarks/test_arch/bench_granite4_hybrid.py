#!/usr/bin/env python3
"""scuffedQuant benchmark on Granite 4 hybrid (attention + SSM layers)."""
import sys, time, argparse
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common import detect_node, save_json, top_k_overlap, ArchResult, PerBits

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant
except ImportError as e:
    print(f"Missing dependency: {e}"); sys.exit(1)

CANDIDATES = ["ibm-granite/granite-4.0-tiny-preview", "ibm-granite/granite-4.0-h-small"]
PROMPT = "Hybrid models interleave attention and SSM layers for efficiency."

def load_model(device):
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    for name in CANDIDATES:
        try:
            print(f"Trying {name} ...")
            m = AutoModelForCausalLM.from_pretrained(name, dtype=dtype,
                                                     device_map=device, trust_remote_code=True)
            t = AutoTokenizer.from_pretrained(name, trust_remote_code=True)
            return m, t, name
        except Exception as e:
            print(f"  Failed: {e}")
    print("No Granite 4 model available"); sys.exit(1)

def classify_layers(cache):
    attn_kv, ssm_states = [], []
    if hasattr(cache, "layers"):
        for i, layer in enumerate(cache.layers):
            if hasattr(layer, "keys") and layer.keys is not None:
                attn_kv.append((i, layer.keys[0].float().cpu().numpy()))
            elif hasattr(layer, "ssm_state"):
                ssm_states.append((i, layer.ssm_state.float().cpu().numpy()))
    for attr in ("ssm_states", "recurrent_states"):
        ss = getattr(cache, attr, None)
        if ss is not None:
            for j, s in enumerate(ss):
                ssm_states.append((j, s.float().cpu().numpy()))
            break
    return attn_kv, ssm_states

def bench_tensors(tensors, label, bits_list):
    if not tensors:
        print(f"  No {label} layers found"); return []
    dim = tensors[0][1].reshape(tensors[0][1].shape[0], -1).shape[-1]
    results = []
    for bits in bits_list:
        sq = ScuffedQuant(dim=dim, bits=bits)
        overlaps = []
        for li, mat in tensors:
            flat = mat.reshape(-1, dim)
            if flat.shape[0] < 2: continue
            query, comp = flat[-1:], sq.compress(flat)
            exact = (query @ flat.T).squeeze()
            approx = sq.attention_scores(query, comp).squeeze()
            ov = top_k_overlap(exact, approx, k=8)
            overlaps.append(ov)
            print(f"  [{label} {bits}b] L{li:2d}  top-8 overlap {ov:.0%}")
        t0 = time.perf_counter()
        sq.compress(tensors[0][1].reshape(-1, dim))
        compress_us = (time.perf_counter() - t0) * 1e6
        mean_ov = float(np.mean(overlaps)) if overlaps else 0.0
        ratio = sq.compression_ratio(tensors[0][1].reshape(-1, dim).shape[0])
        print(f"  {label} {bits}b => overlap={mean_ov:.1%}  ratio={ratio:.1f}x")
        results.append(PerBits(bits=bits, compression_ratio=ratio,
                               rank_overlap_topk=mean_ov, compress_us=compress_us))
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--bits", nargs="+", type=int, default=[8, 4, 3])
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    hostname, gpu = detect_node()
    print(f"Node: {hostname}  GPU: {gpu}")
    model, tokenizer, model_name = load_model(args.device)

    inputs = tokenizer(PROMPT, return_tensors="pt").to(args.device)
    with torch.no_grad():
        out = model(**inputs, use_cache=True)
    cache = out.past_key_values
    seq_len = inputs["input_ids"].shape[1]
    attn_kv, ssm_states = classify_layers(cache)
    print(f"Prefilled {seq_len} tokens: {len(attn_kv)} attn, {len(ssm_states)} SSM layers")

    attn_res = bench_tensors(attn_kv, "attn", args.bits)
    ssm_res = bench_tensors(ssm_states, "ssm", args.bits)

    notes_parts = []
    for bits in args.bits:
        a = [r for r in attn_res if r.bits == bits]
        s = [r for r in ssm_res if r.bits == bits]
        if a and s:
            winner = "attn" if a[0].rank_overlap_topk >= s[0].rank_overlap_topk else "ssm"
            notes_parts.append(f"{bits}b: {winner} compresses better")
    notes = "; ".join(notes_parts)
    if notes: print(f"Notes: {notes}")

    combined = [pb.__dict__ for pb in attn_res + ssm_res]
    result = ArchResult(model=model_name, architecture="hybrid",
                        hostname=hostname, gpu=gpu, seq_len=seq_len,
                        per_bits=combined, notes=notes)
    save_json(result.__dict__, "granite4_hybrid")

if __name__ == "__main__":
    main()
