#!/usr/bin/env python3
"""scuffedQuant benchmark on Granite 4 MoE expert outputs."""
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
PROMPT = "Mixture-of-experts routes tokens to specialized sub-networks."

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

def find_moe_layers(model):
    moe_modules = []
    for name, mod in model.named_modules():
        for attr in ("block_sparse_moe", "moe", "sparse_moe", "experts"):
            if hasattr(mod, attr) or attr in name.lower():
                moe_modules.append((name, mod))
                break
    return moe_modules

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

    moe_layers = find_moe_layers(model)
    captured, hooks = {}, []
    use_moe = len(moe_layers) > 0

    if use_moe:
        print(f"Found {len(moe_layers)} MoE layers, registering hooks")
        for name, mod in moe_layers:
            def make_hook(n):
                def hook_fn(module, inp, out):
                    t = out[0] if isinstance(out, (tuple, list)) else out
                    captured[n] = t.detach().float().cpu().numpy()
                return hook_fn
            hooks.append(mod.register_forward_hook(make_hook(name)))
    else:
        print("No MoE layers found, will use hidden_states")

    inputs = tokenizer(PROMPT, return_tensors="pt").to(args.device)
    with torch.no_grad():
        out = model(**inputs, output_hidden_states=True)
    seq_len = inputs["input_ids"].shape[1]
    for h in hooks: h.remove()

    if use_moe and captured:
        print(f"Captured {len(captured)} MoE outputs")
        tensors = [(k, v.reshape(-1, v.shape[-1])) for k, v in captured.items()]
        source = "moe_hook"
    else:
        if use_moe: print("Hooks captured nothing, falling back to hidden_states")
        hs = out.hidden_states
        tensors = [(f"layer_{i}", h[0].float().cpu().numpy()) for i, h in enumerate(hs)]
        source = "hidden_states"

    dim = tensors[0][1].shape[-1]
    print(f"Benchmarking {len(tensors)} layers, dim={dim}, source={source}")

    per_bits_results = []
    for bits in args.bits:
        sq = ScuffedQuant(dim=dim, bits=bits)
        overlaps = []
        for name, mat in tensors:
            if mat.shape[0] < 2: continue
            query, comp = mat[-1:], sq.compress(mat)
            exact = (query @ mat.T).squeeze()
            approx = sq.attention_scores(query, comp).squeeze()
            ov = top_k_overlap(exact, approx, k=8)
            overlaps.append(ov)
            print(f"  [{bits}b] {name}  top-8 overlap {ov:.0%}")
        t0 = time.perf_counter()
        sq.compress(tensors[0][1])
        compress_us = (time.perf_counter() - t0) * 1e6
        mean_ov = float(np.mean(overlaps)) if overlaps else 0.0
        ratio = sq.compression_ratio(tensors[0][1].shape[0])
        print(f"  {bits}b => overlap={mean_ov:.1%}  ratio={ratio:.1f}x")
        per_bits_results.append(PerBits(bits=bits, compression_ratio=ratio,
                                        rank_overlap_topk=mean_ov, compress_us=compress_us))

    result = ArchResult(model=model_name, architecture="moe",
                        hostname=hostname, gpu=gpu, seq_len=seq_len,
                        per_bits=[pb.__dict__ for pb in per_bits_results],
                        notes=f"source={source}")
    save_json(result.__dict__, "granite4_moe")

if __name__ == "__main__":
    main()
