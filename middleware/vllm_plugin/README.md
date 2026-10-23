# ScuffedRdmaConnector (vLLM KV connector)

Out-of-tree vLLM V1 KV connector for disaggregated prefill (Cerberus, 2x RTX 5090) and decode (Chimera, 3x RTX 3090). Replaces `NixlConnector` / `P2pNcclConnector`: KV moves through the `BlobChannel` interface (`middleware/fabric/channel.py`), so the same connector runs over the libfabric hot/cold pool (`transport: fabric`) or plain TCP (`transport: tcp`).

Written against vLLM `620e8924` (2026-04-12), the commit pinned by the `vllm/` submodule. `KVConnectorBase_V1` is marked experimental upstream; `tests/test_vllm_connector.py::test_signatures_match_vllm_source` re-checks our method signatures against whatever vLLM source is on disk (`VLLM_SRC=/path/to/vllm`). The suite also passes against vLLM 0.24.0 (what `uv pip install vllm` resolves on 2026-10-22): signatures, import and subclass check, and the producer to consumer run through vLLM's own `KVConnectorBase_V1`.

Baselines in `benchmarks/vllm_disagg/launch.sh`: `CONNECTOR=nixl` (NixlConnector, UCX) and `CONNECTOR=nixl-libfabric` (NixlConnector with `"backends": ["LIBFABRIC"]`). NIXL's libfabric plugin picks cxi, efa, tcp or sockets and lists GPUDirect RDMA as required, so on SoftRoCE and the ConnectX-4 towers it runs over libfabric `tcp` at best. This connector stages KV through host memory and runs on the verbs provider.

## Files

| File | What |
|---|---|
| `connector.py` | `ScuffedRdmaConnector(KVConnectorBase_V1)`. Thin; imports vLLM. Loaded via `kv_connector_module_path`. |
| `core.py` | Scheduler-side and worker-side logic with no vLLM import. |
| `kv_layout.py` | Gather/scatter of paged KV blocks (FlashAttention, FlashInfer/Triton, MLA layouts) on numpy or torch. |
| `kv_codec.py` | Wire format: JSON header + raw arrays, bfloat16 safe. Optional `scuffedquant` codec. |
| `transport.py` | `KVSender` (producer queue + thread, WFA hot/cold tag, telemetry) and `KVReceiver` (staging pool). |
| `proxy.py` | Disagg proxy (prefill with `max_tokens=1`, then decode with the returned `kv_transfer_params`). |
| `loopback.py` | Same data path with no vLLM: two processes or two nodes, model-shaped cache, byte-for-byte check. |

## How a request flows

1. Proxy sends the prompt to prefill with `kv_transfer_params={"do_remote_decode": true, "scuffed_xfer_id": <uuid>}` and `max_tokens=1`.
2. Prefill scheduler records the transfer id (`update_state_after_alloc`). Chunked prefill is held until the prompt is complete.
3. Each attention layer's `save_kv_layer` gathers that request's blocks, encodes them, and queues `"<xfer_id>/<layer_name>"` on `KVSender`. The WFA classifier tags each blob hot or cold (under 4 KB hot, over 256 KB cold, mid-range by access frequency and phase). `wait_for_save` adds a hot control blob `"<xfer_id>/__done__"`.
4. `request_finished` returns `{"do_remote_prefill": true, "scuffed_xfer_id": ..., "scuffed_num_tokens": N}`; the proxy forwards it to decode.
5. Decode `get_num_new_matched_tokens` reports `len(prompt) - 1` external tokens. `start_load_kv` waits for each layer's blob (default 30 s), skips blocks already served by the local prefix cache, and scatters the rest into the paged cache. Layers that never arrive are reported through `get_block_ids_with_load_errors` and vLLM recomputes them.

Request ids are not shared between the two engines: vLLM appends a random suffix to the internal id, so transfers are keyed by `scuffed_xfer_id`, the same way NIXL keys by `kv_transfer_params`.

Loads are synchronous (as in `P2pNcclConnector`). Pushes are asynchronous: `save_kv_layer` copies blocks to host memory before returning, so prefill blocks can be freed as soon as the request finishes; set `"sync_send": true` to make `wait_for_save` also wait for the bytes to leave.

## Config (`kv_connector_extra_config`)

| Key | Default | Meaning |
|---|---|---|
| `peer` | `127.0.0.1` | Producer only: decode host. |
| `port` | `14600` | Base port; worker rank r uses `port + r` (symmetric TP only). |
| `bind` | `0.0.0.0` | Consumer listen address. |
| `transport` | `tcp` | `fabric` (libfabric pool, falls back to TCP with a `tcp_fallback` telemetry event) or `tcp`. |
| `provider`, `ep_type` | unset | Passed to `FabricBlobChannel` (`verbs` / `tcp` / `shm`; `msg` / `rdm`). |
| `compress` | unset | `scuffedquant` enables lossy cold-path compression (experimental). `bits`, `qjl_dim` apply. |
| `load_timeout_s` | `30` | Per-layer wait on decode before reporting load errors. |
| `sync_send` | `false` | `wait_for_save` blocks until blobs are handed to the channel. |
| `hot_threshold`, `cold_threshold` | `4096`, `262144` | WFA size cut points. |
| `layout` | auto | Force `flash`, `flashinfer`, or `mla` block axis. |
| `metrics_port` | unset | Serve Prometheus `/metrics` on `metrics_port + rank`. |

## Launch (Chimera decode, Cerberus prefill)

`benchmarks/vllm_disagg/launch.sh print` prints every command with current env settings. By hand:

```bash
# both nodes, repo root
export PYTHONPATH=$PWD

# chimera (decode, start first)
vllm serve ibm-granite/granite-3.3-2b-instruct --port 8200 --no-enable-prefix-caching \
  --kv-transfer-config '{"kv_connector":"ScuffedRdmaConnector","kv_connector_module_path":"middleware.vllm_plugin.connector","kv_role":"kv_consumer","kv_connector_extra_config":{"port":14600,"transport":"fabric","provider":"verbs","ep_type":"msg"}}'

# cerberus (prefill)
vllm serve ibm-granite/granite-3.3-2b-instruct --port 8100 --no-enable-prefix-caching \
  --kv-transfer-config '{"kv_connector":"ScuffedRdmaConnector","kv_connector_module_path":"middleware.vllm_plugin.connector","kv_role":"kv_producer","kv_connector_extra_config":{"peer":"chimera","port":14600,"transport":"fabric","provider":"verbs","ep_type":"msg"}}'

# proxy
python -m middleware.vllm_plugin.proxy --prefill http://cerberus:8100 --decode http://chimera:8200 --port 8000
```

`transport: tcp` gives the same connector over a TCP socket, the control for the transport comparison. The NIXL baseline is `CONNECTOR=nixl ./launch.sh ...` with `--mode nixl` on the proxy.

Cerberus (SM_120) and Chimera (SM_86) run different attention kernels; the connector only requires that both sides use the same KV cache layout, block size, and dtype. If the backends differ in layout, force one with `layout`, or pick the same attention backend on both (`VLLM_ATTENTION_BACKEND`).

## Transport check without vLLM

```bash
chimera$  python -m middleware.vllm_plugin.loopback --role consumer --port 14600 --transport fabric --provider verbs
cerberus$ python -m middleware.vllm_plugin.loopback --role producer --peer chimera --port 14600 --transport fabric --provider verbs
```

Granite 3.3-2B shaped cache (40 layers, 8 KV heads, head_dim 64, bfloat16). Both sides print a SHA-256 per request; they must match.

## Status

Built and tested here (no GPU, no vLLM install): block gather/scatter for all three layouts in numpy and torch, codec incl. bfloat16 and scuffedQuant, scheduler bookkeeping incl. chunked prefill and prefix-cache skip, producer to consumer over real sockets through the actual connector class against both a stub of `KVConnectorBase_V1` and vLLM's own base class imported from source, proxy against mock servers, TTFT runner against a mock server.

Cluster only: a real `vllm serve` on both nodes, GPU tensors, the libfabric verbs provider over SoftRoCE, TTFT/ITL numbers.

Known limits: symmetric TP only; one prefill and one decode instance per port range; loads are synchronous; KV is copied device to host before sending (no GPUDirect path yet, consumer GeForce cards are GDS gated anyway).
