#!/usr/bin/env bash
# Launch helpers for disaggregated prefill (server 1) / decode (server 2).
#
#   CONNECTOR=scuffed TRANSPORT=fabric PROVIDER=verbs ./launch.sh decode    # on server 2, start first
#   CONNECTOR=scuffed TRANSPORT=fabric PROVIDER=verbs ./launch.sh prefill   # on server 1
#   CONNECTOR=scuffed ./launch.sh proxy                                     # anywhere
#   ./launch.sh single                                                      # no-disagg baseline, one node
#   ./launch.sh print                                                       # show every command, run nothing
#
# CONNECTOR: scuffed | nixl | nixl-libfabric | tcp
#   tcp            = ScuffedRdmaConnector over its TCP channel
#   nixl           = vLLM NixlConnector, UCX backend
#   nixl-libfabric = vLLM NixlConnector, LIBFABRIC backend (FI_PROVIDER from NIXL_FI_PROVIDER, default tcp)
#   NIXL_SIDE_PORT_PREFILL / NIXL_SIDE_PORT_DECODE: side-channel ports (set different ones when both run on one host)
# Every knob is an env var; defaults below. vLLM must be installed on both nodes.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="$REPO${PYTHONPATH:+:$PYTHONPATH}"

MODEL="${MODEL:-ibm-granite/granite-3.3-2b-instruct}"
PREFILL_HOST="${PREFILL_HOST:-server1}"
DECODE_HOST="${DECODE_HOST:-server2}"
PREFILL_PORT="${PREFILL_PORT:-8100}"
DECODE_PORT="${DECODE_PORT:-8200}"
PROXY_PORT="${PROXY_PORT:-8000}"
SINGLE_PORT="${SINGLE_PORT:-8300}"
KV_PORT="${KV_PORT:-14600}"
CONNECTOR="${CONNECTOR:-scuffed}"
TRANSPORT="${TRANSPORT:-fabric}"
PROVIDER="${PROVIDER:-verbs}"
EP_TYPE="${EP_TYPE:-msg}"
COMPRESS="${COMPRESS:-}"                 # empty or scuffedquant
METRICS_PORT="${METRICS_PORT:-9464}"
GPU_UTIL="${GPU_UTIL:-0.85}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
EXTRA_ARGS="${EXTRA_ARGS:-}"             # e.g. "--enforce-eager --tensor-parallel-size 2"

scuffed_cfg() {   # $1 = kv_producer | kv_consumer
  local transport="$TRANSPORT"
  [[ "$CONNECTOR" == "tcp" ]] && transport="tcp"
  local comp=""
  [[ -n "$COMPRESS" ]] && comp=",\"compress\":\"$COMPRESS\",\"bits\":3"
  printf '{"kv_connector":"ScuffedRdmaConnector","kv_connector_module_path":"middleware.vllm_plugin.connector","kv_role":"%s","kv_connector_extra_config":{"peer":"%s","port":%s,"transport":"%s","provider":"%s","ep_type":"%s","metrics_port":%s%s}}' \
    "$1" "$DECODE_HOST" "$KV_PORT" "$transport" "$PROVIDER" "$EP_TYPE" "$METRICS_PORT" "$comp"
}

serve_cmd() {     # $1 = prefill | decode
  local port cfg env=""
  if [[ "$1" == "prefill" ]]; then port="$PREFILL_PORT"; else port="$DECODE_PORT"; fi
  case "$CONNECTOR" in
    scuffed|tcp)
      if [[ "$1" == "prefill" ]]; then cfg="$(scuffed_cfg kv_producer)"; else cfg="$(scuffed_cfg kv_consumer)"; fi ;;
    nixl|nixl-libfabric)
      local host="$PREFILL_HOST" sport="${NIXL_SIDE_PORT_PREFILL:-5600}"
      [[ "$1" == "decode" ]] && host="$DECODE_HOST" && sport="${NIXL_SIDE_PORT_DECODE:-5600}"
      if [[ "$CONNECTOR" == "nixl" ]]; then
        cfg='{"kv_connector":"NixlConnector","kv_role":"kv_both"}'
        env="VLLM_NIXL_SIDE_CHANNEL_HOST=$host VLLM_NIXL_SIDE_CHANNEL_PORT=$sport UCX_TLS=rc,tcp,cuda_copy "
      else
        # NIXL's own libfabric backend, the direct baseline for ScuffedRdmaConnector over libfabric.
        # Its provider discovery (src/utils/libfabric/libfabric_common.cpp, nixl d642316) asks for
        # FI_EP_RDM + FI_MSG|FI_RMA and takes cxi, then efa, then tcp, then sockets. verbs is not in
        # that list, so on server 1 / server 2 and servers 3 and 4 it can only run over tcp. The plugin
        # README also lists libfabric >= 1.21 and GPUDirect RDMA as requirements.
        cfg='{"kv_connector":"NixlConnector","kv_role":"kv_both","kv_connector_extra_config":{"backends":["LIBFABRIC"]}}'
        env="VLLM_NIXL_SIDE_CHANNEL_HOST=$host VLLM_NIXL_SIDE_CHANNEL_PORT=$sport FI_PROVIDER=${NIXL_FI_PROVIDER:-tcp} "
      fi ;;
    *) echo "unknown CONNECTOR=$CONNECTOR" >&2; exit 2 ;;
  esac
  echo "${env}vllm serve $MODEL --port $port --gpu-memory-utilization $GPU_UTIL --max-model-len $MAX_MODEL_LEN --no-enable-prefix-caching $EXTRA_ARGS --kv-transfer-config '$cfg'"
}

proxy_cmd() {
  local mode="scuffed"; [[ "$CONNECTOR" == nixl* ]] && mode="nixl"
  echo "python -m middleware.vllm_plugin.proxy --prefill http://$PREFILL_HOST:$PREFILL_PORT --decode http://$DECODE_HOST:$DECODE_PORT --port $PROXY_PORT --mode $mode"
}

single_cmd() {
  echo "vllm serve $MODEL --port $SINGLE_PORT --gpu-memory-utilization $GPU_UTIL --max-model-len $MAX_MODEL_LEN --no-enable-prefix-caching $EXTRA_ARGS"
}

case "${1:-print}" in
  prefill) cmd="$(serve_cmd prefill)" ;;
  decode)  cmd="$(serve_cmd decode)" ;;
  proxy)   cmd="$(proxy_cmd)" ;;
  single)  cmd="$(single_cmd)" ;;
  print)
    echo "# on $DECODE_HOST (start first):";  echo "cd $REPO && $(serve_cmd decode)"
    echo "# on $PREFILL_HOST:";               echo "cd $REPO && $(serve_cmd prefill)"
    echo "# proxy:";                          echo "cd $REPO && $(proxy_cmd)"
    echo "# no-disagg baseline (one node):";  echo "cd $REPO && $(single_cmd)"
    exit 0 ;;
  *) echo "usage: $0 prefill|decode|proxy|single|print" >&2; exit 2 ;;
esac
echo "+ $cmd" >&2
cd "$REPO"
eval "exec $cmd"
