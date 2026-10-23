# Accelerating Mamba-2 with High-Performance Forward Pass Kernels in NVIDIA CUDA Tile

- **Source:** https://developer.nvidia.com/blog/accelerating-mamba-2-with-high-performance-forward-pass-kernels-in-nvidia-cuda-tile/
- **Authors:** Sylvain Gugger, Axel Feldmann, Yinuo Liu, Siddharth Samsi (NVIDIA Technical Blog; Jane Street engineers as early cuTile adopters)
- **Published:** 2026-10-19
- **Retrieved:** 2026-10-22 (added by request, not from the 10-22 bookmark export)
- **Note:** structured summary in my own words, not a verbatim copy. Read the original for the code, figures and per-configuration results.

---

## What it is

CUDA Tile (cuTile) is NVIDIA's Python DSL for writing GPU kernels at tile granularity; the compiler handles thread and warp scheduling and maps tile matmuls onto Tensor Cores. The post walks through a Mamba-2 forward pass written in cuTile.

## Mamba-2 in one paragraph

Mamba-2 keeps a fixed-size matrix hidden state per head (state size by head dimension) instead of a KV cache that grows with the sequence. A naive scan over tokens is memory bound and leaves Tensor Cores idle, so the sequence is cut into chunks and the within-chunk work and the state jumps between chunks are written as matrix multiplies.

## Kernels

- `chunk_cumsum`: per-chunk cumulative sums of the log-space decay, reused by the later kernels.
- `fwd_pass_state`: sequential loop over chunks that produces each chunk's starting state and the final state; tile matmuls on Tensor Cores, parallel over batch, head and state tiles.
- `compute_out`: one fused kernel for the carried-state term, the decayed and causally masked C·Bᵀ term, and the D skip connection; intermediates stay in registers.

Optimizations: latency hints on loads and stores, operand swapping via (AB)ᵀ = BᵀAᵀ so fused operands land in Tensor Memory on Blackwell, a `[batch, head, token]` layout for decay and dt (contiguous, TMA friendly), and per-shape autotuning of block size and occupancy.

## Results as reported

Single B300 (Blackwell Ultra), bf16 inputs with fp32 state, batch 4, 16,384 tokens, 8 heads, state size 128, head size 64, chunk 128. Baseline: the open-source Triton kernels in `mamba_ssm` 2.3.2.post1. Kernel-level forward speedups of 1.14x to 1.82x, growing with sequence length and state size. Forward only; training results depend on backward kernels not covered.

Code: `tilegym.ops.mamba2_chunk_forward` in https://github.com/NVIDIA/TileGym. cuTile: https://github.com/nvidia/cutile-python, https://docs.nvidia.com/cuda/cutile-python/

## Where it plugs into the thesis

- **What moves for SSM layers.** The kernels take an `init_state` and return a `final_state`, and at inference the final state is fed back as the next call's initial state. For disaggregated serving of Mamba-2 or hybrid models (Granite 4), the per-request transfer for SSM layers is this fixed-size state (128 x 64 per head in the benchmark config, fp32), not KV that grows with the prompt. That is the "Mamba state" case in the Update 5-2 per-architecture scuffedQuant work (`benchmarks/test_arch/`), and it changes the hot/cold picture: the state size is constant per layer, so a size-threshold classifier sees the same size at every prompt length.
- **Precision of the moved state.** The kernels keep the state in fp32. Compressing it for the cold path (scuffedQuant) has to be judged against a state that is carried forward and fed back, so error can accumulate across calls, unlike a KV block that is read and not rewritten.
- **Prefill cost on Blackwell.** The forward pass is the prefill path for SSM layers, so faster chunked kernels shrink prefill compute and make the KV/state transfer a larger share of TTFT, which is the share the transport work targets.
