# Update 5: UCX Pull Request Review, External Validation, Middleware Hardening

Dated 2026-04-12; committed with the code in `9570f48` (2026-04-11). A post-submission follow-up to Update 4. It walks through the diff of each of the six UCX pull requests (#11304 to #11309), reads the libmesh-rdma project and its r/HPC thread as an outside account of the same direct-connect RoCE bootstrap problem PR #11307 targets, contrasts Apple MLX's CPU-mediated JACCL backend and Pure Storage's TurboQuant + FlashBlade deployment, records CI flakiness on the UCX RoCE test node, and documents a security audit triggered by a memory-safety bug found in libmesh-rdma. Four unbounded-length reads in the middleware were fixed and three libmesh-rdma modules were ported to Python (GID discovery, binary QP bootstrap, QP state machine with retry).

## Research

UCX and the bootstrap problem
- openucx/ucx PRs #11304 to #11309 and the issues they reference (#4430 and others). GitHub only.
- autoscriptlabs/libmesh-rdma: RC-over-TCP-bootstrap RDMA plus a 55-function MPI subset for switchless consumer clusters; source of the ported bootstrap code. https://github.com/autoscriptlabs/libmesh-rdma (no local copy)
- r/HPC, "Custom MPI over RDMA for direct-connect RoCE": the 77 GB/s, 11.6 us RTT existence proof on ConnectX-7 once UD/ARP is out of the bootstrap. The 77 GB/s and 11.6 us figures are the thread author's, on their hardware. No local copy (Reddit blocks automated capture).

Contrasting designs
- ml-explore/mlx PR #3094 (JACCL distributed backend): tightly coupled CPU-mediated collectives; the opposite pole from async CQ with priorities. GitHub only.
- Pure Storage, Up to 10x faster KV cache restore: TurboQuant + FlashBlade, RDMA plus GDS into GPU memory. [TurboQuant_KV_Cache_FlashBlade.md](../../References/Bookmarks_Collection/TurboQuant_KV_Cache_FlashBlade.md)
- NVIDIA HPC-X. [UCX_Framework_Library_HPC-X.md](../../References/Bookmarks_Collection/UCX_Framework_Library_HPC-X.md)
- Introl, GPU virtualization in multi-tenant environments (context for Configurations D and E). [GPU_Virtualization_Introl_Blog.pdf](../../References/Bookmarks_Collection/GPU_Virtualization_Introl_Blog.pdf)

## Work done

`9570f48` (2026-04-11):
- `middleware/rdma_gid_discovery.py`: scans the GID table for IPv4-mapped GIDs instead of a hardcoded `gid_index = 0`.
- `middleware/rdma_bootstrap.py`: fixed 64-byte network-order `QpInfo` handshake over TCP, `_recv_exact` for partial reads. Closes the unbounded JSON `recv` (finding 1).
- `middleware/rdma_qp_state_machine.py`: `QueuePair` with `to_init/to_rtr/to_rts/verify_rts/close`, exponential backoff retries, GRH fields set on `AHAttr` directly (no AH object, so no ARP), forced RESET before close to avoid the rxe zombie state.
- `middleware/roce_transport.py` retargeted onto the three modules.
- Bounds checks: `MAX_KV_LAYER_BYTES = 500 MB` in `vllm_connector.py` (finding 2), `MAX_SPARSE_NNZ` / `MAX_SPARSE_DIM` in `sae_steering.py` (finding 3), `MAX_RDMA_READ_BYTES` in `transport_tcp_sim.py` (finding 4; that file was later deleted in `022b895`).
- `middleware/tests/test_rdma_bootstrap.py`: 17 tests, 16 pure Python plus one rxe smoke test. In this workspace (no RDMA device) the suite reports 15 passed, 2 skipped.

## Next steps as written, status today

| Next step | Status | Evidence |
|---|---|---|
| 1. Multi-threaded concurrent workload on SoftRoCE to show HOL removal (from Update 4) | built (Oct 2026), cluster run pending | Native mixed-traffic benches in `middleware/libscuffedverbs/` and `middleware/libscuffedfabric/`, notebook 01. No testbed result yet. |
| 2. vLLM KvConnector integration (from Update 4) | built (Oct 2026), cluster run pending | `middleware/vllm_plugin/`, notebook 06. |
| 3. Port the data path from pyverbs to C++ or Rust (from Update 4) | partial | C implementations listed above; NCCL net plugin `middleware/nccl_plugin/`. |
| 4. Confirm PR #11307 on a real direct-connect RoCE ring | open | No ConnectX ring available. Moot unless the PR moves. |
| 5. Decide whether to reopen PR #11304 | open, undecided | Still closed as of 2026-10-22. |
| 6. Decide whether to disclose the `mesh_mpi_pt2pt.c` bug to libmesh-rdma | open | No record of disclosure in the repo. |
| 7. Full `QueuePair` RTR loopback test on ConnectX | open | Server 4 has ConnectX-4; the test still skips on rxe. |

Upstream status: none of the six UCX PRs were merged. As of 2026-10-22, #11305 (adaptive TX CQ moderation), #11306 (eager inline with CUDA MDs present), #11307 (TCP as fallback wireup for RC/DC), #11308 (bandwidth estimate in `ucp_ep_query`) and #11309 (symmetric traffic class in the IB address) are open with review required; #11304 (calculated rndv threshold for `ucp_tag_send_nbr`) is closed. The PR review in this update documents the patches; it is not evidence that upstream UCX behaves differently.

## Run it

- [`notebooks/00_environment_check.ipynb`](../../notebooks/00_environment_check.ipynb): runs `middleware/tests/test_rdma_bootstrap.py` with the rxe0 smoke test enabled on server 1 / server 2.
- The C pools use the same switchless pattern (GID from the table, RC QP to RTR with the GRH set directly): `middleware/libscuffedverbs/`. The libfabric pool in `middleware/libscuffedfabric/` uses provider address exchange instead.

## Corrections

- The tex says attribution for the libmesh-rdma ports "is in a `LICENSE-THIRD-PARTY` file at the middleware root". That file and the "Portions adapted from autoscriptlabs/libmesh-rdma (MIT)" headers were removed in the cleanup commit `b23b058` (2026-04-16). MIT requires the copyright and permission notice to stay with substantial portions of the code, so the notice should be restored (`git show 9570f48:middleware/LICENSE-THIRD-PARTY`).
- The recap describes the PRs as fixes "landed" on branches. They landed on the `ndg8743/ucx` fork only.
- "Update 4 stays as-is": Update 4 still calls the PRs "contributions". See the Update 4 README.
