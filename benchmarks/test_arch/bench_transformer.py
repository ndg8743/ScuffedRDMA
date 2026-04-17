#!/usr/bin/env python3
"""scuffedQuant benchmark on a standard transformer (Granite 3.3-2B)."""
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
    print(f"Missing dependency: {e}")
    sys.exit(1)

MODEL = "ibm-granite/granite-3.3-2b-instruct"
PROMPT = (
    "The key-value cache in transformer inference trades memory for "
    "computation. Without it, each decode step would recompute attention "
    "over the entire sequence, which is quadratic in sequence length."
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--bits", nargs="+", type=int, default=[8, 4, 3])
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA unavailable, falling back to CPU")
        args.device = "cpu"

    hostname, gpu = detect_node()
    print(f"Node: {hostname}  GPU: {gpu}")

    dtype = torch.bfloat16 if args.device == "cuda" else torch.float32
    print(f"Loading {MODEL} ...")
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=dtype, device_map=args.device)
    tokenizer = AutoTokenizer.from_pretrained(MODEL)

    cfg = model.config
    n_layers = cfg.num_hidden_layers
    n_kv_heads = getattr(cfg, "num_key_value_heads", cfg.num_attention_heads)
    head_dim = cfg.hidden_size // cfg.num_attention_heads

    inputs = tokenizer(PROMPT, return_tensors="pt").to(args.device)
    with torch.no_grad():
        out = model(**inputs, use_cache=True)
    cache = out.past_key_values
    seq_len = inputs["input_ids"].shape[1]
    print(f"Prefilled {seq_len} tokens, {n_layers} layers, {n_kv_heads} KV heads, head_dim={head_dim}")

    per_bits_results = []
    for bits in args.bits:
        sq = ScuffedQuant(dim=head_dim, bits=bits)
        overlaps = []

        for li in range(n_layers):
            K = cache.layers[li].keys[0].float().cpu().numpy()  # (n_kv_heads, seq_len, head_dim)
            for h in range(n_kv_heads):
                keys_h = K[h]
                query = keys_h[-1:]
                K_comp = sq.compress(keys_h)

                exact = (query @ keys_h.T).squeeze()
                approx = sq.attention_scores(query, K_comp).squeeze()
                overlaps.append(top_k_overlap(exact, approx, k=8))

            if li % 8 == 0 or li == n_layers - 1:
                mean_so_far = np.mean(overlaps[-n_kv_heads:])
                print(f"  [{bits}b] L{li:2d}  top-8 overlap {mean_so_far:.0%}")

        t0 = time.perf_counter()
        dummy = sq.compress(K[0])
        compress_us = (time.perf_counter() - t0) * 1e6

        ratio = sq.compression_ratio(seq_len)
        mean_overlap = float(np.mean(overlaps))
        print(f"  {bits}b => overlap={mean_overlap:.1%}  ratio={ratio:.1f}x  compress={compress_us:.0f}us")

        per_bits_results.append(PerBits(bits=bits, compression_ratio=ratio,
                                        rank_overlap_topk=mean_overlap,
                                        compress_us=compress_us))

    result = ArchResult(model=MODEL, architecture="transformer",
                        hostname=hostname, gpu=gpu, seq_len=seq_len,
                        per_bits=[pb.__dict__ for pb in per_bits_results])
    save_json(result.__dict__, "transformer_granite33")


if __name__ == "__main__":
    main()
