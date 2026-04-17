#!/usr/bin/env python3
"""scuffedQuant benchmark on Mamba recurrent state (mamba-2.8b-hf)."""
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

MODEL = "state-spaces/mamba-2.8b-hf"
PROMPT = "Recurrent state-space models process sequences in linear time."

def extract_states(model, tokenizer, prompt, device):
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model(**inputs, use_cache=True, output_hidden_states=True)
    seq_len = inputs["input_ids"].shape[1]

    cache = getattr(out, "past_key_values", None)
    if cache is not None:
        for attr in ("ssm_states", "recurrent_states", "cache_params"):
            states = getattr(cache, attr, None)
            if states is not None:
                print(f"Found cache.{attr} with {len(states)} layers")
                tensors = [s.float().cpu().numpy().reshape(s.shape[0], -1) for s in states]
                return tensors, seq_len, "recurrent_cache"
        try:
            layers = list(cache)
            if layers:
                t0 = layers[0][0] if isinstance(layers[0], (tuple, list)) else layers[0]
                if hasattr(t0, "shape"):
                    print(f"Using cache layer tensors, {len(layers)} layers")
                    tensors = []
                    for item in layers:
                        t = item[0] if isinstance(item, (tuple, list)) else item
                        tensors.append(t.float().cpu().numpy().reshape(t.shape[0], -1))
                    return tensors, seq_len, "cache_iter"
        except (TypeError, StopIteration):
            pass

    hs = out.hidden_states
    print(f"Falling back to hidden_states ({len(hs)} layers)")
    return [h[0].float().cpu().numpy() for h in hs], seq_len, "hidden_states"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--bits", nargs="+", type=int, default=[8, 4, 3])
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        args.device = "cpu"

    hostname, gpu = detect_node()
    print(f"Node: {hostname}  GPU: {gpu}")

    dtype = torch.bfloat16 if args.device == "cuda" else torch.float32
    print(f"Loading {MODEL} ...")
    try:
        model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=dtype, device_map=args.device)
        tokenizer = AutoTokenizer.from_pretrained(MODEL)
    except Exception as e:
        print(f"Cannot load model: {e}"); sys.exit(1)

    states, seq_len, source = extract_states(model, tokenizer, PROMPT, args.device)
    n_layers = len(states)
    dim = states[0].shape[-1]
    print(f"Extracted {n_layers} layers, dim={dim}, source={source}")

    per_bits_results = []
    for bits in args.bits:
        sq = ScuffedQuant(dim=dim, bits=bits)
        overlaps = []
        for li in range(n_layers):
            S = states[li].reshape(-1, dim) if states[li].ndim >= 2 else states[li].reshape(1, -1)
            if S.shape[0] < 2: continue
            query, comp = S[-1:], sq.compress(S)
            exact = (query @ S.T).squeeze()
            approx = sq.attention_scores(query, comp).squeeze()
            overlaps.append(top_k_overlap(exact, approx, k=8))
            if li % 8 == 0 or li == n_layers - 1:
                print(f"  [{bits}b] L{li:2d}  top-8 overlap {overlaps[-1]:.0%}")

        t0 = time.perf_counter()
        sq.compress(states[0].reshape(-1, dim))
        compress_us = (time.perf_counter() - t0) * 1e6
        ratio = sq.compression_ratio(states[0].reshape(-1, dim).shape[0])
        mean_ov = float(np.mean(overlaps)) if overlaps else 0.0
        print(f"  {bits}b => overlap={mean_ov:.1%}  ratio={ratio:.1f}x")
        per_bits_results.append(PerBits(bits=bits, compression_ratio=ratio,
                                        rank_overlap_topk=mean_ov, compress_us=compress_us))

    result = ArchResult(model=MODEL, architecture="mamba",
                        hostname=hostname, gpu=gpu, seq_len=seq_len,
                        per_bits=[pb.__dict__ for pb in per_bits_results],
                        notes=f"state_source={source}")
    save_json(result.__dict__, "mamba_state")

if __name__ == "__main__":
    main()
