# NCCL Net Plugin (libscuffed_nccl_net)

NCCL network plugin that routes traffic through dual QP pools (hot/cold) based on message size.

## Build

```
make
```

Requires `libibverbs-dev`.

## Use

```
NCCL_NET_PLUGIN=$(pwd)/libscuffed_nccl_net.so vllm serve --model granite-3.3-2b
```

## How it works

Each connection gets two RC QPs: hot (< 4KB, inline sends, busy-poll CQ) and cold (>= 4KB, DMA from MR). This is the WFA classifier from libscuffedrdma implemented at the NCCL transport layer.
