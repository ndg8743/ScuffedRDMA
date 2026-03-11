"""
Flash Attention-style tiled attention kernel.

Simplified Triton implementation of the tiled attention algorithm.
Falls back to standard scaled dot-product attention via NumPy.
"""
import numpy as np
import math
from typing import Optional


def attention_numpy(q: np.ndarray, k: np.ndarray, v: np.ndarray,
                    scale: Optional[float] = None) -> np.ndarray:
    """
    Reference scaled dot-product attention.

    Args:
        q: Queries (batch, heads, seq_q, head_dim)
        k: Keys (batch, heads, seq_k, head_dim)
        v: Values (batch, heads, seq_k, head_dim)
        scale: Scaling factor (default: 1/sqrt(head_dim))

    Returns:
        Attention output (batch, heads, seq_q, head_dim)
    """
    if scale is None:
        scale = 1.0 / math.sqrt(q.shape[-1])

    scores = np.matmul(q, k.swapaxes(-2, -1)) * scale
    scores_max = np.max(scores, axis=-1, keepdims=True)
    exp_scores = np.exp(scores - scores_max)
    attn_weights = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)
    return np.matmul(attn_weights, v)


def flash_attention(q, k, v, scale: Optional[float] = None, block_size: int = 64):
    """
    Flash Attention-style tiled attention.

    Uses Triton if available with tiled computation to reduce
    memory from O(N^2) to O(N). Falls back to NumPy.

    Args:
        q: Queries
        k: Keys
        v: Values
        scale: Optional scaling factor
        block_size: Tile size for K/V blocking

    Returns:
        Attention output
    """
    try:
        import triton
        import torch
        if isinstance(q, torch.Tensor):
            return _flash_attention_triton(q, k, v, scale, block_size)
    except ImportError:
        pass

    return attention_numpy(
        np.asarray(q), np.asarray(k), np.asarray(v), scale
    )


def _flash_attention_triton(q, k, v, scale=None, block_size=64):
    """
    Simplified Flash Attention in Triton.

    Implements the online softmax trick: process K/V in blocks,
    maintaining running max and sum for numerical stability
    without materializing the full N*N attention matrix.
    """
    import triton
    import triton.language as tl
    import torch

    batch, heads, seq_q, head_dim = q.shape
    seq_k = k.shape[2]

    if scale is None:
        scale = 1.0 / math.sqrt(head_dim)

    out = torch.empty_like(q)

    # Flatten batch and heads for grid
    grid = (batch * heads, triton.cdiv(seq_q, block_size))

    @triton.jit
    def _kernel(
        q_ptr, k_ptr, v_ptr, out_ptr,
        seq_q, seq_k, head_dim: tl.constexpr,
        stride_qb, stride_qh, stride_qs, stride_qd,
        stride_kb, stride_kh, stride_ks, stride_kd,
        stride_vb, stride_vh, stride_vs, stride_vd,
        stride_ob, stride_oh, stride_os, stride_od,
        scale,
        BLOCK_Q: tl.constexpr, BLOCK_K: tl.constexpr,
    ):
        pid_bh = tl.program_id(0)
        pid_q = tl.program_id(1)

        offs_q = pid_q * BLOCK_Q + tl.arange(0, BLOCK_Q)
        offs_d = tl.arange(0, head_dim)

        # Load Q block
        q_ptrs = q_ptr + pid_bh * stride_qh + offs_q[:, None] * stride_qs + offs_d[None, :] * stride_qd
        q_block = tl.load(q_ptrs, mask=(offs_q[:, None] < seq_q), other=0.0)

        # Running statistics for online softmax
        m_prev = tl.full((BLOCK_Q,), float('-inf'), dtype=tl.float32)
        l_prev = tl.zeros((BLOCK_Q,), dtype=tl.float32)
        acc = tl.zeros((BLOCK_Q, head_dim), dtype=tl.float32)

        # Iterate over K/V blocks
        for k_start in range(0, seq_k, BLOCK_K):
            offs_k = k_start + tl.arange(0, BLOCK_K)

            k_ptrs = k_ptr + pid_bh * stride_kh + offs_k[:, None] * stride_ks + offs_d[None, :] * stride_kd
            k_block = tl.load(k_ptrs, mask=(offs_k[:, None] < seq_k), other=0.0)

            # QK^T
            scores = tl.dot(q_block, tl.trans(k_block)) * scale

            # Online softmax update
            m_curr = tl.maximum(m_prev, tl.max(scores, axis=1))
            alpha = tl.exp(m_prev - m_curr)
            p = tl.exp(scores - m_curr[:, None])
            l_curr = alpha * l_prev + tl.sum(p, axis=1)

            # Load V and accumulate
            v_ptrs = v_ptr + pid_bh * stride_vh + offs_k[:, None] * stride_vs + offs_d[None, :] * stride_vd
            v_block = tl.load(v_ptrs, mask=(offs_k[:, None] < seq_k), other=0.0)

            acc = alpha[:, None] * acc + tl.dot(p, v_block)

            m_prev = m_curr
            l_prev = l_curr

        # Normalize
        acc = acc / l_prev[:, None]

        # Store
        out_ptrs = out_ptr + pid_bh * stride_oh + offs_q[:, None] * stride_os + offs_d[None, :] * stride_od
        tl.store(out_ptrs, acc, mask=(offs_q[:, None] < seq_q))

    _kernel[grid](
        q, k, v, out,
        seq_q, seq_k, head_dim,
        q.stride(0), q.stride(1), q.stride(2), q.stride(3),
        k.stride(0), k.stride(1), k.stride(2), k.stride(3),
        v.stride(0), v.stride(1), v.stride(2), v.stride(3),
        out.stride(0), out.stride(1), out.stride(2), out.stride(3),
        scale,
        BLOCK_Q=block_size, BLOCK_K=block_size,
    )
    return out
