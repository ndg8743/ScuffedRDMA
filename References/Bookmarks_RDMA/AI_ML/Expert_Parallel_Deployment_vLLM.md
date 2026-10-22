# Expert Parallel Deployment - vLLM

- **Source:** https://docs.vllm.ai/en/latest/serving/expert_parallel_deployment/#prerequisites
- **Bookmarked:** 2026-07-26 (Chrome, Bookmarks bar > RDMA > AI & ML)
- **Retrieved:** 2026-10-22


---

# Expert Parallel Deployment[¶](#expert-parallel-deployment)

vLLM supports Expert Parallelism (EP), which allows experts in Mixture-of-Experts (MoE) models to be deployed on separate GPUs, increasing locality, efficiency, and throughput overall.

EP is typically coupled with Data Parallelism (DP). While DP can be used independently of EP, EP is more efficient when used in conjunction with DP. You can read more about data parallelism [here](../data_parallel_deployment/).

## Prerequisites[¶](#prerequisites)

Before using EP, you need to install the necessary dependencies. We are actively working on making this easier in the future:

1. **Install DeepEP**: Set up host environment following vLLM's guide for EP kernels  [here](https://github.com/vllm-project/vllm/tree/main/tools/ep_kernels).
2. **Install DeepGEMM library**: Follow the [official instructions](https://github.com/deepseek-ai/DeepGEMM#installation).
3. **For disaggregated serving**: Install `gdrcopy` by running the  [`install_gdrcopy.sh`](https://github.com/vllm-project/vllm/blob/main/tools/install_gdrcopy.sh) script (e.g., `install_gdrcopy.sh "${GDRCOPY_OS_VERSION}" "12.8" "x64"`). You can find available OS versions [here](https://developer.download.nvidia.com/compute/redist/gdrcopy/CUDA%2012.8/).

NCCL version (CUDA 13+)

The `deepep_v2` backend requires NCCL >= 2.30.4. PyTorch ships an older
NCCL, so you must upgrade it before building or running DeepEP. See the
 [EP kernels guide](https://github.com/vllm-project/vllm/tree/main/tools/ep_kernels) for instructions.

### Backend Selection Guide[¶](#backend-selection-guide)

vLLM provides multiple communication backends for EP. Use `--all2all-backend` to select one:

| Backend | Use Case | Features | Best For | 
|---|---|---|---|
| `allgather_reducescatter` | Default backend | Standard all2all using allgather/reducescatter primitives | General purpose, works with any EP+DP configuration | 
| `deepep_high_throughput` | Multi-node prefill | Grouped GEMM with continuous layout, optimized for prefill | Prefill-dominated workloads, high-throughput scenarios | 
| `deepep_low_latency` | Multi-node decode | CUDA graph support, masked layout, optimized for decode | Decode-dominated workloads, low-latency scenarios | 
| `flashinfer_nvlink_one_sided` | MNNVL systems | FlashInfer's one-sided A2A strategy for multi-node NVLink | High-throughput workloads | 
| `passthrough` | Any | Internal, not accepted on the CLI: bound automatically for MoE backends that dispatch and combine themselves, so no all-to-all runs in the framework | `--moe-backend flashinfer_moe_ep_*` (FlashInfer MoE-EP megakernels) | 
| `flashinfer_nvlink_two_sided` | MNNVL systems | FlashInfer's two-sided A2A strategy for multi-node NVLink | Systems with NVLink across nodes | 

## Single Node Deployment[¶](#single-node-deployment)

### Configuration[¶](#configuration)

Enable EP by setting the `--enable-expert-parallel` flag. The EP size is automatically calculated as:

Where:

- `TP_SIZE`: Tensor parallel size
- `DP_SIZE`: Data parallel size
- `EP_SIZE`: Expert parallel size (computed automatically)

### Layer Behavior with EP Enabled[¶](#layer-behavior-with-ep-enabled)

When EP is enabled, different layers in MoE models behave differently:

| Layer Type | Behavior | Parallelism Used | 
|---|---|---|
| **Expert (MoE) Layers** | Sharded across all EP ranks | Expert Parallel (EP) of size `TP × DP` | 
| **Attention Layers** | Behavior depends on TP size | See below | 

**Attention layer parallelism:**

- **When `TP = 1`**: Attention weights are **replicated** across all DP ranks (data parallelism)
- **When `TP > 1`**: Attention weights are **sharded** using tensor parallelism across TP ranks within each DP group

For example, with `TP=2, DP=4` (8 GPUs total):

- Expert layers form an EP group of size 8, with experts distributed across all GPUs
- Attention layers use TP=2 within each of the 4 DP groups

Key Difference from Data Parallel Deployment

Without `--enable-expert-parallel`, MoE layers would use tensor parallelism (forming a TP group of size `TP × DP`), similar to dense models. With EP enabled, expert layers switch to expert parallelism, which can provide better efficiency and locality for MoE models.

### Example Command[¶](#example-command)

The following command serves a `DeepSeek-V3-0324` model with 1-way tensor parallel, 8-way (attention) data parallel, and 8-way expert parallel. The attention weights are replicated across all GPUs, while the expert weights are split across GPUs. It will work on a H200 (or H20) node with 8 GPUs. For H100, you can try to serve a smaller model or refer to the multi-node deployment section.

## Multi-Node Deployment[¶](#multi-node-deployment)

For multi-node deployment, use the DeepEP communication kernel with one of two modes (see [Backend Selection Guide](#backend-selection-guide) above).

### Deployment Steps[¶](#deployment-steps)

1. **Run one command per node** - Each node requires its own launch command
2. **Configure networking** - Ensure proper IP addresses and port configurations
3. **Set node roles** - First node handles requests, additional nodes run in headless mode

### Example: 2-Node Deployment[¶](#example-2-node-deployment)

The following example deploys `DeepSeek-V3-0324` across 2 nodes using `deepep_low_latency` mode:

### Key Configuration Notes[¶](#key-configuration-notes)

- **Headless mode**: Secondary nodes run with `--headless` flag, meaning all client requests are handled by the primary node
- **Rank calculation**: `--data-parallel-start-rank` should equal the cumulative local DP size of previous nodes
- **Load scaling**: Adjust `--api-server-count` on the primary node to handle higher request loads

### Network Configuration[¶](#network-configuration)

InfiniBand Clusters

On InfiniBand networked clusters, set this environment variable to prevent initialization hangs:

This ensures torch distributed group discovery uses Ethernet instead of InfiniBand for initial setup.
## Expert Parallel Load Balancer (EPLB)[¶](#expert-parallel-load-balancer-eplb)

While MoE models are typically trained so that each expert receives a similar number of tokens, in practice the distribution of tokens across experts can be highly skewed. vLLM provides an Expert Parallel Load Balancer (EPLB) to redistribute expert mappings across EP ranks, evening the load across experts.

### Configuration[¶](#configuration_1)

Enable EPLB with the `--enable-eplb` flag.

When enabled, vLLM collects load statistics with every forward pass and periodically rebalances expert distribution.

### EPLB Parameters[¶](#eplb-parameters)

Configure EPLB with the `--eplb-config` argument, which accepts a JSON string. The available keys and their descriptions are:

| Parameter | Description | Default | 
|---|---|---|
| `window_size` | Number of engine steps to track for rebalancing decisions | 1000 | 
| `step_interval` | Frequency of rebalancing (every N engine steps) | 3000 | 
| `log_balancedness` | Log balancedness metrics (avg tokens per expert ÷ max tokens per expert) | `false` | 
| `num_redundant_experts` | Additional global experts per EP rank beyond equal distribution | `0` | 
| `use_async` | Use non-blocking EPLB for reduced latency overhead | `true` | 
| `policy` | The policy type for expert parallel load balancing | `"default"` | 
| `communicator` | Backend for expert weight transfers: `"torch_nccl"`, `"torch_gloo"`, `"pynccl"`, `"nixl"`,  or `null` (auto) | `null` | 

For example:

## Prefer individual arguments instead of JSON?

### Expert Distribution Formula[¶](#expert-distribution-formula)

- **Default**: Each EP rank has `NUM_TOTAL_EXPERTS ÷ NUM_EP_RANKS` experts
- **With redundancy**: Each EP rank has `(NUM_TOTAL_EXPERTS + NUM_REDUNDANT_EXPERTS) ÷ NUM_EP_RANKS` experts

### Memory Footprint Overhead[¶](#memory-footprint-overhead)

EPLB uses redundant experts that need to fit in GPU memory. This means that EPLB may not be a good fit for memory constrained environments or when KV cache space is at a premium.

This overhead equals `NUM_MOE_LAYERS * BYTES_PER_EXPERT * (NUM_TOTAL_EXPERTS + NUM_REDUNDANT_EXPERTS) ÷ NUM_EP_RANKS`.
For DeepSeekV3, this is approximately `2.4 GB` for one redundant expert per EP rank.

### Example Command[¶](#example-command_1)

Single node deployment with EPLB enabled:

For multi-node deployment, add these EPLB flags to each node's command. We recommend setting `--eplb-config '{"num_redundant_experts":32}'` to 32 in large scale use cases so the most popular experts are always available.

## Advanced Configuration[¶](#advanced-configuration)

### Performance Optimization[¶](#performance-optimization)

- **DeepEP kernels**: The `high_throughput` and `low_latency` kernels are optimized for disaggregated serving and may show poor performance for mixed workloads
- **Dual Batch Overlap**: Use `--enable-dbo` to overlap all-to-all communication with compute. See [Dual Batch Overlap](../../design/dbo/) for more details.
- **Async scheduling (experimental)**: Try `--async-scheduling` to overlap scheduling with model execution.

### Troubleshooting[¶](#troubleshooting)

- **`non-zero status: 7 cannot register cq buf`**: When using Infiniband/RoCE, make sure host VM and pods show `ulimit -l` "unlimited".
- **`init failed for transport: IBGDA`**: The InfiniBand GDA kernel modules are missing. Run `tools/ep_kernels/configure_system_drivers.sh` on each GPU node and reboot. Also fixes error `NVSHMEM API called before NVSHMEM initialization has completed`.
- **NVSHMEM peer disconnect**: Usually a networking misconfiguration. If deploying via Kubernetes, verify that every pod runs with `hostNetwork: true`, `securityContext.privileged: true` to access Infiniband.

### Benchmarking[¶](#benchmarking)

- Use simulator flags `VLLM_MOE_ROUTING_SIMULATION_STRATEGY=uniform_random` and `VLLM_RANDOMIZE_DP_DUMMY_INPUTS=1` so token routing is balanced across EP ranks.

## Disaggregated Serving (Prefill/Decode Split)[¶](#disaggregated-serving-prefilldecode-split)

For production deployments requiring strict SLA guarantees for time-to-first-token and inter-token latency, disaggregated serving allows independent scaling of prefill and decode operations.

### Architecture Overview[¶](#architecture-overview)

- **Prefill Instance**: Uses `deepep_high_throughput` backend for optimal prefill performance
- **Decode Instance**: Uses `deepep_low_latency` backend for minimal decode latency
- **KV Cache Transfer**: Connects instances via NIXL or other KV connectors

### Setup Steps[¶](#setup-steps)

1. **Install gdrcopy/ucx/nixl**: For maximum performance, run the  [install\_gdrcopy.sh](https://github.com/vllm-project/vllm/blob/main/tools/install_gdrcopy.sh) script to install `gdrcopy` (e.g., `install_gdrcopy.sh "${GDRCOPY_OS_VERSION}" "12.8" "x64"`). You can find available OS versions [here](https://developer.download.nvidia.com/compute/redist/gdrcopy/CUDA%2012.8/). If `gdrcopy` is not installed, things will still work with a plain `pip install nixl`, just with lower performance. `nixl` and `ucx` are installed as dependencies via pip. For non-cuda platform to install nixl with non-cuda UCX build, run the  [install\_nixl\_from\_source\_ubuntu.py](https://github.com/vllm-project/vllm/blob/main/tools/install_nixl_from_source_ubuntu.py) script.
2. **Configure Both Instances**: Add this flag to both prefill and decode instances `--kv-transfer-config '{"kv_connector":"NixlConnector","kv_role":"kv_both"}`. Noted, you may also specify one or multiple NIXL\_Backend. Such as: `--kv-transfer-config '{"kv_connector":"NixlConnector","kv_role":"kv_both", "kv_connector_extra_config":{"backends":["UCX", "GDS"]}}'`
3. **Client Orchestration**: Use the client-side script below to coordinate prefill/decode operations. We are actively working on routing solutions.

### Client Orchestration Example[¶](#client-orchestration-example)

### Benchmarking[¶](#benchmarking_1)

- To simulate the decode deployment of disaggregated serving, pass `--kv-transfer-config '{"kv_connector":"DecodeBenchConnector","kv_role":"kv_both"}'` to the `vllm serve` invocation. The connector populates KV cache with random values so decode can be profiled in isolation. Add `"kv_connector_extra_config":{"startup_fill":true}` to fill the whole KV cache once at startup instead of in the decode steps that admit new requests (see the connector docstring for its limitations).
- **CUDAGraph capture**: Use `--compilation_config '{"cudagraph_mode": "FULL_DECODE_ONLY"}'` to enable CUDA graph capture for decode only and save KV cache.