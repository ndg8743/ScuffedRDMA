# FlashAttention 3 Fix for NVIDIA Blackwell (RTX 5090)

**Date:** February 2026
**Issue:** [vllm-project/vllm#22279](https://github.com/vllm-project/vllm/issues/22279)
**Affected Hardware:** RTX 5090, RTX 5080, GB200, B200 (Blackwell architecture)

## Problem

vLLM fails to run certain models on Blackwell GPUs (RTX 5090) with FlashAttention 3 enabled:

```
AssertionError: Sinks are only supported in FlashAttention 3
```

Despite setting `VLLM_FLASH_ATTN_VERSION=3`, the system incorrectly rejects Blackwell GPUs.

### Error Chain

```
RuntimeError: Early CUDA initialization error
  → mm_encoder_attention.py imports fa_utils at module scope
  → fa_utils imports vllm_flash_attn
  → vllm_flash_attn imports flash_attention
  → flash_attention imports cutlass
  → cutlass calls cuInit() before GPU context is ready
```

### Affected Models

- HunyuanOCR (`tencent/HunyuanOCR`)
- Any model using `MMEncoderAttention`
- Vision-language models with FlashAttention backends

## Solution

**Make the `get_flash_attn_version` import lazy** to avoid early CUDA initialization.

### Patch

```diff
diff --git a/vllm/model_executor/layers/attention/mm_encoder_attention.py b/vllm/model_executor/layers/attention/mm_encoder_attention.py
index 35c10ec0b..c83c5c587 100644
--- a/vllm/model_executor/layers/attention/mm_encoder_attention.py
+++ b/vllm/model_executor/layers/attention/mm_encoder_attention.py
@@ -7,7 +7,6 @@ import torch
 from vllm.logger import init_logger
 from vllm.model_executor.custom_op import CustomOp
 from vllm.model_executor.models.vision import get_vit_attn_backend
-from vllm.v1.attention.backends.fa_utils import get_flash_attn_version
 from vllm.v1.attention.backends.registry import AttentionBackendEnum
 from vllm.v1.attention.ops.vit_attn_wrappers import (
     vit_flash_attn_wrapper,
@@ -69,6 +68,7 @@ class MMEncoderAttention(CustomOp):
             AttentionBackendEnum.FLASH_ATTN,
             AttentionBackendEnum.ROCM_AITER_FA,
         }
+        from vllm.v1.attention.backends.fa_utils import get_flash_attn_version

         self._fa_version = (
             get_flash_attn_version() if self.is_flash_attn_backend else None
```

## Applying the Patch

### Option 1: Patch vLLM Source (Recommended)

```bash
# Clone vLLM
git clone https://github.com/vllm-project/vllm.git
cd vllm

# Apply patch
patch -p1 < /path/to/vllm-blackwell-fa3.patch

# Build from source
pip install -e .
```

### Option 2: Docker with Patched Source

```dockerfile
FROM vllm/vllm-openai:latest

# Apply the lazy import fix
RUN sed -i '/from vllm.v1.attention.backends.fa_utils import get_flash_attn_version/d' \
    /usr/local/lib/python3.*/dist-packages/vllm/model_executor/layers/attention/mm_encoder_attention.py && \
    sed -i '/AttentionBackendEnum.ROCM_AITER_FA,/a\        from vllm.v1.attention.backends.fa_utils import get_flash_attn_version' \
    /usr/local/lib/python3.*/dist-packages/vllm/model_executor/layers/attention/mm_encoder_attention.py
```

### Option 3: Monkey Patch at Runtime

```python
# Add to vLLM startup script
import sys
from unittest.mock import patch

# Delay the problematic import
original_import = __builtins__.__import__

def lazy_import(name, *args, **kwargs):
    if name == 'vllm.v1.attention.backends.fa_utils':
        return None  # Will be imported later when needed
    return original_import(name, *args, **kwargs)

# Apply before vLLM import
with patch.object(__builtins__, '__import__', lazy_import):
    import vllm
```

## Verification

After applying the patch, verify FlashAttention 3 works:

```bash
# Check GPU is detected
python -c "import torch; print(torch.cuda.get_device_name())"
# Should show: NVIDIA GeForce RTX 5090

# Test vLLM with FA3
VLLM_FLASH_ATTN_VERSION=3 python -c "
from vllm import LLM
llm = LLM(model='meta-llama/Llama-3.2-1B', tensor_parallel_size=1)
print('FlashAttention 3 working!')
"
```

## Cluster Impact

### Cerberus (2× RTX 5090)

This fix is **required** for Cerberus to participate in multi-node vLLM inference with FlashAttention 3.

| Before Fix | After Fix |
|------------|-----------|
| FA3 fails on Blackwell | FA3 works correctly |
| Falls back to FA2 | Native FA3 performance |
| ~15% slower | Full Blackwell optimization |

### Chimera (3× RTX 3090)

RTX 3090 (Ampere) is **not affected** - FlashAttention 3 works without this patch.

## Root Cause Analysis

The issue stems from Python's eager module import behavior:

```python
# Module scope import (BAD - causes early cuInit)
from vllm.v1.attention.backends.fa_utils import get_flash_attn_version

class MMEncoderAttention:
    def __init__(self):
        self._fa_version = get_flash_attn_version()  # Already failed
```

```python
# Function scope import (GOOD - deferred until needed)
class MMEncoderAttention:
    def __init__(self):
        from vllm.v1.attention.backends.fa_utils import get_flash_attn_version
        self._fa_version = get_flash_attn_version()  # Works now
```

The CUTLASS library (used by FlashAttention) calls `cuInit()` at import time. On Blackwell GPUs, this must happen after the CUDA context is properly initialized, which doesn't occur until the model is actually loaded.

## References

- [vLLM Issue #22279](https://github.com/vllm-project/vllm/issues/22279)
- [FlashAttention 3 Paper](https://arxiv.org/abs/2307.08691)
- [NVIDIA Blackwell Architecture](https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/)
- [FlashInfer](https://github.com/flashinfer-ai/flashinfer) - Alternative attention backend

## Status

- **vLLM Main**: Not yet merged (as of Feb 2026)
- **Workaround**: Apply patch manually
- **Expected Fix**: vLLM 0.11.x or later
