# Updates

Thesis updates for ScuffedRDMA (RDMA transport middleware for disaggregated LLM inference). Each folder holds the `.tex` source, the rendered `.pdf`, and a `README.md` that documents the work behind the update: the sources it leans on, the code and results that came out of it, the status of every next step, and corrections found later.

## Current status

Update 8 (draft) builds the dual pool on libfabric (`middleware/libscuffedfabric/`) and a native libibverbs implementation of the same API (`middleware/libscuffedverbs/`), so both stacks run the identical benchmark. The method and build are done; the cluster tables are filled by running notebooks 01 to 03 in cluster mode. Update 7 read Ray Direct Transport, ROCm eRNIC and the near speed-of-light collectives paper against the middleware and placed it among the libfabric, UCX and DOCA stacks.

Two earlier figures are withdrawn and get re-measured in notebook 01: the 8 µs cross-node latency (the Python pool did not check completion status) and the 4x-vs-FP16 compression ratio (it was against FP32; against FP16 it is 2x at head_dim 64).

## Index

| Update | Topic | Notes |
|---|---|---|
| [Proposal](Proposal/README.md) | original and revised proposals, Hydra lab test guide | what was kept, reshaped, deferred |
| [Update 1](Update1-HardwareSetup/README.md) | hardware procurement and bring-up | |
| [Update 2](Update2-ImplementationPlan/README.md) | scope, architecture, evaluation plan | phase-by-phase status |
| [Update 3](Update3-TensorCacheArchitecture/README.md) | tensor cache, communication stack survey, experimental pillars | |
| [Update 4](Update4-UCX/README.md) | UCX analysis, PMP/WFA theory, scuffedQuant, Python MVP | the UCX PRs were not merged |
| [Update 5](Update5-UCX-Review/README.md) | PR review, security audit, middleware hardening | |
| [Update 5-2](Update5-2-Architectures/README.md) | per-architecture scuffedQuant, test_arch harness | two drafts: canonical and `stack-draft/` |
| [Update 6](Update6-StorageTier/README.md) | storage tier for KV offload | spill, coalescing, PMP storage arm now built |
| [Update 7](Update7-TransportLandscape/README.md) | RDT, eRNIC, SoL collectives, libfabric / UCX / DOCA | |
| [Update 8 (draft)](Update8-Libfabric/update8.pdf) | dual pool on libfabric vs libibverbs | provider behavior found while building; experiments E1 to E6 |
| [Drafts/updates-todo](Drafts/updates-todo/README.md) | backlog drafts | keep / merge / drop per draft |

`Drafts/draft1.tex` is the rolling thesis draft.

## Running the work

Every update's README ends with a "Run it" section pointing at the notebook and tests that cover it. The notebooks live in `../notebooks/` and run in `MODE="local"` (smoke) or `MODE="cluster"` (Cerberus and Chimera).

## Notes

`Drafts/updates-todo/` uses its own numbering that does not line up with the main sequence. `updates-todo/Update4-FlashAttention3Blackwell` is a side draft, not a replacement for `Update4-UCX`.
