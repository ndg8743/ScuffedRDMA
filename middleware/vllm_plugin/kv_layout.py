"""
Paged KV buffer slicing. Pure functions over numpy arrays or torch tensors,
so the connector's data movement is testable without CUDA or vLLM.

vLLM paged layouts handled (per layer):
  FlashAttention   [2, num_blocks, block_size, num_kv_heads, head_size]  block axis 1
  FlashInfer/Triton [num_blocks, 2, block_size, num_kv_heads, head_size] block axis 0
  MLA              [num_blocks, block_size, head_size]                    block axis 0

The heuristic matches P2pNcclConnector's (shape[0]==2 vs shape[1]==2), plus
ndim==3 for MLA. Pass layout= explicitly when num_blocks could equal 2.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

import numpy as np

LAYOUT_AXIS = {"flash": 1, "flashinfer": 0, "triton": 0, "mla": 0}


def _is_torch(x: Any) -> bool:
    return type(x).__module__.startswith("torch")


def block_axis(shape: Sequence[int], layout: Optional[str] = None) -> int:
    if layout is not None:
        return LAYOUT_AXIS[layout]
    if len(shape) == 3:
        return 0
    if shape[0] == 2 and shape[1] != 2:
        return 1
    if shape[1] == 2:
        return 0
    if shape[0] == 2:
        return 1
    return 0


def take_blocks(layer: Any, block_ids: Sequence[int], axis: int) -> Any:
    """Gather the given blocks along the block axis. Returns a new contiguous array/tensor."""
    ids = list(int(b) for b in block_ids)
    if _is_torch(layer):
        import torch
        idx = torch.as_tensor(ids, dtype=torch.long, device=layer.device)
        return layer.index_select(axis, idx).contiguous()
    return np.ascontiguousarray(np.take(layer, ids, axis=axis))


def narrow(x: Any, axis: int, start: int, length: int) -> Any:
    if _is_torch(x):
        return x.narrow(axis, start, length)
    sl = [slice(None)] * x.ndim
    sl[axis] = slice(start, start + length)
    return x[tuple(sl)]


def put_blocks(layer: Any, blocks: Any, block_ids: Sequence[int], axis: int) -> int:
    """
    Scatter blocks into layer at block_ids along axis, in place.
    Copies min(len(block_ids), blocks.shape[axis]) blocks; returns that count.
    Shapes must match on every other axis (symmetric TP only).
    """
    ids = list(int(b) for b in block_ids)
    n = min(len(ids), int(blocks.shape[axis]))
    if n == 0:
        return 0
    lshape = list(layer.shape)
    bshape = list(blocks.shape)
    lshape[axis] = bshape[axis] = -1
    if lshape != bshape:
        raise ValueError(f"KV shape mismatch outside block axis: layer {tuple(layer.shape)} vs blocks {tuple(blocks.shape)}")
    src = narrow(blocks, axis, 0, n)
    if _is_torch(layer):
        import torch
        idx = torch.as_tensor(ids[:n], dtype=torch.long, device=layer.device)
        src = src.to(device=layer.device, dtype=layer.dtype)
        layer.index_copy_(axis, idx, src)
        return n
    sl = [slice(None)] * layer.ndim
    sl[axis] = np.asarray(ids[:n])
    layer[tuple(sl)] = src
    return n
