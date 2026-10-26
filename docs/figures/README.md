# Figures

Every figure here is written by a notebook in [`notebooks/`](../../notebooks/) through its `fig(name)` helper, as PNG (170 dpi) and PDF (vector, for LaTeX). Re-running a notebook overwrites its figures.

- **Top level** (`docs/figures/<name>`): model figures. Arithmetic, proofs, or results files already in the repo. The same on every machine; usable in the paper as they are.
- **`local/`, `cluster/`, `gpu/`**: measured on the machine that ran the notebook, in that `MODE`. `local/` is the smoke run on a VM with the libfabric `tcp` / `shm` providers and `/tmp` instead of NVMe: it shows the measurement path works, nothing else. The paper's measured figures come from `cluster/` (server 1 and server 2) and `gpu/`.

The number prefix is the README section the figure belongs to.

| Figure | Notebook | Kind | What it shows |
|---|---|---|---|
| `01_kv_traffic` | 01 | model | KV bytes per request and wire time vs prompt length, Granite 3.3-2B bf16, 10 / 25 / 100 Gb/s |
| `02_hol_model` | 01 | model | mean hot wait vs cold message size: one FIFO (Pollaczek–Khinchine), hot priority per message (Cobham), per packet (two QPs) |
| `<mode>/02_hol_measured` | 01 | measured | hot RTT p99 with the cold stream off / 256 KiB / 1 MiB, single vs dual endpoint, per stack |
| `05_credit_window` | 03 | model | FabricBlobChannel throughput bound $NB/R$ vs credit round trip, against 10 / 25 / 100 Gb/s |
| `<mode>/04_dualpool_latency_bw` | 03 | measured | hot-path one-way latency (p50, p99) and cold-path bandwidth (busy poll vs wait object) per stack |
| `<mode>/04_dualpool_matrix` | 03 | measured | hot p99 with and without a cold stream for each libfabric endpoint / completion configuration |
| `<mode>/05_blob_channel` | 03 | measured | FabricBlobChannel vs TcpBlobChannel throughput and time per blob |
| `<mode>/06_completion_measured` | 02 | measured | one-way latency per completion mechanism (cq, flag, sentinel, cntr, read) and payload |
| `<mode>/06_completion_instructions` | 02 | measured | instructions retired per post, per mechanism (only where perf counters exist) |
| `07_staging_cost` | 06 | model | host staging copy vs wire time per layer size; the ratio is $C/(8P)$ |
| `<mode>/07_ttft_itl` | 06 | measured | TTFT and ITL percentiles vs prompt length per setup (mock server in local mode) |
| `gpu/07_single_gpu_ttft_itl` | 08 | measured | the same on one GPU shared by prefill and decode |
| `08_wfa_static_phases` | 04 | model | Proposition 1: the static phase detector's outputs on in-order decode traffic (DECODE = 0) and where the deltas are routed |
| `08_wfa_training` | 04 | model | learned WFA training loss (strictly convex objective) |
| `08_wfa_heldout` | 04 | model | learned vs static: route accuracy and hot recall on held-out synthetic mixes |
| `08_wfa_confusion` | 04 | model | learned WFA state confusion per mix |
| `08_wfa_weights` | 04 | model | hot − cold logit margin per feature and current state |
| `09_policy_routes` | 04 | model | routes and compress decisions of the default policy per context |
| `10_pmp_regions` | 04 | model | decision regions in the $(q_H, q_C)$ plane: implemented rule, derived service-allocation rule, routing-consistent rule |
| `10_pmp_simulation` | 04 | model | queue lengths and mean wait under each rule on Poisson arrivals |
| `10_pmp_spill` | 07 | model | three-option decision vs GPU memory pressure, and the switching coefficients |
| `11_rotation` | 05 | model | per-channel variance before and after the rotation; rotated coordinates vs $\mathcal N(0, 1/d)$ with the 3-bit Lloyd–Max levels |
| `11_bytes_per_vector` | 05 | model | bytes per K or V vector: bf16, FP8, KIVI 2-bit, scuffedQuant with and without the sketch, at head_dim 64 and 128 |
| `11_sketch_error` | 05 | model | inner-product error vs sketch size, with the sketch (follows $c/\sqrt m$) and reconstruction only |
| `<mode>/11_topk_overlap` | 05 | measured | top-8 overlap per layer (synthetic KV in local mode, the real model in cluster mode) |
| `11_topk_granite_update4` | 05 | model (repo results) | Granite 3.3-2B top-8 overlap per layer, 91.1% ± 3.3%, and inner-product error with vs without the sketch |
| `12_coalescing_fit` | 07 | model (repo results) | $t(n) = a + nb$ fitted to the Update 6 NVMe sweep; asymptote $B/b$ |
| `<mode>/12_storage_sweep` | 07 | measured | write and read MB/s vs coalesce depth through `StorageTier`, with the Update 6 points |

Model figures that depend on an assumed constant say so in their caption (the 20 GB/s PCIe rate in `07_staging_cost`, Poisson arrivals in `02_hol_model` and `10_pmp_simulation`).
