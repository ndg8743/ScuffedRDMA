"""
Baseline softmax kernel.

Triton implementation with online normalization for numerical stability.
Falls back to NumPy when Triton is not available.
"""
import numpy as np
from typing import Optional


def softmax_numpy(x: np.ndarray, axis: int = -1) -> np.ndarray:
    """Reference NumPy softmax with numerical stability."""
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def softmax(x, axis: int = -1):
    """
    Softmax with Triton or NumPy fallback.

    Uses online normalization (two-pass: max then exp+sum) for stability.

    Args:
        x: Input tensor
        axis: Axis to normalize over (default: last)

    Returns:
        Softmax output, same shape as input
    """
    try:
        import triton
        import torch
        if isinstance(x, torch.Tensor):
            return _softmax_triton(x)
    except ImportError:
        pass

    return softmax_numpy(np.asarray(x), axis=axis)


def _softmax_triton(x):
    """Triton softmax kernel (row-wise)."""
    import triton
    import triton.language as tl
    import torch

    assert x.ndim == 2, "Triton softmax expects 2D input"
    M, N = x.shape

    out = torch.empty_like(x)

    # One program per row
    grid = (M,)

    # Find next power of 2 >= N for the block size
    BLOCK_N = triton.next_power_of_2(N)

    @triton.jit
    def _kernel(x_ptr, out_ptr, N, stride_x, stride_out, BLOCK_N: tl.constexpr):
        row = tl.program_id(0)
        offs = tl.arange(0, BLOCK_N)

        x_ptrs = x_ptr + row * stride_x + offs
        mask = offs < N

        x_vals = tl.load(x_ptrs, mask=mask, other=float('-inf'))

        # Online normalization
        x_max = tl.max(x_vals, axis=0)
        exp_x = tl.exp(x_vals - x_max)
        sum_exp = tl.sum(exp_x, axis=0)

        result = exp_x / sum_exp

        out_ptrs = out_ptr + row * stride_out + offs
        tl.store(out_ptrs, result, mask=mask)

    _kernel[grid](x, out, N, x.stride(0), out.stride(0), BLOCK_N=BLOCK_N)
    return out
