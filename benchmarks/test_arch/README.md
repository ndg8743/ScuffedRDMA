# test_arch

Per-architecture scuffedQuant benchmarks used by Update 5-2. Each script loads one model family, extracts its architecture-specific state, runs the `ScuffedQuant` pipeline (from `middleware/rdma_tensor_cache/scuffed_quant.py`) at several bit widths, and writes one JSON per `(hostname, model)` into `../results/test_arch/`.

The aggregator in `../aggregate_results.py` picks up those JSONs and emits `../results/test_arch_comparison.tex` with Chimera and Cerberus columns side by side.

## Scripts

| Script | Architecture | State tensor |
|---|---|---|
| `bench_transformer.py` | Transformer | `outputs.past_key_values` → per-layer K flattened to `(heads*seq, head_dim)` |
| `bench_mamba3.py` | Mamba-3 (fallback Mamba-2) | `cache_params.ssm_states` per layer, shape `(d_model, d_state)` |
| `bench_granite4_hybrid.py` | Granite 4 hybrid (attention + SSM) | both KV and SSM blocks in the same forward pass |
| `bench_granite4_moe.py` | Granite 4 MoE | expert-output activation captured pre-all-to-all |

## Output schema

Each JSON matches the `Result` dataclass in `common.py`:

```json
{
  "model": "...",
  "architecture": "transformer|mamba3|granite4_hybrid|granite4_moe",
  "hostname": "chimera|cerberus|...",
  "gpu": "3090|5090|cpu|...",
  "seq_len": 42,
  "state_shape": [...],
  "per_bits": [
    {"bits": 8, "compression_ratio": ..., "rank_overlap_topk": ..., "compress_us": ..., "decompress_us": ...},
    ...
  ],
  "notes": "..."
}
```

## Running cross-node

Each script is independent. Run them on each node and the hostname tag keeps the outputs separate.

```bash
# On Chimera (3x 3090):
cd benchmarks/test_arch && bash run_all.sh

# On Cerberus (2x 5090):
cd benchmarks/test_arch && bash run_all.sh
```

Then from a control host that has both results directories synced:

```bash
python benchmarks/aggregate_results.py --results-dir benchmarks/results/test_arch
# emits benchmarks/results/test_arch_comparison.tex
```

## Notes on model availability

- `state-spaces/mamba-3-1b` is gated on HuggingFace at the time of writing. `bench_mamba3.py` falls back to `state-spaces/mamba2-2.7b` and tags the result with `notes="mamba-3 unavailable..."` so the Update 5-2 reader knows what was actually measured.
- `bench_granite4_moe.py` tries a forward hook on the first module whose class name contains `moe` or `experts`. If none is found (older HF versions), it synthesises a routed-activation tensor of the expected `(n_experts, tokens, d_model)` shape so the compression pipeline still runs end-to-end.
