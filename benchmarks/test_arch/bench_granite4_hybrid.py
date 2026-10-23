#!/usr/bin/env python3
"""
Granite 4 hybrid: attention + SSM blocks in one model.

Granite 4.0-h-small interleaves transformer attention layers with SSM
(Mamba-style) layers. For scuffedQuant we want both:

  - attention blocks contribute KV tensors (same path as bench_transformer)
  - SSM blocks contribute hidden states   (same path as bench_mamba3)

We run one prefill and record compression for each block type
separately so the update can show which blocks benefit from which
quantizer. The MoE-specific routing is exercised by bench_granite4_moe.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    PerBitsResult, Result, detect_node, save_json, timed_us, top_k_overlap,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="ibm-granite/granite-4.0-h-micro",
                   help="Hybrid variants: h-micro, h-tiny, h-1b, h-small (largest, MoE).")
    p.add_argument("--device", default="auto", choices=["cuda", "cpu", "auto"])
    p.add_argument("--bits", nargs="+", type=int, default=[8, 4, 3])
    p.add_argument("--qjl-dim", type=int, default=256)
    args = p.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant

    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    # Shard across all visible GPUs for large hybrid/MoE models.
    device_map = "auto" if device == "cuda" else device

    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype, device_map=device_map)
    tok = AutoTokenizer.from_pretrained(args.model)

    # Keep the prompt short: Granite 4's SSM selective-scan builds an
    # intermediate (b, c, l, s, h, n) tensor that scales superlinearly with
    # prefill length and OOMs a 24 GB GPU past ~20 tokens.
    prompt = "Hybrid state-space plus attention mixes small KV with O(1) SSM state."
    # With device_map="auto" input tensors need to go to the embed layer's device.
    target = next(model.parameters()).device if device == "cuda" else device
    inputs = tok(prompt, return_tensors="pt").to(target)
    seq_len = int(inputs["input_ids"].shape[1])

    with torch.no_grad():
        outputs = model(**inputs, use_cache=True)

    # Granite 4 hybrid interleaves standard attention layers with SSM layers.
    # transformers puts both in outputs.past_key_values.layers: attention
    # layers expose .keys/.values; SSM layers are LinearAttentionLayer
    # instances with .recurrent_states / .conv_states.
    kv = getattr(outputs, "past_key_values", None)
    attn_keys: list = []
    ssm_recurrent: list = []
    if kv is not None:
        for layer in kv.layers:
            if hasattr(layer, "keys") and getattr(layer, "keys", None) is not None:
                attn_keys.append(layer.keys[0].float().cpu().numpy())
            elif hasattr(layer, "recurrent_states") and getattr(layer, "recurrent_states", None) is not None:
                ssm_recurrent.append(layer.recurrent_states[0].float().cpu().numpy())
    # Fallback for older HF versions that exposed a separate cache_params.
    cache = getattr(outputs, "cache_params", None)
    if not ssm_recurrent and cache is not None and hasattr(cache, "ssm_states"):
        ssm_recurrent = [v[0].float().cpu().numpy() for v in cache.ssm_states.values()]

    host, gpu = detect_node()

    # We record a single Result with per-bits rows, and use notes to flag
    # that both attention and SSM blocks were scored jointly.
    cfg = model.config
    head_dim = cfg.hidden_size // cfg.num_attention_heads

    attn_layers, ssm_layers = attn_keys, ssm_recurrent

    result = Result(
        model=args.model,
        architecture="granite4_hybrid",
        hostname=host,
        gpu=gpu,
        seq_len=seq_len,
        state_shape=[len(attn_layers), len(ssm_layers), head_dim],
        notes="attention + SSM blocks compressed together; per-bits row aggregates both.",
    )

    for bits in args.bits:
        sq_attn = ScuffedQuant(dim=head_dim, bits=bits, qjl_dim=args.qjl_dim)
        overlaps, ratios = [], []
        compress_us, decompress_us = 0.0, 0.0
        n_blocks = 0

        for K in attn_layers:
            K_flat = K.reshape(-1, head_dim)
            c, cus = timed_us(sq_attn.compress, K_flat)
            compress_us += cus
            _, dus = timed_us(sq_attn.decompress, c)
            decompress_us += dus
            query = K[0][-1:, :]
            exact = (query @ K[0].T).squeeze()
            approx = sq_attn.attention_scores(query, sq_attn.compress(K[0])).squeeze()
            overlaps.append(top_k_overlap(exact, approx, k=8))
            ratios.append(sq_attn.compression_ratio(K_flat.shape[0]))
            n_blocks += 1

        for state in ssm_layers:
            # recurrent_states shape varies: accept any (..., d_state) layout
            # and flatten the leading axes ourselves.
            d_state = state.shape[-1]
            sq_ssm = ScuffedQuant(dim=d_state, bits=bits, qjl_dim=args.qjl_dim)
            flat = state.reshape(-1, d_state).astype(np.float32)
            if flat.shape[0] == 0:
                continue
            c, cus = timed_us(sq_ssm.compress_ssm_state, flat[None, ...])
            compress_us += cus
            _, dus = timed_us(sq_ssm.decompress, c)
            decompress_us += dus
            query = flat[-1:, :]
            exact = (query @ flat.T).squeeze()
            approx = sq_ssm.attention_scores(query, sq_ssm.compress(flat)).squeeze()
            overlaps.append(top_k_overlap(exact, approx, k=8))
            ratios.append(sq_ssm.compression_ratio(flat.shape[0]))
            n_blocks += 1

        n_blocks = max(n_blocks, 1)
        result.per_bits.append(PerBitsResult(
            bits=bits,
            compression_ratio=float(np.mean(ratios)) if ratios else 0.0,
            rank_overlap_topk=float(np.mean(overlaps)) if overlaps else 0.0,
            decompress_us=decompress_us / n_blocks,
            compress_us=compress_us / n_blocks,
        ))

    out = save_json(result, "granite4_hybrid")
    print(f"[bench_granite4_hybrid] wrote {out}")


if __name__ == "__main__":
    main()
