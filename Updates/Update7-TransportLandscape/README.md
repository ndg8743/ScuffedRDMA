# Update 7: Ray Direct Transport, ROCm eRNIC, Near-SoL Collectives, and the Transport Landscape

Dated September 2026; committed in `353551b` (2026-09-11). No code changed after it until October.

The update reads three recent developments against libscuffedrdma and then places the middleware among the transport stacks. Ray Direct Transport (RDT) keeps GPU tensors out of Ray's object store and ships them over NIXL (which runs on UCX); its four optimizations (register once and send views as offsets, ahead-of-time registration, targeted receive, pooling small tensors) are the same amortization moves the tensor cache makes, but RDT serves barrier-style weight sync where nothing competes for the link. AMD's ROCm eRNIC is an emulated RDMA NIC for VMs, useful as a published software-RDMA latency floor and for its per-instance Prometheus exporter. The "Every us Matters" paper argues decode is latency-bound and uses data-as-signal synchronization (flags in the payload, sentinel buffers) instead of barriers. The conclusion: all three validate the middleware's mechanics, and none classes traffic or schedules a contended link; mixed hot/cold traffic on one commodity Ethernet link is where the thesis sits. The second half places libscuffedrdma against libfabric, UCX and DOCA (it is built on libibverbs and keeps UCX out of the data path), notes that libfabric's endpoint types and counters map directly onto the hot/cold split, and reads IBM Storage Scale's published RDMA defects (data integrity, write flush, QP reconnect, silent TCP fallback) as requirements for the middleware.

## Research

Ray Direct Transport and NIXL
- Anyscale, RDT: fast weight syncing for RL (7.5x over naive NIXL on 2x GB200 MNNVL; 18x and 2.2x results on H100 clusters, their hardware). https://www.anyscale.com/blog/rdt-ray-direct-transport-fast-easy-weight-syncing-for-rl-reinforcement-learning
- Anyscale, RDMA support in Ray Core (part 1). https://www.anyscale.com/blog/ray-direct-transport-rdma-support-in-ray-core
- Ray docs: RDT, custom tensor transport, GPU object store RFC #51173. https://docs.ray.io/en/master/ray-core/direct-transport.html
- NIXL docs: UCX is the network backend. [GitHub_NIXL_NVIDIA_Inference_Xfer.md](../../References/Bookmarks_Collection/GitHub_NIXL_NVIDIA_Inference_Xfer.md)
- Mooncake (arXiv:2407.00079): the KV-centric disaggregated baseline RDT compares against. No local copy.

Emulated and software RDMA
- ROCm/rocm-ernic repo and its perf reports (RC WRITE 4 KB about 181 us over its TCP mesh, about 1.8-1.9 GB/s from 512 KB, their EPYC host). https://github.com/ROCm/rocm-ernic. Related local: [AMD_ERNIC_Product_Guide.md](../../References/Bookmarks_Collection/AMD_ERNIC_Product_Guide.md) (the Xilinx ERNIC soft IP, a different product).
- SoftRoCE background. [SoftRoCE_Paper_-_RoCE_Initiative_2016.pdf](../../References/Bookmarks_Collection/SoftRoCE_Paper_-_RoCE_Initiative_2016.pdf)

Collectives and latency
- Shen et al., Every us Matters: near speed-of-light GPU collectives (arXiv:2607.16100, NVIDIA and ETH Zurich): decode-is-latency-bound citation (`sol2026`), LL-style flags, sentinel buffers. [Near_SoL_GPU_Collectives_NVIDIA_2607.16100.pdf](../../References/Bookmarks_10-22/Near_SoL_GPU_Collectives_NVIDIA_2607.16100.pdf)

Transport stacks (the libfabric thread for the next update)
- Brian Smith, Omni-Path and the Open Fabrics Interfaces (Cornelis, MUG'23): libfabric vs UCX framing, eager/multi-packet/rendezvous selection in OPX. [MUG23_OmniPath_OFI_Brian_Smith_Cornelis.pdf](../../References/Bookmarks_10-22/MUG23_OmniPath_OFI_Brian_Smith_Cornelis.pdf)
- Shamis et al., UCX (2015): UCS/UCT/UCP layers; libfabric can sit under UCT. No local copy.
- Papadopoulou, Oden and Balaji, A Performance Study of UCX over InfiniBand (CCGrid 2017): rkey re-resolution, non-inlinable dispatch, unnecessary progress polling; the instruction-count methodology. No local copy.
- UCX FAQ: "not a user-level driver", `UCX_TLS` caveats, fabric-level `UCX_IB_SL` / `UCX_IB_TRAFFIC_CLASS` only. https://github.com/openucx/ucx/blob/master/docs/source/faq.md
- NVIDIA DOCA SDK. https://docs.nvidia.com/doca/sdk/
- Bookmarked since and relevant to the libfabric comparison: ARCHER2 OFI vs UCX on HPE Cray EX ([slides](../../References/Bookmarks_10-22/ARCHER2_OFI_vs_UCX_CUG2022.pdf), [repo notes](../../References/Bookmarks_10-22/ARCHER2_OFI_vs_UCX_GitHub.md)), Castain and Squyres, The ABCs of Open MPI ([pdf](../../References/Bookmarks_10-22/ABCs_of_Open_MPI_Part1_Castain_Squyres_2020.pdf)), Rohit Zambre on libfabric vs libibverbs ([md](../../References/Bookmarks_RDMA/root/For_the_RDMA_novice_libfabric_libibverbs_InfiniBand_OFED_MOFED_Rohit_Zambre.md)), UCX in a nutshell and comparison to libfabric, OSTI ([md](../../References/Bookmarks_RDMA/root/UCX_in_a_nutshell_and_comparison_to_libfabric_Technical_Report_OSTI_GOV.md)), CSCS libfabric docs ([md](../../References/Bookmarks_RDMA/root/libfabric_CSCS_Documentation.md)), Lequn Chen on libfabric over EFA ([md](../../References/Bookmarks_Collection/RDMA_EFA_3200Gbps_Network.md)), jcxue RDMA-Tutorial ([md](../../References/Bookmarks_10-22/RDMA-Tutorial_jcxue_GitHub.md)).

IBM Storage Scale RDMA defect record
- APAR IJ44629 (incorrect reads under RDMA), the IJ44524/IJ44525 write-flush alert, the `verbsRdmasPerNode` vs `nsdMaxWorkerThreads` alert, APAR IJ25511 (quorum expel), APAR IV61625 (no reconnect after QP error, silent TCP fallback), 5.1.0.x resolved APARs (RoCE + `verbsRdmaCm` with non-link-local IPv6). All IBM Support pages; URLs in the tex bibliography. No local copies.
- T. Hoover, Storage Scale S3 over RDMA (June 2026): control on HTTP, bulk on RDMA. No local copy.
- Background: [Improving_Spectrum_Scale_RDMA_SSSD21.pdf](../../References/Bookmarks_Collection/Improving_Spectrum_Scale_RDMA_SSSD21.pdf)

## Work done

Writing only: `Updates/Update7-TransportLandscape/update7.tex` and `.pdf`. No code, configs or results came out of this update.

## Next steps as written, status today

| Next step | Status | Evidence |
|---|---|---|
| 1. Add RDT, eRNIC, the SoL paper and the libfabric/UCX/DOCA taxonomy to the related-work chapter; cite `sol2026` | open | `Updates/Drafts/draft1.tex` last changed 2026-04-16 (`b23b058`) and does not mention RDT, eRNIC or libfabric. |
| 2. `pip install nixl` + Ray on the cluster, confirm NIXL picks UCX over SoftRoCE, RDT view-count sweep (1 to 10,000 views) with and without competing hot traffic | open | |
| 3. Completion-signaling microbenchmark on hot QPs: CQ vs flag-in-payload vs sentinel vs trailing RDMA READ; report instructions per op | built (Oct 2026), cluster run pending | Notebook 02; native benches in `middleware/libscuffedverbs/` and `middleware/libscuffedfabric/` (libfabric adds `fi_cntr` as a fifth mode). |
| 4. Dual QP pool on libfabric's verbs provider vs the libibverbs pool on identical payloads | built (Oct 2026), cluster run pending | `middleware/libscuffedfabric/` (C, dual-endpoint pool, `sf_bench`), Python binding in `middleware/fabric/`, notebook 03. Runs on the verbs provider on the cluster and on the tcp/shm providers anywhere. |
| 5. Per-QP-class Prometheus counters including QP error/reconnect and TCP fallback | built (Oct 2026) | `middleware/telemetry.py` exports per-class ops, bytes, latency histograms and `qp_error` / `reconnect` / `tcp_fallback` / `timeout` / `retry` events on `/metrics` (`tests/test_telemetry.py`). Transports reporting into it is in progress. |

## Run it

- [`notebooks/01_hol_blocking.ipynb`](../../notebooks/01_hol_blocking.ipynb): the mixed hot/cold regime this update says RDT does not cover.
- [`notebooks/02_completion_signaling.ipynb`](../../notebooks/02_completion_signaling.ipynb): Next step 3.
- [`notebooks/03_libfabric_vs_libibverbs.ipynb`](../../notebooks/03_libfabric_vs_libibverbs.ipynb): Next step 4, including MSG vs RDM endpoints and counters vs CQ for the hot class.
- Telemetry: `middleware/telemetry.py`, `tests/test_telemetry.py`.

## Corrections

- **"Upstream UCX patches from the Update 4-5 work" and "the same `ucp_put`/`ucp_get` paths that Updates 4 and 5 patched".** The six PRs were never merged (#11305 to #11309 open, review required; #11304 closed as of 2026-10-22). Upstream UCX, and therefore NIXL and RDT, has none of those changes. The sentence that "the upstream UCX patches stand on their own because NIXL, RDT, and vLLM's existing connectors all route through UCX and inherit those fixes" should go.
- **"That is the head-of-line blocking measured in Update 4."** Update 4 did not measure HOL blocking. Its loopback run was single-threaded on SoftRoCE, where operations complete one at a time, and the dual QP pool came out slightly slower (p99 21.4 us vs 17.7 us, `benchmarks/results/aggregate_results.json`). The concurrent run that would show HOL blocking is Next step 1 of Updates 4 and 5, still open. Next step 2 here ("the Update-4 HOL blocking") needs the same fix.
- **"A pre-registered tensor-cache arena addressed by rkey offsets".** The Python pool registers named buffers on one PD and supports offsets; a single `ibv_reg_mr` over vLLM's contiguous PagedAttention buffer is not implemented yet.
- **SwiftRDMA and Celeris** are named as the closest related work, but neither has a local copy. The local "Swift: Rethinking RDMA Control Plane for Elastic Computing" (arXiv:2501.19051) is about connection setup cost; confirm it is the paper meant before citing it as SwiftRDMA (APNet 2025).
