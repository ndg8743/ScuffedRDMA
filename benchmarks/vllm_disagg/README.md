# vLLM disaggregated prefill/decode: TTFT and ITL

Measures time to first token and inter-token latency for Granite 3.3-2B served disaggregated (prefill on server 1, decode on server 2) with:

| Label | Setup |
|---|---|
| `single` | One `vllm serve`, no disaggregation. Reference. |
| `nixl` | `NixlConnector` (UCX underneath), vLLM's own baseline. |
| `scuffed-tcp` | `ScuffedRdmaConnector` over its TCP channel. Same connector, no RDMA. |
| `scuffed-fabric-verbs` | `ScuffedRdmaConnector` over the libfabric hot/cold pool, verbs provider on SoftRoCE. |

No results are checked in from this folder until they come from the cluster.

## Run

```bash
./launch.sh print                                                   # every command for the current env
CONNECTOR=scuffed TRANSPORT=fabric PROVIDER=verbs ./launch.sh decode   # server 2, first
CONNECTOR=scuffed TRANSPORT=fabric PROVIDER=verbs ./launch.sh prefill  # server 1
CONNECTOR=scuffed ./launch.sh proxy

python run_ttft_sweep.py --url http://localhost:8000 --label scuffed-fabric-verbs \
    --prompt-lens 128,512,1024,2048,4096 --n 20 --max-tokens 64 --out ../results/vllm_disagg/
```

Repeat with `CONNECTOR=tcp`, `CONNECTOR=nixl`, and `./launch.sh single` (sweep against `:8300`). `notebooks/06_vllm_disagg_ttft.ipynb` runs the sweeps and plots them.

`run_ttft_sweep.py --selftest` checks the measurement path against a mock streaming server with known delays.

## What the numbers mean

- Prompts are random token ids of exact length; `ignore_eos` keeps output length fixed at `--max-tokens`.
- TTFT on the proxy includes the prefill round trip, the KV transfer, and decode's first step. The proxy returns `X-Scuffed-Prefill-Ms` so the prefill part can be split out.
- Prefix caching is off on both servers so repeated prompts do not skip the transfer.
- The decode engine waits for every layer before the first decode step (synchronous load), so TTFT carries the full transfer time. Layer-pipelined loading is future work.
