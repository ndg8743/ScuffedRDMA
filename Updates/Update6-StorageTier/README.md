# Update 6: Storage-Tier Integration for KV Cache Offloading

Dated April 2026. First version `c17b8ba` (2026-04-16) on main; revised in `0eea051` (2026-04-17, "add GPFS Ansible + sandook deployment paths, measured NVMe baseline") on `feat/update-5-2`, which was merged into main on 2026-10-22 (`f8aa1c2`). The merged tex is the revised one.

This update looks one layer below the network: when the KV cache no longer fits in GPU memory, evicted blocks should be retrievable from storage instead of recomputed. It adopts Vincent Hsu's four-tier KV hierarchy (G1 GPU HBM, G2 CPU DRAM, G3 local NVMe, G4 shared network storage), walks through GPFS block size and subblock tradeoffs for KV-sized writes, surveys sandook (aggregated NVMe with read/write isolation) and WEKA's Augmented Memory Grid, and extends the WFA from a two-way decision (hot QP vs cold QP) to three ways (hot QP, cold QP, storage spill), with the PMP controller allocating between network and storage paths. The revision adds a measured NVMe spill baseline and two deployment paths: IBM's Ansible roles for a two-node Storage Scale cluster and the sandook QuickStart.

## Research

KV tiering and IBM Storage Scale
- V. Hsu, Accelerating NVIDIA Dynamo with IBM Storage Scale and BlueField-4: the four-tier hierarchy. [Accelerating_NVIDIA_Dynamo_...md](../../References/Bookmarks_RDMA/thesis_refs/Accelerating_NVIDIA_Dynamo_with_IBM_Storage_Scale_and_BlueField_4_Infe.md)
- A. Hsu et al., Rethinking LLM Inference Economics (llm-d + LMCache + Storage Scale): the 8 GB/s sustained comparison point and >10x TTFT at high reuse, on their H100 hardware. [Rethinking_LLM_Inference_Economics_...md](../../References/Bookmarks_RDMA/thesis_refs/Rethinking_LLM_Inference_Economics_KV_Cache_Reuse_with_llm_d_LMCache_a.md)
- IBM Research, Accelerating AI inference with IBM Storage Scale. [IBM_Accelerating_AI_Inference_Storage_Scale.md](../../References/Bookmarks_Collection/IBM_Accelerating_AI_Inference_Storage_Scale.md)
- IBM, Storage Scale install infra (Ansible roles). https://github.com/IBM/ibm-spectrum-scale-install-infra (no local copy)
- Storage Scale RDMA background: [Improving_Spectrum_Scale_RDMA_SSSD21.pdf](../../References/Bookmarks_Collection/Improving_Spectrum_Scale_RDMA_SSSD21.pdf), [RDMA_Tuning_-_IBM_Storage_Scale.md](../../References/Bookmarks_Collection/RDMA_Tuning_-_IBM_Storage_Scale.md), [GPUDirect_Storage_IBM_Storage_Scale.md](../../References/Bookmarks_Collection/GPUDirect_Storage_IBM_Storage_Scale.md)

Commodity and vendor storage
- Chaudhry et al., sandook (NSDI 2026): aggregated NVMe block device with dynamic read/write isolation; its control-plane/data-plane split mirrors WFA + PMP. [sandook_...md](../../References/Bookmarks_RDMA/thesis_refs/sandook_Aggregated_NVMe_Block_Device_with_Read_Write_Workload_Isolatio.md), https://github.com/mit-sandook/sandook
- WEKA Augmented Memory Grid / NeuralMesh: the high-end comparison (7.5M read IOPS, 41x TTFT on 128K sequences, their numbers). [WEKA_Augmented_Memory_Grid_NeuralMesh.md](../../References/Bookmarks_Collection/WEKA_Augmented_Memory_Grid_NeuralMesh.md), [NVIDIA_Shared_KV_Cache_WEKA_Roadmap.md](../../References/Bookmarks_Collection/NVIDIA_Shared_KV_Cache_WEKA_Roadmap.md)
- NVIDIA BlueField-4 inference context memory storage platform: DPU offload of coalescing and the storage control plane. No local copy.
- LMCache (arXiv:2510.09665). [LMCache.md](../../References/Bookmarks_RDMA/AI_ML_LLM_Inference/LMCache.md)
- PagedAttention: 16-token KV blocks. [PagedAttention_Efficient_LLM_Serving_2309.06180.pdf](../../References/Bookmarks_Collection/PagedAttention_Efficient_LLM_Serving_2309.06180.pdf)

## Work done

- Measured NVMe spill on Chimera with `benchmarks/test_arch/stack-draft/bench_storage_spill.py` (`ad4443e`, 2026-04-16). Results in `benchmarks/results/test_arch/chimera_storage_spill.json`:

| Coalesce | Payload | Write (MB/s) | Read (MB/s) |
|---|---|---|---|
| 1 | 1,568 KB | 662 | 1,731 |
| 10 | 15,680 KB | 731 | 2,149 |
| 20 | 31,360 KB | 803 | 2,188 |
| 50 | 78,400 KB | 827 | 1,104 |

  Writes are `write` + `fsync` per file; reads follow `posix_fadvise(DONTNEED)`. Each number is a median over `--writes` files (default 50; the JSON does not record the value used).
- No middleware code came out of this update in April. The three-way classification and storage-pressure term were design only.

## Next steps as written, status today

| Next step | Status | Evidence |
|---|---|---|
| 1. Two-node GPFS cluster on Chimera/Cerberus via the Ansible role, mount `/gpfs/scuffedrdma`, rerun spill vs 803 MB/s | open | No deployment record. |
| 2. Build sandook (controller on Cerberus, ublk agent on Chimera), benchmark aggregated throughput and tail latency | open | |
| 3. KV spill/retrieve in `middleware/rdma_tensor_cache/` with async I/O, gated by the WFA, routing a fraction of cold traffic to storage | built (Oct 2026), cluster run pending | `middleware/rdma_tensor_cache/storage_tier.py`, notebook 07. |
| 4. Storage-pressure term in the PMP controller based on GPU memory headroom | built (Oct 2026), cluster run pending | `PMPController.pressure()` in `middleware/rdma_tensor_cache/pmp_controller.py`, `tests/test_pmp_controller.py`. |

## Run it

- [`notebooks/07_storage_tier.ipynb`](../../notebooks/07_storage_tier.ipynb): coalescing sweep and spill/retrieve through `storage_tier.py`, plus the PMP storage-pressure behavior. Point it at a path you know is NVMe (not `/tmp` if that is tmpfs) and record the device.
- Tests: `tests/test_pmp_controller.py` and the storage-tier tests added with `storage_tier.py`.

## Corrections

- **Compression figures do not match the bytes written.** The text says scuffedQuant 3-bit is "~5x" (256 KB block to ~50 KB) and later "6.4x". The spill benchmark's own serialized block is 1,568 KB for an FP16 block of 2,048 KB (8,192 rows x 128 dims): `uint8` indices, one byte per QJL sign, no residual norms, so about 1.3x. Bit-packed at head_dim 128, 3 bits plus norms is about 2.9x vs FP16 with a 256-bit QJL sketch and 4x with a 64-bit one; "~5x" is only reachable vs FP32. Pick one serialization and quote its measured size.
- **The GPFS alignment sentence is inconsistent.** "30 compressed blocks fit in 30 GPFS blocks, each below the subblock boundary": the measured blocks are 1.5 MB, larger than a 1 MB GPFS block and far above a 32 KB subblock.
- **"Measured on Chimera's NVMe".** The benchmark writes into `tempfile.TemporaryDirectory()`, i.e. `/tmp`. Whether that is NVMe or tmpfs on Chimera was not recorded. The read drop at 50 blocks is attributed to page cache pressure without evidence.
- **GDS dependency.** "GDS requires `nvidia-peermem`": GPUDirect Storage depends on the `nvidia-fs` driver (with MOFED for remote storage over RDMA); `nvidia-peermem` is the GPUDirect RDMA module. Neither works on SoftRoCE or GeForce cards, so the conclusion (Tower 2 only) stands.
- "Chimera/Cerberus run Ubuntu 22 ... kernel 6.8" disagrees with Update 4's infrastructure table (Ubuntu 24.04 on Chimera).
- "Both have been confirmed to work on commodity hardware" means the upstream projects document it; neither path has been run on this testbed.
- The introduction calls the UCX PRs "six upstream UCX patches". None were merged.
