# ScuffedRDMA

Adaptive RDMA middleware for disaggregated LLM inference over commodity Ethernet.

![ScuffedRDMA overview: every transfer is measured, classified, routed by policy and placed on the hot, cold or spill queue](docs/media/00_overview.gif)

MS Computer Science thesis, SUNY New Paltz. Author: Nathan Gopee. Advisors: Dr. Wafi Danesh, Dr. Ashley Suchy.

---

## Problem

Disaggregated prefill/decode serving moves the KV cache across nodes: prefill writes it once in bulk, decode needs small, latency-critical pieces of it every step. On commodity 10GbE, one RDMA queue pair carries both, so a few-hundred-byte decode transfer waits behind multi-megabyte prefill blocks (head-of-line blocking). libscuffedrdma splits traffic into a hot and a cold class, each on its own queue pair or endpoint with its own completion handling, and decides per transfer which class it belongs to.

## The thesis, section by section

Each part as a short animation, then what it shows and the algorithm behind it. The animations are made with [Manim Community](https://github.com/ManimCommunity/manim); the source is in [`docs/animations/`](docs/animations/) and `bash docs/animations/render.sh` rebuilds every GIF. Numbers in them are either arithmetic (sizes, line rate) or come from a results file in this repo. The ones marked illustrative are not measurements.

**Color key:** orange = hot (latency-critical), blue = cold (bulk), violet = storage spill, green = decision or check passed, red = stall or failure.

### 1. What moves: network and storage

![KV traffic between prefill and decode, and spill to NVMe](docs/media/01_traffic.gif)

Prefill on Cerberus reads the whole prompt once and writes K and V for every layer. For Granite 3.3-2B (40 layers, 8 KV heads, head_dim 64, bf16) that is 2 × 8 × 64 × 2 B = **2 KiB per token per layer**. A 2,048-token prompt is therefore 4 MiB per layer and 160 MiB per request, about 134 ms of serialization on a 10 Gb/s wire before any protocol overhead.

While that streams, other requests need small messages on the same link: the connector's `__done__` control blob, flow-control credits, scheduler metadata, token ids. Those are 32 B to a few hundred KiB and sit on the decode critical path.

On the decode side the paged KV cache fills GPU memory. Past a watermark, cold blocks are written to local NVMe (Update 6) instead of being dropped and recomputed, and the GPFS tier on Hydra is the next level down.

### 2. Head-of-line blocking

![One queue pair vs the dual pool](docs/media/02_headofline.gif)

With one queue pair, work requests leave in order. A 1 MiB block takes 8.39 Mbit ÷ 10 Gb/s = **0.84 ms** to serialize, so a 4 KiB decode message queued behind four of them waits **3.36 ms** before its first byte moves. That wait lands directly in time-to-first-token and in p99.

The dual pool gives each traffic class its own queue pair (libibverbs) or endpoint (libfabric), with its own completion handling, so nothing bulk sits ahead of a hot message in its own queue.

The NIC and wire are still shared. On SoftRoCE the rxe kernel thread processes every QP, so whether the separation survives below the verbs layer is a measurement (Update 8, experiment E3), not an assumption. If hot p99 under a cold stream stays near its unloaded value with two endpoints and grows with one, the design works on that stack. If both grow, the bottleneck is below the QP.

### 3. Where industry stands

![The serving stack and five problems in it](docs/media/03_landscape.gif)

| Problem | Evidence |
|---|---|
| **Built for bulk.** Ray Direct Transport, Mooncake, NIXL and LMCache move homogeneous bulk (weight sync, KV handoff). None classes mixed hot/cold traffic on a contended link. | Update 7 |
| **The stock libfabric path is EFA-shaped.** NIXL's `LIBFABRIC` backend discovers providers in the order cxi, efa, tcp, sockets; verbs is not on the list. Its README requires GPUDirect RDMA and lists AWS EFA as the only validated hardware. On SoftRoCE, or ConnectX-4 without peer memory, it runs over libfabric `tcp` at best. | [nixl `src/utils/libfabric/libfabric_common.cpp`](https://github.com/ai-dynamo/nixl/tree/main/src/utils/libfabric), commit `d642316` |
| **Library side effects.** Mistral traced a 400 MB/min memory leak in disaggregated vLLM to UCX hooking every `mmap` for its registration cache. | [Mistral engineering](https://mistral.ai/news/debugging-memory-leak-in-vllm) |
| **Silent fallback.** IBM Storage Scale APAR IV61625: after a QP error there was no reconnect, and traffic moved to TCP without notice. | Update 7 |
| **Unchecked completions.** This project's own Update 4 pool did not check `wc.status`, so failed writes counted as fast completions. The 8 µs figure is withdrawn; the pool now raises on a bad status. | `dual_qp_pool.py` `check_completion` |

The thesis sits in the cell none of these cover: mixed hot/cold traffic on commodity 10 GbE with SoftRoCE, no GPUDirect, KV staged through host memory.

### 4. The dual pool on libfabric

![Endpoints, completion styles and providers per class](docs/media/04_dualpool.gif)

`libscuffedfabric` opens one fabric and domain, registers one memory arena, and gives each class its own endpoint:

- **Hot:** a 64-entry transmit queue, busy-polled CQ or an `fi_cntr` with `FI_SELECTIVE_COMPLETION` so only the operations that matter generate completions, and `FI_INJECT` for writes under the provider's inject size.
- **Cold:** a 512-entry transmit queue and a CQ with a wait object, so its thread sleeps in `fi_cq_sread` instead of burning a core.

Provider and endpoint type are chosen per class at run time (`verbs` MSG, `verbs;ofi_rxm` RDM, `tcp`, `shm`). Classes with the same provider and type share the domain and the registration; a mixed setup (hot RDM, cold MSG) needs two domains and registers the arena twice.

`libscuffedverbs` implements the same C API (`scuffed_fabric.h`) on raw RC queue pairs, so `sf_bench` and `sv_bench` are one benchmark source linked against two libraries. Any difference between them comes from the library, not the harness.

| libibverbs | libfabric |
|---|---|
| RC QP per class | endpoint per class, `FI_EP_MSG` or `FI_EP_RDM` |
| `RDMA_WRITE_WITH_IMM` | `fi_writedata` with remote CQ data |
| send CQ + completion channel | CQ with `FI_WAIT_UNSPEC`, `fi_cq_sread` |
| (none) | `fi_cntr` remote-write counter (`FI_RMA_EVENT`) |
| QPN / PSN / GID over a TCP side channel | passive endpoint (MSG) or `fi_av_insert` (RDM) |

### 5. FabricBlobChannel: credits and one-sided writes

![Credit-based blob protocol over the pool](docs/media/05_blobchannel.gif)

The connector needs "send this named blob", not raw writes. `FabricBlobChannel` builds that on the pool:

1. Each side's region is split into **receive slots** (written by the peer), **staging slots** (source of its own writes) and a small **scratch** area for credits.
2. A sender holds one **credit per free receive slot** at the peer. To send, it takes a credit, copies a 64-byte header (magic, blob id, key length, flags, total, chunk offset, chunk length), the key and the chunk into the matching staging slot.
3. One `fi_writedata` puts it into the peer's slot with `imm = DATA | slot`. Payload and notification are one operation on one endpoint, so the notification cannot overtake its payload.
4. The receiver copies the chunk out and returns the slot with an 8-byte `fi_writedata` on the **hot** endpoint, `imm = CREDIT | slot`. Credits do not wait behind KV on the cold endpoint.

Blobs larger than a slot are chunked. With N slots, N chunks are in flight; the sender stalls only when every slot is full.

### 6. How the receiver learns data arrived

![Five completion-signaling mechanisms](docs/media/06_completion.gif)

| Mechanism | How the target finds out | Needs | Seen while building |
|---|---|---|---|
| CQ data | the immediate lands in the target's CQ | a posted receive per write | |
| flag in payload | target spins on the buffer's last bytes | the NIC placing the last bytes last | |
| sentinel write | a second 8-byte write after the payload | write-after-write ordering | `shm` does not advertise it |
| remote-write counter | `fi_cntr` counts arrivals | `FI_RMA_EVENT` | `tcp` advertised it but did not count |
| write + 8-byte read | the read returns only after the write is placed | one more round trip | |

The counter is the libfabric form of fabric-lib's `ImmCounter`; write + read is the GPFS flush pattern. Experiment E5 (`sf_bench -m sig`) measures p99 and user-space instructions retired per post for each. A mechanism gets adopted only if it moves p99.

### 7. ScuffedRdmaConnector inside vLLM

![Request flow through prefill, the channel and decode](docs/media/07_connector.gif)

1. The proxy sends the prompt to prefill with `max_tokens=1`, `do_remote_decode` and a transfer id.
2. Each attention layer's `save_kv_layer` gathers that request's paged blocks, copies them to host memory, encodes them (raw bf16, or scuffedQuant for the cold path) and queues one blob per layer. The WFA tags each blob; `wait_for_save` adds a hot `__done__` blob.
3. `request_finished` returns `kv_transfer_params`; the proxy forwards the full request to decode with them.
4. Decode reports the prompt as externally matched, `start_load_kv` waits for each layer and scatters it into the local paged cache, and tokens stream back through the proxy.

If a layer never arrives (30 s default), its blocks go back to vLLM through `get_block_ids_with_load_errors` and are recomputed. If the libfabric channel won't open, the connector uses TCP and records a `tcp_fallback` event. Staging through host memory is deliberate: SoftRoCE has no GPUDirect path, and Tower 2's kernel lacks peer memory support. The connector passes its tests against vLLM `620e8924` and 0.24.0; baselines are vLLM's `NixlConnector` with the UCX backend and with its `LIBFABRIC` backend (`CONNECTOR=nixl-libfabric` in `benchmarks/vllm_disagg/launch.sh`).

### 8. WFA classifier: static thresholds vs learned weights

![Three-state automaton and per-phase cutoffs](docs/media/08_wfa.gif)

One weighted finite automaton per tensor, with states cold, warm and hot. Hot routes to the hot endpoint; warm and cold go to the cold one. The learned version scores every next state from the transfer's signal vector:

$$P(s' \mid s, x) = \mathrm{softmax}_{s'}\big(W_{s,s'} \cdot \varphi(x)\big), \qquad W \in \mathbb{R}^{3 \times 3 \times F}$$

$\varphi(x)$ is the standardized `SignalVector` features (log₂ size, access frequency, queue depth, is_prefill, is_decode, log₂ sequence length, log₂ inter-arrival, is_control), a bias, and two interactions, log₂ size × is_prefill and log₂ size × is_decode. The interactions let one linear map hold a different size cutoff per phase. $W$ is fit with Adam on cross-entropy plus L2, teacher-forcing the previous state.

The static baseline (`WFAClassifier`) routes under 4 KiB hot and over 256 KiB cold, and decides the band in between by access count (10 hits, 5 during decode). On synthetic traces it sends most decode KV deltas cold, because they fall in that band before they have been seen often enough. The learned weights recover per-phase cutoffs. That result is synthetic and partly by construction, since the oracle labels define decode deltas up to 256 KiB as hot. The real test is training on telemetry from the cluster runs, labeled by measured completion latency (`wfa_learner.latency_label`, notebook 04).

### 9. Rule-Node Expression Trees

![Evaluating the default policy on one transfer](docs/media/09_policy.gif)

A rule is a boolean tree over signals (the `SignalVector`) and context (GPU memory, link utilization), plus an action that sets `route` (hot, cold, spill) and/or `compress`. Node types: `and`, `or`, `not`, `threshold`, `in`, and `classifier` (calls a registered classifier such as the WFA, at most once per decision).

Rules run in priority order. A matching rule fills only the fields that are still unset, so the first rule to set a field owns it; `final` stops evaluation. Later rules can read the route decided so far. Every decision carries a trace of which rule set what and why.

Worked example from `middleware/policy/default_policy.json`: a 4 MiB prefill KV block with GPU memory at 93% and the link at 85%. Rule 100 fails (role is kv). Rule 90 (GPU ≥ 0.9 ∧ size > 256 KiB ∧ ¬decode) sets `route=spill`. Rule 80 short-circuits on phase. Rule 70 matches but route is taken. Rule 60 (link ≥ 0.8 ∧ route ∈ {cold, spill} ∧ size ≥ 256 KiB) sets `compress=true`. Result: spill to NVMe, compressed.

### 10. PMP bang-bang controller with a storage arm

![Switching coefficients and the decision per step](docs/media/10_pmp.gif)

The controller chooses which queue the next transfer joins. With queue depths as state and Pontryagin's maximum principle, the Hamiltonian is linear in the control, so the optimal control sits at a vertex: each transfer goes entirely to one arm (bang-bang). For two arms (Update 4) the switching function is

$$S = \lambda_{q_H} C \mu_H - \lambda_{q_C} C \mu_C$$

with costates $\lambda$ (shadow prices of queue depth), link capacity $C$ and service rates $\mu$. $S > 0$ means hot is congested, so send cold; $S < 0$ sends hot.

The storage arm (Update 6) adds GPU KV occupancy $u$ and a running cost above a watermark $u_0$. With the controls on the simplex $u_H + u_C + u_S = 1$, the Hamiltonian is still linear, so the controller picks the smallest of

$$\sigma_H = \alpha\, q_H C \mu_H, \quad \sigma_C = \beta\, q_C C \mu_C, \quad \sigma_S = \delta\, q_S \mu_S - \gamma p, \quad p = \frac{\max(0,\, u - u_0)}{1 - u_0}$$

with costates approximated by queue depth. Below the watermark the spill arm is off and the result equals the two-arm decision. Above it, $-\gamma p$ makes spilling cheap until pressure drops. A deadband keeps the previous arm while it is within a margin of the best, so decisions don't chatter. The queue values in the animation are illustrative.

### 11. scuffedQuant: rotate, quantize, sketch the residual

![Rotation, Lloyd-Max codebook, QJL sketch and the 64-byte wire format](docs/media/11_scuffedquant.gif)

For each K or V vector $x$ (head_dim $d$):

1. Store $\lVert x \rVert$ and work with $x / \lVert x \rVert$.
2. Rotate with a randomized Hadamard transform $H\,\mathrm{diag}(\pm 1)$. Energy spreads evenly across coordinates and they look Gaussian, so one fixed codebook fits every vector and outliers stop wasting levels.
3. Quantize each coordinate to the nearest of 8 Lloyd-Max levels, fit once to the distribution of rotated coordinates (about $\mathcal{N}(0, 1/d)$; times $\sqrt d$ they are about ±0.25, ±0.75, ±1.33, ±2.1): 3 bits per coordinate, giving $\hat x$.
4. Take the residual $r = x - \hat x$ and store $\lVert r \rVert$ plus a 1-bit Johnson-Lindenstrauss sketch, $\mathrm{sign}(S r)$ with $m = 256$ random projections (QJL).

Attention needs inner products, not exact vectors. The sketch gives an unbiased correction to the quantized term:

$$\langle q, k \rangle \approx \langle q, \hat k \rangle + \lVert r \rVert \, \frac{\sqrt{\pi/2}}{m} \sum_{j=1}^{m} \mathrm{sign}(S r)_j \, (S q)_j$$

At head_dim 64 the packed wire format is 4 B ($\lVert x \rVert$) + 4 B ($\lVert r \rVert$) + 24 B (64 × 3-bit indices) + 32 B (256 sign bits) = **64 B per vector, 2× smaller than FP16** (the earlier "4×" was against FP32). On Granite 3.3-2B the top-8 attention overlap is 91.1% ± 3.3% over 40 layers, minimum 82.8% (`benchmarks/results/scuffed_quant_llm.json`). TurboQuant-style rotate and quantize (Zandieh et al.); the sketch is QJL (Zandieh, Daliri, Han).

### 12. NVMe storage tier

![Spill, coalesced writes, extent reuse, verified reads, measured sweep](docs/media/12_storage.gif)

When the controller or the policy picks spill, `StorageTier.spill(key, buf)` queues the block and returns a future. Every `coalesce` blocks become one `pwrite` and one `fdatasync` into a single backing file, in 4096-byte aligned extents. `delete(key)` returns the extent to a free list, neighbors merge, and the next spill reuses space first-fit. `retrieve(key)` is a `pread` followed by a CRC32 check; contiguous keys are read with one `pread`. `O_DIRECT` is used when the filesystem allows it, and the tier records why when it doesn't.

Measured on Chimera's NVMe with 1.5 MiB KV blocks (`benchmarks/results/test_arch/chimera_storage_spill.json`):

| coalesce | write MB/s | read MB/s |
|---|---|---|
| 1 | 662 | 1731 |
| 10 | 731 | 2149 |
| 20 | 803 | 2188 |
| 50 | 827 | 1104 |

Writes gain from batching. Reads peak at 20 blocks and fall at 50 on this drive, so the batch size is a tuning knob, not "bigger is better".

## Components

| Component | Where | State |
|---|---|---|
| Dual pool on libfabric | `middleware/libscuffedfabric/` | built; tested here on tcp, tcp;ofi_rxm, shm; verbs provider runs on the cluster |
| Dual QP pool on libibverbs (C) | `middleware/libscuffedverbs/` | built; compile-checked here, runs on SoftRoCE |
| Dual QP pool (Python, pyverbs) | `middleware/rdma_tensor_cache/dual_qp_pool.py` | original MVP; completion status now checked |
| Python binding + blob channel | `middleware/fabric/` | `FabricPool`, `FabricBlobChannel` over either C library |
| Telemetry | `middleware/telemetry.py` | signal vectors, per-class histograms, QP error / reconnect / TCP-fallback events, Prometheus `/metrics` |
| WFA classifier | `middleware/rdma_tensor_cache/wfa_classifier.py`, `wfa_learner.py` | static thresholds; learned transition weights (gradient descent) with synthetic validation |
| Rule-Node Expression Trees | `middleware/policy/` | and/or/not/threshold/in/classifier nodes, priority rules, explanation traces |
| PMP controller | `middleware/rdma_tensor_cache/pmp_controller.py` | bang-bang hot/cold; storage-pressure arm returns HOT/COLD/SPILL |
| Storage tier | `middleware/rdma_tensor_cache/storage_tier.py` | NVMe spill/retrieve, coalescing, O_DIRECT, crc32 |
| scuffedQuant | `middleware/rdma_tensor_cache/scuffed_quant.py` | bit-packed wire format, size reported from packed bytes |
| vLLM connector | `middleware/vllm_plugin/` | `ScuffedRdmaConnector` on `KVConnectorBase_V1`, proxy, loopback check; tests pass against vLLM 620e8924 and 0.24.0 |
| NCCL net plugin | `middleware/nccl_plugin/` | `ncclNetPlugin_v8`, hot/cold QPs split at 4 KB; builds, not yet run under NCCL |

<details><summary>Static system map (Mermaid)</summary>

```mermaid
flowchart LR
    subgraph Cerberus["Cerberus · prefill · 2× RTX 5090"]
        PF[vLLM prefill worker<br/>ScuffedRdmaConnector]
    end
    subgraph Mid["libscuffedrdma"]
        direction TB
        TEL[telemetry<br/>signal vectors, p50/p99, Prometheus]
        WFA[WFA classifier<br/>static or learned weights]
        POL[Rule-Node Expression Tree<br/>policy]
        PMP[PMP bang-bang controller<br/>+ storage-pressure arm]
        QNT[scuffedQuant<br/>Hadamard + Lloyd-Max + 256-bit QJL]
        subgraph Pool["Dual pool · one domain / PD"]
            direction LR
            HOT[["Hot endpoint / QP<br/>busy-poll CQ or fi_cntr"]]
            COLD[["Cold endpoint / QP<br/>deep queue, wait object"]]
        end
        TEL --> WFA --> POL --> PMP
        PMP -->|hot| HOT
        PMP -->|cold| COLD
        QNT -.->|optional| COLD
    end
    subgraph Chimera["Chimera · decode · 3× RTX 3090"]
        DC[vLLM decode worker<br/>ScuffedRdmaConnector]
    end
    PF -->|KV blocks| TEL
    HOT ==>|RDMA write + imm| DC
    COLD ==>|RDMA write + imm| DC

    classDef pool fill:#fef3c7,stroke:#b45309,stroke-width:1px
    classDef ctrl fill:#dbeafe,stroke:#1d4ed8,stroke-width:1px
    classDef quant fill:#dcfce7,stroke:#15803d,stroke-width:1px
    class HOT,COLD pool
    class TEL,WFA,POL,PMP ctrl
    class QNT quant
```

</details>

---

## Notebooks

Each notebook has a parameter cell. `MODE = "local"` runs smoke sizes on any Linux box with libfabric (tcp / shm providers), results to `/tmp`. `MODE = "cluster"` runs on Cerberus and Chimera, results to `benchmarks/results/`, tagged with hostname and UTC time. Notebook 08 has `MODE = "gpu"` for one machine with an NVIDIA GPU. Local numbers are smoke tests, not results.

| Notebook | What it runs |
|---|---|
| [00_environment_check](notebooks/00_environment_check.ipynb) | RDMA devices, GID table, libfabric providers, pyverbs, builds all native code, full test suite |
| [01_hol_blocking](notebooks/01_hol_blocking.ipynb) | hot RTT under a cold bulk stream, single vs dual endpoint, native verbs vs libfabric; re-run of the Update 4 pyverbs benchmark |
| [02_completion_signaling](notebooks/02_completion_signaling.ipynb) | CQ data vs flag-in-payload vs sentinel vs remote-write counter vs trailing READ, instructions per post |
| [03_libfabric_vs_libibverbs](notebooks/03_libfabric_vs_libibverbs.ipynb) | latency and bandwidth per stack, MSG / RDM / mixed endpoints, counters vs CQ, wait objects, blob channel vs TCP |
| [04_wfa_and_policy](notebooks/04_wfa_and_policy.ipynb) | learned WFA vs static thresholds, policy tree decisions with explanations |
| [05_scuffedquant](notebooks/05_scuffedquant.ipynb) | packed sizes, Granite 3.3-2B top-8 overlap per layer |
| [06_vllm_disagg_ttft](notebooks/06_vllm_disagg_ttft.ipynb) | ScuffedRdmaConnector loopback, TTFT / ITL sweeps against NIXL (UCX and LIBFABRIC backends) and single-node baselines |
| [07_storage_tier](notebooks/07_storage_tier.ipynb) | NVMe spill coalescing sweep, PMP storage arm |
| [08_local_gpu](notebooks/08_local_gpu.ipynb) | one GPU: connector with KV caches on the GPU, scuffedQuant on real KV, vLLM prefill + decode on one card through libfabric `shm`, greedy-output match and TTFT / ITL against a single instance and NIXL |

## Repository

| Path | Contents |
|------|----------|
| `middleware/` | Transports (TCP / SoftRoCE / TTPoe), RDMA bootstrap, telemetry, policy engine |
| `middleware/libscuffedfabric/` | libfabric dual-endpoint pool, `sf_bench` |
| `middleware/libscuffedverbs/` | libibverbs implementation of the same API, `sv_bench` |
| `middleware/fabric/` | ctypes binding, `FabricBlobChannel`, `TcpBlobChannel` |
| `middleware/rdma_tensor_cache/` | pyverbs dual QP pool, WFA (static + learned), PMP, scuffedQuant, storage tier |
| `middleware/vllm_plugin/` | ScuffedRdmaConnector, disagg proxy, loopback |
| `middleware/nccl_plugin/` | NCCL net plugin |
| `notebooks/` | research notebooks (generated from `notebooks/_build/`) |
| `docs/animations/`, `docs/media/` | Manim sources for the README animations (`render.sh`) and the rendered GIFs |
| `scripts/local_gpu/` | `setup_gpu_env.sh`: libfabric, CUDA torch, vLLM, builds and tests on a GPU machine (WSL2 or Linux) |
| `tests/`, `middleware/tests/` | pytest suite (`pytest -q` from the repo root) |
| `benchmarks/` | benchmark scripts, `fabric/runner.py`, `vllm_disagg/`, `test_arch/`, results |
| `deployment/` | Docker/K8s for Chimera/Cerberus, FA3 Blackwell patch |
| `Updates/` | Updates 1 through 8 and 5-2 (LaTeX + PDF), each with a README of the work and sources |
| `References/` | saved papers and pages; `Bookmarks_10-22/RANKED_SOURCES.md` ranks every source |
| `vllm/`, `uccl/` | submodules (reference / comparison) |
| `REFERENCES.md` | annotated bibliography |

## Hardware

| Node | Role | GPUs | VRAM | NIC | RDMA |
|------|------|------|------|-----|------|
| Cerberus | Prefill | 2× RTX 5090 | 64 GB | Intel X710 10GbE | SoftRoCE (X710 has no iWARP) |
| Chimera | Decode | 3× RTX 3090 | 72 GB | Aquantia AQC107 10GbE | SoftRoCE |
| Tower 1 | Dev | RTX 5070 Ti | 16 GB | ConnectX-4 100GbE | Hardware RoCEv2 |
| Tower 2 | Dev | 2× Tesla V100 | 64 GB | ConnectX-4 100GbE | Hardware RoCEv2, GPUDirect |

---

## Results

Only numbers with a results file in the repo.

| Metric | Value | Source |
|--------|-------|--------|
| scuffedQuant 3-bit + 256-bit QJL, top-8 attention overlap (Granite 3.3-2B, FP32 KV) | 91.1% ± 3.3% over 40 layers (min 82.8%) | `benchmarks/results/scuffed_quant_llm.json` |
| scuffedQuant 3-bit top-8 (Granite 3.3-2B, MLX 4-bit) | 100.0% over 40 layers | `benchmarks/results/scuffed_quant_mlx.json` |
| scuffedQuant packed size at head_dim 64 | 64 B per vector: 2× vs FP16, 4× vs FP32 | `tests/test_scuffed_quant.py`, notebook 05 |
| NVMe spill, Chimera, coalesce 1 → 50 blocks of 1.5 MiB | write 662 → 827 MB/s; read peaks 2188 MB/s at 20, 1104 MB/s at 50 | `benchmarks/results/test_arch/chimera_storage_spill.json` |
| Per-architecture scuffedQuant (Transformer, Mamba state, Granite 4 hybrid, MoE) on Chimera and Cerberus | see Update 5-2 | `benchmarks/results/test_arch/` |

### Withdrawn, to be re-measured

- **Cross-node decode latency "8 µs"** (`dual_qp_remote_benchmark.json`). The pyverbs pool did not check `wc.status`, so error and flush completions counted as fast completions; 8 MB writes "finished" in about 8 µs, which 10GbE cannot do. Fixed in `dual_qp_pool.py` (`check_completion`); re-run in notebook 01.
- **"4× vs FP16" compression.** The ratio was against FP32. Against FP16 it is 2× at head_dim 64. `kv_compressed_bytes` in `scuffed_quant_llm.json` divides FP16 bytes by the FP32 ratio and is understated by 2×.
- **SoftRoCE bandwidth, single-QP p50, dual-QP overhead, FA3 Blackwell speedup, gpt-oss-120b tok/s.** Earlier README rows pointed at sources that do not hold them (backlog drafts, a different link speed, an Ollama run). Notebooks 01 to 03 re-measure the transport numbers on the current harness.

## Built

- [x] libfabric dual-endpoint pool, per-class endpoint type (MSG / RDM), hot completions via CQ or `fi_cntr`, cold CQ with a wait object, one MR per domain
- [x] Native libibverbs implementation of the same API; `sv_bench` and `sf_bench` share one source
- [x] Benchmarks: completion-signaling mechanisms, bandwidth, mixed hot/cold head-of-line test, instructions per post, CPU pinning, JSON output
- [x] Python binding and `FabricBlobChannel` (credit-based slots, notification and payload in one `fi_writedata`)
- [x] Unified telemetry with Prometheus exporter
- [x] Learned WFA transition weights and synthetic validation; Rule-Node Expression Tree policy engine
- [x] PMP storage-pressure arm; NVMe storage tier with coalescing
- [x] `ScuffedRdmaConnector` for vLLM V1 (pinned vLLM 620e8924), disagg proxy, TTFT runner
- [x] NCCL net plugin builds and exports `ncclNetPlugin_v8`
- [x] Dual QP pool over SoftRoCE with WFA routing; PMP controller; RDMA bootstrap (handshake, GID discovery, QP state machine with retry); security audit fixes (Updates 4 and 5)
- [x] scuffedQuant on Granite 3.3-2B and per-architecture state (Updates 4 and 5-2)

## Planned

- [ ] Cluster runs of notebooks 01 to 03 on Cerberus ↔ Chimera (SoftRoCE) and Tower 1 ↔ Tower 2 (ConnectX-4): the libfabric versus libibverbs comparison for Update 8
- [ ] Single-GPU end-to-end run on the desktop GPU (notebook 08): vLLM prefill + decode with the connector, greedy match, TTFT / ITL
- [ ] vLLM disaggregated serving with ScuffedRdmaConnector across nodes, TTFT / ITL against NIXL on UCX and on its LIBFABRIC backend (notebook 06)
- [ ] NIXL + Ray RDT view-count sweep over SoftRoCE with competing hot traffic (Update 7)
- [ ] NCCL plugin under NCCL with vLLM tensor parallel; PMP-driven split instead of the fixed 4 KB threshold
- [ ] Signal dumps from the transports into the learned WFA (notebook 04 cluster cell)
- [ ] GPUDirect RDMA on Tower 2 (blocked on the PVE kernel's `CONFIG_INFINIBAND_PEER_MEM`)

---

## Usage

```bash
# native code (needs libfabric-dev, libibverbs-dev / rdma-core)
make -C middleware/libscuffedfabric && make -C middleware/libscuffedverbs && make -C middleware/nccl_plugin

# tests
python3 -m pytest -q

# SoftRoCE on both nodes
sudo modprobe rdma_rxe && sudo rdma link add rxe0 type rxe netdev <10GbE iface>

# hot-path latency, libfabric verbs provider (server first, then client)
middleware/libscuffedfabric/sf_bench -r server -H <server ip> -p verbs -t msg -d rxe0 -m sig -M cq
middleware/libscuffedfabric/sf_bench -r client -H <server ip> -p verbs -t msg -d rxe0 -m sig -M cq

# same benchmark on native libibverbs
middleware/libscuffedverbs/sv_bench -r server -H <server ip> -d rxe0 -m hol
middleware/libscuffedverbs/sv_bench -r client -H <server ip> -d rxe0 -m hol

# vLLM connector data path without vLLM
python3 -m middleware.vllm_plugin.loopback --role both --transport fabric --provider tcp

# GPU machine (Ubuntu under WSL2, or Linux): CUDA torch + vLLM + libfabric, builds, tests
bash scripts/local_gpu/setup_gpu_env.sh            # then notebooks/08_local_gpu.ipynb with MODE = "gpu"
```

The notebooks wrap all of this; start with `notebooks/00_environment_check.ipynb` on each node.

## Timeline

| Window | Milestone | Status |
|--------|-----------|--------|
| Jan–Feb 2026 | Hardware bring-up, Updates 1–3 | done |
| Mar–Apr 2026 | Python MVP, scuffedQuant, Updates 4, 5, 5-2, 6 | done |
| Sep 2026 | Transport landscape (Update 7) | done |
| Oct 2026 | libfabric pool, native verbs pool, connector, policy, telemetry, notebooks | built |
| Oct–Nov 2026 | Cluster runs, Update 8 (libfabric), full thesis draft | in progress |
| Dec 2026 | Defense | planned |

## Citations

Full bibliography in [REFERENCES.md](REFERENCES.md); ranked source list in [References/Bookmarks_10-22/RANKED_SOURCES.md](References/Bookmarks_10-22/RANKED_SOURCES.md). Core references:

- Kwon et al., *PagedAttention*, SOSP 2023. [arXiv:2309.06180](https://arxiv.org/abs/2309.06180)
- Zandieh et al., *TurboQuant*. [arXiv:2504.19874](https://arxiv.org/abs/2504.19874)
- Zandieh, Daliri, Han, *QJL: 1-Bit Quantized JL Transform for KV Cache Quantization*. [arXiv:2406.03482](https://arxiv.org/abs/2406.03482)
- Grun et al., *A Brief Introduction to the OpenFabrics Interfaces*, HotI 2015. libfabric man pages: `fi_endpoint(3)`, `fi_cntr(3)`, `fi_mr(3)`, `fi_verbs(7)`, `fi_rxm(7)`
- Licker, Hu, Zaytsev, Chen, *fabric-lib: RDMA Point-to-Point Communication for LLM Systems* (formerly TransferEngine; closest system-level comparison). [arXiv:2510.27656](https://arxiv.org/abs/2510.27656)
- NIXL libfabric plugin (the stock stack's libfabric path; baseline in notebooks 06 and 08). [ai-dynamo/nixl](https://github.com/ai-dynamo/nixl/tree/main/src/plugins/libfabric)
- Pontryagin et al., *The Mathematical Theory of Optimal Processes*, 1962.

## License

[MIT](LICENSE). Author: Nathan Gopee
