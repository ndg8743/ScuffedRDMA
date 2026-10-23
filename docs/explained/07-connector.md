# 7. ScuffedRdmaConnector inside vLLM

[← back to the README section](../../README.md#7-scuffedrdmaconnector-inside-vllm)

![Connector request flow](../media/07_connector.gif)

The connector plugs the transport into vLLM's disaggregated serving. This page walks through one request step by step and argues the properties that matter:

- the decode side never uses KV from the wrong request;
- a lost layer degrades to recomputation, never to a wrong answer;
- the decode side never waits forever;
- the host staging copy has a predictable cost.

Code: `middleware/vllm_plugin/` (`connector.py`, `core.py`, `kv_layout.py`, `kv_codec.py`, `transport.py`, `proxy.py`). Tests: `tests/test_vllm_connector.py` (also run against vLLM 0.24.0).

---

## 1. The request, step by step

1. **Proxy → prefill.** The proxy sends the prompt with `max_tokens=1`, `do_remote_decode: true` and a fresh transfer id `xfer_id` (a UUID).
2. **Prefill scheduler** records `xfer_id` for the request (`update_state_after_alloc`). Chunked prefill is held until the whole prompt is processed, so KV is pushed once.
3. **Each attention layer** calls `save_kv_layer`: gather this request's paged blocks (`kv_layout.take_blocks`), copy them to host memory, encode them (raw bf16, or scuffedQuant), and queue one blob keyed `"<xfer_id>/<layer>"` on the sender. The WFA tags each blob hot or cold.
4. **`wait_for_save`** queues a hot `"<xfer_id>/__done__"` blob.
5. **`request_finished`** returns `{do_remote_prefill, scuffed_xfer_id, scuffed_num_tokens}`; the proxy forwards the original request plus these parameters to decode.
6. **Decode scheduler**, `get_num_new_matched_tokens`: reports `len(prompt) − 1` tokens as available externally, so vLLM allocates blocks for them instead of computing them.
7. **Decode worker**, `start_load_kv`: for each layer, wait (default 30 s) for its blob, decode it, skip blocks already served by the local prefix cache, and scatter the rest into the paged cache (`put_blocks`).
8. Decode runs and tokens stream back through the proxy.

## 2. Why transfers are keyed by `xfer_id`, not the request id

vLLM appends a random suffix to request ids internally, so the prefill and decode engines name the same request differently. The proxy generates one `xfer_id` and passes it to both through `kv_transfer_params`. (NIXL does the same thing.)

**Collision bound.** `xfer_id` is a random UUID with 122 random bits. For $`n`$ ids, the probability that any two collide is at most $`n^2 / 2^{123}`$. Even for $`n = 10^9`$ requests that is about $`10^{-19}`$.

## 3. A lost layer degrades to recomputation, not a wrong answer

**Claim.** If a layer's KV never arrives, the output is still correct (only slower).

**Argument.** `start_load_kv` waits for each layer with a deadline. If the deadline passes, the blocks that layer would have filled are reported through `get_block_ids_with_load_errors`. vLLM treats those blocks as not computed and recomputes them, as it would without the connector. Blocks that did arrive came over a reliable transport and passed the blob header check (magic number, lengths), so they hold the producer's bytes. In both branches, every block decode attends over was either produced by prefill's forward pass or recomputed by decode's own, so the attention inputs match a non-disaggregated run. $`\square`$

**Liveness.** Each layer wait is bounded by `load_timeout_s`, so a request waits at most $`L \times`$ `load_timeout_s` in the worst case (40 layers × 30 s by default; a real deployment should lower it) and then proceeds.

## 4. Fallback when libfabric will not open

If the libfabric channel fails to open, the connector creates a TCP channel with the same interface and records a `tcp_fallback` telemetry event. The run continues, and the event makes it impossible to mistake it for an RDMA result (README section 3, problem 4).

## 5. Host staging: what it costs

None of the lab servers has a GPUDirect RDMA path (SoftRoCE has none; server 4's kernel lacks peer-memory support). So each layer is copied from GPU to host memory before it is sent, and from host to GPU after it arrives.

**Cost model.** For a layer of $`b`$ bytes over a PCIe link with effective bandwidth $`P`$, each copy takes $`b/P`$. Example: a 4 MiB layer (2K tokens of Granite 3.3-2B) over a PCIe 4.0 x16 link at an effective ~20 GB/s takes about 0.2 ms, against 3.4 ms to put the same 4 MiB on a 10 Gb/s wire. The copy is roughly 6% of the wire time per layer at these rates. That is an estimate with an assumed PCIe rate; notebook 08 times the real copies.

**Why push is asynchronous.** `save_kv_layer` returns once the blocks are copied to host memory, and a background thread sends them. Prefill's GPU blocks can be freed as soon as the request finishes; the network time does not hold GPU memory. `sync_send: true` makes `wait_for_save` also wait for the bytes to leave, if needed.

## 6. Baselines

The same request flow runs with vLLM's `NixlConnector` on its UCX backend (`CONNECTOR=nixl`) and on its `LIBFABRIC` backend (`CONNECTOR=nixl-libfabric`). The second one, on our hardware, can only use libfabric `tcp` (README section 3, problem 2). E7 (one GPU) and E8 (across servers) compare all of them on time-to-first-token and inter-token latency.

## 7. Status

| Claim | Status |
|---|---|
| Correct KV per request (keying) | by construction; collision bound above |
| Lost layer → recompute, not wrong output | argued above; tested with a dropped layer in `tests/test_vllm_connector.py` |
| Bounded wait | by the per-layer timeout |
| Signatures and base class match vLLM | tested against 620e8924 and 0.24.0 |
| Staging cost | estimate; measured by notebook 08 |
| TTFT/ITL vs NIXL | open: E7, E8 |

## References

1. vLLM. `KVConnectorBase_V1`, [`vllm/distributed/kv_transfer/kv_connector/v1/base.py`](https://github.com/vllm-project/vllm/blob/v0.24.0/vllm/distributed/kv_transfer/kv_connector/v1/base.py) (v0.24.0). *Used for: the hooks in §1 and the load-error path in §3.*
2. vLLM documentation. "Disaggregated Prefilling." [docs.vllm.ai](https://docs.vllm.ai/en/latest/features/disagg_prefill/). *Used for: the proxy pattern (§1).*
3. vLLM. `NixlConnector`, [`vllm/distributed/kv_transfer/kv_connector/v1/nixl/`](https://github.com/vllm-project/vllm/tree/v0.24.0/vllm/distributed/kv_transfer/kv_connector/v1/nixl) (v0.24.0). *Used for: keying transfers through `kv_transfer_params` (§2) and the baselines (§6).*
4. K. Davis, B. Peabody, P. Leach. "Universally Unique IDentifiers (UUIDs)." [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562), 2024. *Used for: 122 random bits in a version-4 UUID (§2).*
5. NVIDIA. NIXL. [github.com/ai-dynamo/nixl](https://github.com/ai-dynamo/nixl). *Used for: the baseline transport (§6).*
6. `middleware/vllm_plugin/` and `tests/test_vllm_connector.py` (dropped-layer test asserting load errors). *The implementation and tests behind §3.*
