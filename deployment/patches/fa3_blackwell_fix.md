# FA3 on Blackwell (RTX 5090)

vLLM aborts with `AssertionError: Sinks are only supported in FlashAttention 3` on Blackwell even with `VLLM_FLASH_ATTN_VERSION=3`. Root cause: `mm_encoder_attention.py` imports `get_flash_attn_version` at module scope, which pulls in CUTLASS, which calls `cuInit()` before the CUDA context is ready.

Upstream: [vllm#22279](https://github.com/vllm-project/vllm/issues/22279).

## Fix

Move the import inside `__init__`. Patch file: `vllm-blackwell-fa3.patch` in this directory.

```bash
cd path/to/vllm
patch -p1 < deployment/patches/vllm-blackwell-fa3.patch
pip install -e .
```

Or sed against an installed image:

```
sed -i '/from vllm.v1.attention.backends.fa_utils import get_flash_attn_version/d' \
    /usr/local/lib/python3.*/dist-packages/vllm/model_executor/layers/attention/mm_encoder_attention.py
sed -i '/AttentionBackendEnum.ROCM_AITER_FA,/a\        from vllm.v1.attention.backends.fa_utils import get_flash_attn_version' \
    /usr/local/lib/python3.*/dist-packages/vllm/model_executor/layers/attention/mm_encoder_attention.py
```

## Scope

Cerberus (2x RTX 5090) needs it. Chimera (3x RTX 3090, Ampere) does not.
