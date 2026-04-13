# rdma_tensor_cache

The main libscuffedrdma code. Precision-aware tensor caching and transfer
over RDMA, with a dual QP pool routed by an optimal-control policy.

## Main modules

- `dual_qp_pool.py` — separate hot (busy-poll, low latency) and cold
  (sleep-poll, high throughput) RC QP pools over a shared PD. Hot and
  cold transfers stop blocking each other on the same QP. Addresses UCX
  issues #11004, #11034, #1319.
- `wfa_classifier.py` — Work-First Adaptive classifier. Decides whether
  a given transfer goes on the hot or cold pool using size thresholds
  plus a phase detector that distinguishes prefill from decode. Makes
  UCX's implicit eager/RNDV/zcopy cliffs (#10552, #10486, #10532) explicit
  and logged.
- `pmp_controller.py` — Pontryagin's Maximum Principle bang-bang
  controller. Given hot and cold queue depths plus service rates, the
  switching function `S = λ_qH C μ_H - λ_qC C μ_C` decides the next
  transfer's pool. Overrides the WFA classifier when one pool is
  congested.
- `scuffed_quant.py` — two-stage KV cache compression. Stage 1 is
  PolarQuant (Walsh-Hadamard rotation then per-coordinate codebook
  quantization, no calibration). Stage 2 is QJL (1-bit signs of a random
  projection of the residual). Individual vectors are lossy but
  attention scores stay accurate. Based on Zandieh et al., TurboQuant,
  arXiv:2504.19874.

## Supporting modules

- `precision.py` — `PrecisionFormat` enum (FP32/FP16/BF16/INT8/MXFP4),
  device profiles (V100, RTX 5070 Ti), and stochastic rounding to keep
  gradient estimates unbiased across precision boundaries.
- `quantization.py` — `AdaptiveQuantizer` picks the most aggressive
  quantization that stays within a fidelity bound, based on current link
  bandwidth and latency targets.
- `prefetch.py` — ring-buffer history plus stride and layer-sweep
  detection. Predicts the next fetch so RDMA latency hides behind
  compute.
- `cache.py` — `RdmaTensorCache`. Wraps a transport, a
  `PrecisionManager`, an `AdaptiveQuantizer`, and a `PrefetchEngine` into
  the cache API that callers actually use.
- `sae_steering.py` — sparse-autoencoder feature storage with a wire
  format for sparse vectors. Clamps features on top of a model to steer
  behavior without fine-tuning. Bounded-nnz and bounded-dim checks
  protect `from_bytes()` from crafted peers.
- `vllm_connector.py` — `RDMAKVCacheConnector` for disaggregated
  prefill/decode. Follows the MooncakeConnector / NixlConnector pattern.
  Includes a standalone `TensorClassifier` (WFA-based heat classifier).

## Transport backends

- `transport_rdma.py` — real pyverbs/rdma-core transport. Registers MRs,
  posts RDMA Writes and Receives. Linux-only, degrades gracefully when
  pyverbs is missing.
- `transport_tcp_sim.py` — asyncio-TCP simulation exposing the same
  API. Cross-platform, used for development without RDMA hardware.

## Stale

None obvious. The older `TensorClassifier` in `vllm_connector.py`
overlaps with `wfa_classifier.py` but serves a different caller
(disaggregated prefill/decode vs dual QP pool routing).
