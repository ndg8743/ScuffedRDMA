# 3. Where industry stands

[← back to the README section](../../README.md#3-where-industry-stands)

![Industry landscape](../media/03_landscape.gif)

This section makes claims about other systems rather than mathematical claims, so the "proof" for each is the evidence: what the source says, where to check it, and what follows for this thesis. Each claim is kept to what the source supports.

---

## The stack

From top to bottom, a disaggregated-serving deployment is:

1. **Serving engine**: vLLM, SGLang, or an orchestration layer such as Ray (Ray Direct Transport moves tensors between actors).
2. **KV connector**: the plug-in that moves KV between prefill and decode: NIXL, Mooncake, LMCache, or ours (`ScuffedRdmaConnector`).
3. **Transport stack**: UCX, libfabric (OFI) or NVIDIA DOCA.
4. **Verbs**: `libibverbs` / rdma-core, the kernel-bypass interface every RDMA NIC exposes.
5. **NIC**: ConnectX (InfiniBand/RoCE), AWS EFA, HPE Slingshot (cxi), or SoftRoCE (RDMA implemented in the Linux kernel over a plain Ethernet NIC).

## Problem 1: the tools are built for bulk

**Claim.** RDT, Mooncake, NIXL and LMCache optimize large homogeneous transfers (weight synchronization, KV hand-off). None of them separates small latency-critical messages from bulk on a shared link.

**Evidence.** Update 7 read each system's design and benchmarks:

- RDT's optimizations (register once and send views as offsets, ahead-of-time registration, targeted receive, pooling small tensors) all serve barrier-style weight sync, where nothing competes for the link while it runs. Its results are on NVLink and InfiniBand-class fabrics.
- NIXL, Mooncake and LMCache move KV for one request at a time through one path.

**What follows.** Nobody has measured what happens to small decode-path messages when bulk KV shares a commodity link. That is the gap (README section 2).

## Problem 2: the stock libfabric path is EFA-shaped

**Claim.** NIXL's `LIBFABRIC` backend, which vLLM can select, will not use the verbs provider, and it requires GPUDirect RDMA.

**Evidence** (NIXL repository, commit `d642316`, 22 Oct 2026):

- `src/utils/libfabric/libfabric_common.cpp`, `getAvailableNetworkDevices()`: asks `fi_getinfo` for `FI_EP_RDM` endpoints with `FI_MSG | FI_RMA`, groups results by provider, then returns the first match in the order `cxi`, `efa`, `tcp`, `sockets`. There is no branch for `verbs` (whose RDM form is reported as `verbs;ofi_rxm`).
- `src/plugins/libfabric/README.md`: lists libfabric ≥ 1.21 and "GDR (GPU Direct RDMA) support is currently required", and AWS EFA as the only validated hardware.
- vLLM v0.24.0 `nixl/base_worker.py` reads the backend list from `kv_connector_extra_config["backends"]`, default `["UCX"]`.

**What follows.** On SoftRoCE servers, or ConnectX-4 servers without the peer-memory kernel module, the stock libfabric path can only fall back to libfabric `tcp`, or fail to start. That is why the thesis builds its own libfabric layer over the verbs provider, and why the comparison (Update 8, E8) includes NIXL-libfabric as a baseline rather than assuming it works here.

## Problem 3: library side effects

**Claim.** In production disaggregated vLLM, a transport library caused a memory leak large enough to crash servers.

**Evidence.** Mistral's engineering write-up ("Debugging a memory leak in vLLM"): memory grew about 400 MB per minute. They traced it with Heaptrack and BPFtrace to UCX, which NIXL uses. UCX patches the global offset table to intercept every `mmap` for its registration cache and did not release regions promptly on `munmap`. The workaround was `UCX_MEM_MMAP_HOOK_MODE=none`, and a fix was merged into vLLM.

**What follows.** Library behavior below the connector matters in production, and is hard to see. The thesis keeps the data path on code it controls (`libscuffedfabric`, `libscuffedverbs`) and records transport events in telemetry.

## Problem 4: silent fallback

**Claim.** A mature RDMA user, IBM Storage Scale (GPFS), has shipped defects where RDMA failed and traffic silently moved to TCP.

**Evidence.** IBM APAR IV61625: after a QP went to the error state, clients could not reconnect, the server kept the dead connection, and I/O fell back to TCP with the corresponding slowdown. Update 7 lists this with the other published GPFS RDMA defects (data integrity, write flush, quorum loss).

**What follows.** A fallback must be visible. The connector falls back from libfabric to TCP when it has to, and records a `tcp_fallback` event in telemetry, so a run that silently fell back cannot be mistaken for an RDMA result.

## Problem 5: unchecked completions

**Claim.** It is easy to publish wrong RDMA latency numbers by not checking completion status. This project did.

**Evidence.** The Update 4 Python pool timed writes until a completion appeared but did not check `wc.status`. Failed or flushed writes produce completions too, quickly, so they counted as fast transfers. The reported 8 µs cross-node figure included 8 MB writes "completing" in about 8 µs, which a 10 Gb/s link cannot do (8 MB takes at least 6.7 ms). The pool now raises on a bad status (`check_completion` in `dual_qp_pool.py`), and the native libraries check every completion.

**What follows.** Every latency number in the thesis comes from a harness that checks completion status. The 8 µs figure is withdrawn.

## Where the thesis sits

The cell none of the above covers: **mixed hot/cold traffic, on commodity 10 GbE with SoftRoCE, without GPUDirect, with KV staged through host memory.** The contribution is the classification and scheduling of that mixed traffic, not a faster bulk path.

## References

1. Update 7 (`Updates/Update7-TransportLandscape/update7.pdf`). *Used for: problems 1 and 4 (the reading of RDT, NIXL, Mooncake, LMCache and the GPFS defect record).*
2. Anyscale. "RDT: Ray Direct Transport, fast, easy weight syncing for RL," 2026. [anyscale.com/blog](https://www.anyscale.com/blog/rdt-ray-direct-transport-fast-easy-weight-syncing-for-rl-reinforcement-learning). *Problem 1.*
3. R. Qin et al. "Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving." [arXiv:2407.00079](https://arxiv.org/abs/2407.00079), 2024. *Problem 1.*
4. LMCache. "LMCache + vLLM v1 + NIXL." [blog.lmcache.ai](https://blog.lmcache.ai/2025-04-11-lmcache-vllmv1-nixl/), 2025. *Problem 1.*
5. NVIDIA. NIXL libfabric plugin: `src/plugins/libfabric/README.md` and `src/utils/libfabric/libfabric_common.cpp` (`getAvailableNetworkDevices`), commit `d642316`, 22 Oct 2026. [github.com/ai-dynamo/nixl](https://github.com/ai-dynamo/nixl/tree/d642316/src/plugins/libfabric). *Problem 2.*
6. vLLM v0.24.0. `NixlConnector` worker, [`vllm/distributed/kv_transfer/kv_connector/v1/nixl/base_worker.py`](https://github.com/vllm-project/vllm/blob/v0.24.0/vllm/distributed/kv_transfer/kv_connector/v1/nixl/base_worker.py). *Problem 2: backend selection, default `["UCX"]`.*
7. Mistral AI. "Debugging a memory leak in vLLM." [mistral.ai/news](https://mistral.ai/news/debugging-memory-leak-in-vllm). *Problem 3.*
8. IBM. "APAR IV61625: RDMA reconnection problem." [ibm.com/support](https://www.ibm.com/support/pages/apar/IV61625). *Problem 4.*
9. Update 4 (`Updates/Update4-UCX/`) and `middleware/rdma_tensor_cache/dual_qp_pool.py` (`check_completion`). *Problem 5.*
