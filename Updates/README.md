# Updates

Weekly thesis updates for the ScuffedRDMA project (RDMA transport for distributed LLM inference). Each folder contains a `.tex` source plus the rendered `.pdf`. Read the PDFs in order if you want the narrative arc.

## Current status

Update 6 is the latest. It covers storage-tier integration (GPFS, sandook, WEKA) for KV cache offloading, block size tradeoffs, and how the dual QP pool extends to cover storage traffic. Update 5 reviewed the six upstream UCX PRs and hardened the middleware. Update 4 established the UCX analysis, libscuffedrdma design, and upstream contribution plan.

## Index

- **Proposal/** - Original and revised thesis proposals (`propsal.tex`, `revised_proposal_v2.tex`). `Hydra_Lab_Test.md` is the SoftRoCE / SR-IOV / GPUDirect setup guide for the Hydra cluster.
- **Update1-HardwareSetup** - Hardware procurement and bring-up for the two-tower testbed: V100s, ConnectX-4 NICs, DDR5, BIOS/rebar, photos of the rack.
- **Update2-ImplementationPlan** - Thesis scope and architecture. What vLLM already provides, what the adaptive RDMA contribution is, the evaluation plan, and risk mitigation.
- **Update3-TensorCacheArchitecture** - RDMA tensor cache design, NVIDIA communication stack survey, MLA/MQA KV cache problem, CUDA vs Triton, three experimental pillars, and ScuffedKernels / ScuffedSearch sub-projects.
- **Update4-UCX** - UCX codebase analysis, PMP/WFA classification theory, upstream PR table, TurboQuant KV compression pipeline, cross-node SoftRoCE benchmark results, and the Python MVP.
- **Update5-UCX-Review** - Review of the six upstream UCX PRs with real diffs, CI flakiness notes, security audit, and middleware hardening.
- **Update6-StorageTier** - Storage-tier integration: GPFS block size tradeoffs, sandook NVMe aggregation, WEKA AMG, four-tier KV memory hierarchy, dual QP extension to storage spill/retrieve.
- **Drafts/** - `draft1.tex` is the rolling thesis draft. `updates-todo/` holds exploratory updates that are not yet in the main sequence (FlashAttention-3 on Blackwell, gpt-oss-120b benchmarks, transport middleware, infrastructure testing, WFA classifier validation, mechanistic interpretability, work-first scheduling, USB4, lock-free middleware, Kokkos remote spaces, architecture comparison).

## Notes

The `Drafts/updates-todo/` folder uses its own numbering that does not line up with the main Update1-5 sequence. For example, `Update4-FlashAttention3Blackwell` is a drafted side-update, not a replacement for `Update4-UCX`. Treat `updates-todo/` as a backlog of potential future updates rather than a parallel canonical sequence.
