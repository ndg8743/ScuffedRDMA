# Update 5-2: Architectures and Transport

Two versions of Update 5-2 were written on two branches in April and merged into main on 2026-10-22 (`f8aa1c2`). Neither replaces the other, so both are documented here.

| | Canonical (`update5_2.tex`) | Stack draft (`stack-draft/update5_2.tex`) |
|---|---|---|
| Title | Architecture Comparison and RDMA's Role Per Model Family | Architecture-Driven Transport and Stack Comparison |
| Date | tex 2026-04-13; commit `4cc8a1f` 2026-04-15 (branch `update5-2-architectures`) | tex "April 2026"; commits `4bc0a38`, `ad4443e`, `be2dc3f` 2026-04-16/17 (branch `feat/update-5-2`) |
| Harness | `benchmarks/test_arch/` | `benchmarks/test_arch/stack-draft/` |
| Results | `benchmarks/results/test_arch/{cerberus,chimera}_*.json` | `benchmarks/results/test_arch/stack-draft/*.json`, plus three files that landed in the canonical folder: `chimera_mamba_state.json`, `chimera_transformer_granite33.json`, `chimera_storage_spill.json` |
| Unique content | eml analogy, relative position as a transport signal, GPU decompression and torch.compile autotune on 3090 vs 5090, results on both nodes | transport stack table (NCCL, UCX, NVSHMEM, UCCL, ibverbs, NCCL plugin), UCCL comparison plan, NCCL net plugin design, NVMe storage spill results |

Both argue the same thing: which bytes move depends on the model family. A Transformer's KV cache grows with context, an SSM carries a fixed-size state, and MoE turns traffic into an all-to-all expert shuffle, so a single compress-then-RDMA pipeline has to know which case it is in. scuffedQuant's rotation + codebook + QJL math is unchanged; two wrappers (`compress_ssm_state`, `compress_expert_activation`) apply it to SSM state and expert activations.

## Research

Architectures
- FlashAttention-4 (asymmetric pipelining on Blackwell). [TriDao_FlashAttention-4_Kernel_Pipelining_MLSys2026.pdf](../../References/Bookmarks_Collection/TriDao_FlashAttention-4_Kernel_Pipelining_MLSys2026.pdf), [FlashAttention_4_Algorithm_...md](../../References/Bookmarks_RDMA/NVIDIA_CUDA/FlashAttention_4_Algorithm_and_Kernel_Pipelining_Co_Design_for_Asymmetric_Hardwa.md)
- FlashAttention 1-3. [FlashAttention_IO-Aware_2205.14135.pdf](../../References/Bookmarks_Collection/FlashAttention_IO-Aware_2205.14135.pdf), [FlashAttention-2_Faster_Attention_2307.08691.pdf](../../References/Bookmarks_Collection/FlashAttention-2_Faster_Attention_2307.08691.pdf), [TriDao_FlashAttention-3_...2407.08608.pdf](../../References/Bookmarks_Collection/TriDao_FlashAttention-3_Asynchrony_LowPrecision_2407.08608.pdf)
- Mamba-3 (arXiv:2603.15569): fixed-size state. No local copy. Mamba and Mamba-2 (SSD): [TriDao_Mamba_Linear_Time_SSM_2312.00752.pdf](../../References/Bookmarks_Collection/TriDao_Mamba_Linear_Time_SSM_2312.00752.pdf), [TriDao_Transformers_are_SSMs_Mamba2_2405.21060.pdf](../../References/Bookmarks_Collection/TriDao_Transformers_are_SSMs_Mamba2_2405.21060.pdf)
- SonicMoE (arXiv:2512.14080): IO/compute overlap for all-to-all expert traffic. [TriDao_SonicMoE_IO_Tile_MoE_2512.14080.pdf](../../References/Bookmarks_Collection/TriDao_SonicMoE_IO_Tile_MoE_2512.14080.pdf)
- Granite 4 technical report (IBM, 2026): hybrid and MoE models used in the harness. No local copy.
- Odrzywolek, eml universal operator (arXiv:2603.21852): the "one primitive, many parameters" framing. [All_elementary_functions_...2603.21852.pdf](../../References/Bookmarks_RDMA/Papers_Papers/All_elementary_functions_from_a_single_binary_operator_2603.21852.pdf)
- CoPE (arXiv:2602.05258) and D2L's positional encoding chapter: relative position as a transport signal. [CoPE_...2602.05258.pdf](../../References/Bookmarks_RDMA/Papers_Papers/CoPE_Clipped_RoPE_as_A_Scalable_Free_Lunch_for_Long_Context_LLMs_2602.05258.pdf)
- PagedAttention. [PagedAttention_Efficient_LLM_Serving_2309.06180.pdf](../../References/Bookmarks_Collection/PagedAttention_Efficient_LLM_Serving_2309.06180.pdf)
- TurboQuant (arXiv:2504.19874). No local PDF; see [TurboQuant_KV_Cache_FlashBlade.md](../../References/Bookmarks_Collection/TurboQuant_KV_Cache_FlashBlade.md).

Transport stack (stack draft)
- Kraus, Multi-node multi-GPU programming (Magnum IO: NCCL, NVSHMEM, GPUDirect RDMA). [Multi_Node_Multi_GPU_Programming_Kraus_2022.pdf](../../References/Multi_Node_Multi_GPU_Programming_Kraus_2022.pdf)
- UCCL: round-robin multi-QP over ibverbs; the comparison point. `uccl/` submodule.
- NCCL `ncclNet` plugin interface: the integration path. [NCCL_Documentation.md](../../References/Bookmarks_RDMA/thesis_refs/NCCL_Documentation.md)
- libmesh-rdma. https://github.com/autoscriptlabs/libmesh-rdma
- Hsu et al., KV cache reuse with llm-d, LMCache and IBM Storage Scale (8 GB/s comparison point for spill). [Rethinking_LLM_Inference_Economics_...md](../../References/Bookmarks_RDMA/thesis_refs/Rethinking_LLM_Inference_Economics_KV_Cache_Reuse_with_llm_d_LMCache_a.md)

## Work done

Canonical (`4cc8a1f`):
- `middleware/rdma_tensor_cache/scuffed_quant.py`: `compress_ssm_state`, `compress_expert_activation`, `decompress_torch`, `decompress_torch_autotune` (+106 lines).
- `benchmarks/test_arch/`: `common.py`, `bench_transformer.py`, `bench_mamba3.py`, `bench_granite4_hybrid.py`, `bench_granite4_moe.py`, `bench_gpu_decompress.py`, `bench_auto_kernel.py`, `run_all.sh`; `benchmarks/aggregate_results.py` emits the three `.tex` tables in this folder.

Stack draft (`4bc0a38`, `ad4443e`, `be2dc3f`):
- `middleware/nccl_plugin/`: `scuffed_nccl_net.c/.h`, an `ncclNet_v8_t` plugin with two RC QPs per connection, hot below 4 KB (inline, busy-poll), cold otherwise.
- `benchmarks/test_arch/stack-draft/`: its own harness plus `bench_storage_spill.py`, `bench_scuffedrdma_p2p.py`, `bench_uccl_p2p.py`, `run_transport_comparison.sh`.
- Update 6's tex was revised in the same branch (`0eea051`).

Results (canonical, both nodes, `benchmarks/results/test_arch/`, aggregated in `test_arch_comparison.tex`):

| Architecture (model in the JSON) | bits | ratio | top-8 overlap, server 1 / server 2 |
|---|---|---|---|
| transformer (`granite-3.3-2b-instruct`, 4-layer subset) | 3 | 4.00x | 83.59% / 82.42% |
| granite4_hybrid (`granite-4.0-h-micro`) | 3 | 5.64x | 96.25% / 95.94% |
| granite4_moe (`granite-4.0-h-tiny`, expert activations) | 3 | 7.60x | 100.00% / 100.00% |
| "mamba3" (`state-spaces/mamba-130m-hf`) | 3 | 1.39x | 97.40% / 97.40% |

GPU decompression (`*_gpu_decompress.json`, `gpu_decompress_comparison.tex`): 131,072 rows x 128 dim at 3 bits takes 20,763 us on the 5090 and 33,583 us on the 3090 (1.62x). `torch.compile` reduce-overhead and max-autotune do not beat eager on either GPU (`*_auto_kernel.json`, `auto_kernel_comparison.tex`).

Stack-draft storage spill (`benchmarks/results/test_arch/chimera_storage_spill.json`): write 662 MB/s at 1 block, 827 MB/s at 50 blocks; read 1,731 MB/s at 1, 2,188 MB/s at 20, 1,104 MB/s at 50. This is the same data Update 6 reports.

## Next steps as written, status today

Canonical:

| Next step | Status | Evidence |
|---|---|---|
| Run `test_arch/run_all.sh` on server 1 and server 2 | done | Both hosts' JSONs exist; `test_arch_comparison.tex` is filled. |
| Wire `test_arch` into the KV connector with Mamba/MoE branches | open | `middleware/vllm_plugin/` targets Transformer KV first. |
| Long-context (128k) streaming prefill | open | |
| Mamba-3 weights | open | All "mamba3" rows use `mamba-130m-hf`. |

Stack draft:

| Next step | Status | Evidence |
|---|---|---|
| UCCL vs ScuffedRDMA mixed-traffic p99 | open | `bench_uccl_p2p.py` exists; no result. Notebook 01 runs the libscuffedrdma side. |
| Build the NCCL plugin against NCCL 2.25 and test with vLLM over SoftRoCE | partial | Source targets `ncclNet_v8_t` (NCCL 2.23.x per the header). Build is part of notebook 00 in the Oct 2026 pass; not exercised inside NCCL or vLLM. |
| NVSHMEM + OpenMPI on the cluster | open | Needs hardware RoCE or IB; not on SoftRoCE. |
| GPFS access on Hydra for storage-tier runs | open | |
| Fill the Mamba/MoE tables | done | `be2dc3f`. The cross-GPU table in the stack draft is still "Pending"; the canonical version has those numbers. |

## Run it

- [`notebooks/05_scuffedquant.ipynb`](../../notebooks/05_scuffedquant.ipynb): reruns the Granite overlap and reports bit-packed sizes. `benchmarks/test_arch/run_all.sh` remains the per-architecture runner on the GPU nodes.
- [`notebooks/00_environment_check.ipynb`](../../notebooks/00_environment_check.ipynb): builds `middleware/nccl_plugin/`.
- [`notebooks/01_hol_blocking.ipynb`](../../notebooks/01_hol_blocking.ipynb): the mixed-traffic p99 the stack draft names as the key test.
- [`notebooks/07_storage_tier.ipynb`](../../notebooks/07_storage_tier.ipynb): the storage spill sweep, rerun through `middleware/rdma_tensor_cache/storage_tier.py`.
- Tests: `tests/test_scuffed_quant.py`.

## Corrections

- **The "Mamba-3" rows are not Mamba-3.** The canonical harness falls back to `state-spaces/mamba-130m-hf` (a Mamba-1 model) because Mamba-3 weights were gated. Label the rows "Mamba (130M fallback)" in the thesis.
- **Two incompatible Transformer numbers.** Canonical reports rank overlap (top-8 index agreement) with ratios vs FP32: 3-bit is 4.00x, about 83%. The stack draft reports "top-8 cosine similarity" with different ratios: 3-bit is 5.3x, 85.2% (and its Mamba row is `mamba-2.8b-hf`, not 130M). These come from different harnesses and metrics; do not put them in the same table.
- **Recap of Update 4 is wrong twice.** "91.1% ... with a 10x compression ratio vs FP16": Update 4's ratio is 4.0x vs FP32, about 2.0x vs FP16. "Update 4 measured T_RDMA write of about 8 us for small hot-QP transfers": that figure is the single-QP cross-node run, and those completions are not trustworthy (see the Update 4 README). The expected sanity check "hot-QP cross-node latency within 1 us of Update 4's 8 us" inherits the same problem.
- **Decompression prose vs table.** The text says the 4k-row speedup "widens to 1.8-2.0x"; `gpu_decompress_comparison.tex` shows 3.20x (3-bit), 3.70x (4-bit) and 1.64x (8-bit) at 4,096 rows.
- **"PolarQuant (Walsh-Hadamard + per-coordinate codebook)".** That stage is TurboQuant's rotation plus Lloyd-Max quantization; PolarQuant (arXiv:2502.02617) is a different, polar-coordinate method. The QJL residual is a 256-bit sign sketch per vector in Update 4's runs.
- **NCCL plugin description (stack draft).** The text describes `ncclNet_v9` and a PMP background thread that moves the threshold. The code implements `ncclNet_v8_t` with a fixed 4 KB size split and no controller thread.
- **Storage spill block size (stack draft).** The "1.5 MB compressed block" (1,568 KB in the JSON) is 8,192 rows x 128 dims serialized with `uint8` indices and one byte per QJL sign (default `qjl_dim` 64) and omits residual norms, so it is only about 1.3x smaller than the 2 MB FP16 block it represents. The "6.4x compression" quoted next to it does not match the bytes written. The benchmark writes to `tempfile.TemporaryDirectory()`, so whether it hit NVMe or tmpfs depends on server 2's `/tmp`, which is not recorded.
- **OS versions disagree.** The stack draft says Ubuntu 22.04, CUDA 12.8, rdma-core 55; Update 4's infrastructure table says Ubuntu 24.04, CUDA 12.4, pyverbs 50.0 on server 2. Notebook 00 now records versions per run.
- Both versions call the six UCX PRs "upstream UCX patches"; none were merged (see the Update 5 README).
