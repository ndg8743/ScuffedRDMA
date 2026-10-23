# Update 8: libfabric Under the Stack, From Queue Pairs to vLLM

Dated October 2026; draft. Text and build are done. The tables fill from notebooks 01 to 03 and 06 on Cerberus and Chimera, and notebook 08 on one GPU.

The update moves the dual pool onto libfabric and carries it up to vLLM. `libscuffedfabric` gives each traffic class its own endpoint, CQs and, optionally, its own provider and endpoint type. `libscuffedverbs` implements the same C API on raw RC queue pairs, so both stacks run one benchmark source. `FabricBlobChannel` puts a credit-based blob protocol on the pool, and `ScuffedRdmaConnector` moves disaggregated-prefill KV through it inside vLLM. The baseline is the stock stack's own libfabric path, NIXL's `LIBFABRIC` backend. Reading its source shows it selects cxi, efa, tcp or sockets (not verbs) and requires GPUDirect RDMA, so on SoftRoCE and the ConnectX-4 towers it can run over libfabric `tcp` at best. The rest of the October work (telemetry, learned WFA, policy trees, PMP storage arm, NVMe tier, scuffedQuant packing) is summarized around the transport. Experiments E1 to E6 are transport-level, E7 is vLLM prefill and decode on one GPU, E8 is the cross-node TTFT comparison.

## Research

libfabric
- Grun et al., A Brief Introduction to the OpenFabrics Interfaces (HotI 2015). No local copy.
- libfabric man pages: `fi_endpoint(3)`, `fi_cq(3)`, `fi_cntr(3)`, `fi_mr(3)`, `fi_verbs(7)`, `fi_rxm(7)`. https://ofiwg.github.io/libfabric/
- B. Smith, Omni-Path and the Open Fabrics Interfaces (MUG'23). [pdf](../../References/Bookmarks_10-22/MUG23_OmniPath_OFI_Brian_Smith_Cornelis.pdf)
- Bareford et al., OpenFabrics and UCX on ARCHER2 (CUG 2022). [slides](../../References/Bookmarks_10-22/ARCHER2_OFI_vs_UCX_CUG2022.pdf), [repo notes](../../References/Bookmarks_10-22/ARCHER2_OFI_vs_UCX_GitHub.md)
- Papadopoulou, Oden and Balaji, A Performance Study of UCX over InfiniBand (CCGrid 2017): per-operation instruction accounting used in E5. No local copy.

libfabric in LLM serving
- NIXL libfabric plugin, commit `d642316` (2026-10-22): `src/plugins/libfabric/README.md` (libfabric >= 1.21, GPUDirect RDMA required, validated on AWS EFA) and `src/utils/libfabric/libfabric_common.cpp` (`getAvailableNetworkDevices`: `FI_EP_RDM`, `FI_MSG | FI_RMA`, prefers cxi, efa, tcp, sockets). https://github.com/ai-dynamo/nixl/tree/main/src/plugins/libfabric. Background: [GitHub_NIXL_NVIDIA_Inference_Xfer.md](../../References/Bookmarks_Collection/GitHub_NIXL_NVIDIA_Inference_Xfer.md)
- vLLM v0.24.0 `NixlConnector`: `backends` in `kv_connector_extra_config`, default `["UCX"]` (`vllm/distributed/kv_transfer/kv_connector/v1/nixl/base_worker.py`).
- NVIDIA Dynamo, EFA on AWS: selects NIXL's LIBFABRIC backend for EFA. https://docs.nvidia.com/dynamo/latest/kubernetes/installation/rdma-setup/efa-on-aws
- L. Chen, Harnessing 3200 Gbps Network (1): RDMA and EFA: EFA is reached through libfabric. [md](../../References/Bookmarks_Collection/RDMA_EFA_3200Gbps_Network.md)
- Licker, Hu, Zaytsev, Chen, fabric-lib: RDMA Point-to-Point Communication for LLM Systems (arXiv:2510.27656v2, formerly TransferEngine): `WriteImm` + `ImmCounter`, 400 Gbps on ConnectX-7 and EFA. [pdf](../../References/Bookmarks_RDMA/Papers_Papers/fabric_lib_RDMA_Point_to_Point_Communication_for_LLM_Systems_2510.27656.pdf)

vLLM install for the GPU run
- vLLM GPU installation docs: `uv pip install vllm --torch-backend=auto`, CUDA 12.8 / 12.9 / 13.0 builds, WSL note. https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html

## Work done

| Piece | Where | Tested here |
|---|---|---|
| Dual pool on libfabric, `sf_bench` (sig / bw / hol) | `middleware/libscuffedfabric/` | tcp, tcp;ofi_rxm, shm |
| Same API on libibverbs, `sv_bench` | `middleware/libscuffedverbs/` | compiles; needs an RDMA device |
| ctypes binding, `FabricBlobChannel`, `TcpBlobChannel` | `middleware/fabric/` | `tests/test_fabric_pool.py` |
| `ScuffedRdmaConnector`, proxy, loopback | `middleware/vllm_plugin/` | 32 tests; also against vLLM 0.24.0 (signatures, import, end to end through vLLM's base class, CPU) |
| GPU tests: KV layout and codec on CUDA tensors, connector loopback with caches on `cuda:0` | `tests/test_gpu.py` (`pytest -m gpu`) | skip here (no GPU); pass with the device forced to CPU |
| GPU setup: apt libfabric / rdma-core, venv with CUDA torch + vLLM (`uv --torch-backend`), builds, tests, Jupyter kernel | `scripts/local_gpu/setup_gpu_env.sh` | `--dry-run` and the no-driver path |
| Launcher: `CONNECTOR=nixl-libfabric` (NIXL `LIBFABRIC` backend, `FI_PROVIDER` from `NIXL_FI_PROVIDER`, default tcp), per-side NIXL ports | `benchmarks/vllm_disagg/launch.sh` | `launch.sh print` |
| Notebook 08: single-GPU end to end | `notebooks/08_local_gpu.ipynb` | runs clean in local mode |
| Notebook 06: adds the NIXL `LIBFABRIC` setup | `notebooks/06_vllm_disagg_ttft.ipynb` | runs clean in local mode |
| Text | `update8.tex`, `update8.pdf` | |

Telemetry, learned WFA, policy trees, PMP storage arm, NVMe tier and the scuffedQuant packing fix are tracked in the READMEs of the updates that proposed them (2, 4, 6, 7) and summarized in Section 6 of the tex.

## Next steps as written, status today

| Next step | Status |
|---|---|
| 1. Notebook 08 on the desktop GPU, fill E7 | gpu: run `setup_gpu_env.sh`, then the notebook with `MODE = "gpu"` |
| 2. Notebooks 00 to 03 on Cerberus and Chimera, then the towers; fill E1 to E5 | cluster |
| 3. Notebook 06 across nodes for E8, including the NIXL `LIBFABRIC` row | cluster |
| 4. Make hot RDM + cold MSG the default if it wins E4; route NVMe and GPFS spill through the same domain | open, depends on E4 |
| 5. Train the learned WFA on telemetry dumps labeled by measured latency | open, depends on 2 and 3 |

## Run it

- [`notebooks/08_local_gpu.ipynb`](../../notebooks/08_local_gpu.ipynb): E7. On the GPU machine: `bash scripts/local_gpu/setup_gpu_env.sh`, then `MODE = "gpu"`. Set `NIXL_BACKENDS = "UCX,LIBFABRIC"` after `setup_gpu_env.sh --nixl` for the NIXL rows.
- [`notebooks/01_hol_blocking.ipynb`](../../notebooks/01_hol_blocking.ipynb), [`02_completion_signaling`](../../notebooks/02_completion_signaling.ipynb), [`03_libfabric_vs_libibverbs`](../../notebooks/03_libfabric_vs_libibverbs.ipynb): E1 to E6.
- [`notebooks/06_vllm_disagg_ttft.ipynb`](../../notebooks/06_vllm_disagg_ttft.ipynb): E8. `CONNECTOR=nixl-libfabric bash benchmarks/vllm_disagg/launch.sh print` shows the NIXL libfabric commands.
- Tests: `python3 -m pytest -q`; `pytest -m gpu` on a GPU machine; `VLLM_SRC=/path/to/vllm` to check signatures against another vLLM.

## Corrections

- The 8 µs cross-node figure and the 4x-vs-FP16 compression ratio are withdrawn in the tex (Section 7), with the reasons. The same corrections are in the top-level README.
