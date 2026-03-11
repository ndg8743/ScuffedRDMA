"""
Baseline tiled matrix multiplication kernel.

Triton implementation with NVSHMEM integration stubs for RDMA-aware compute.
Falls back to NumPy when Triton is not available.
"""
import numpy as np
from typing import Optional


def matmul_numpy(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Reference NumPy matrix multiplication."""
    return a @ b


def matmul_tiled(a, b, block_size: int = 64):
    """
    Tiled matrix multiplication.

    Uses Triton if available, otherwise falls back to NumPy.
    Tiling improves cache locality and maps naturally to GPU blocks.

    Args:
        a: Left matrix (M, K)
        b: Right matrix (K, N)
        block_size: Tile dimension

    Returns:
        Result matrix (M, N)
    """
    try:
        import triton
        import triton.language as tl
        import torch
        return _matmul_triton(a, b, block_size)
    except ImportError:
        # NumPy fallback
        a_np = np.asarray(a)
        b_np = np.asarray(b)
        return matmul_numpy(a_np, b_np)


def _matmul_triton(a, b, block_size: int = 64):
    """Triton tiled matmul kernel."""
    import triton
    import triton.language as tl
    import torch

    assert a.shape[1] == b.shape[0], f"Shape mismatch: {a.shape} x {b.shape}"
    M, K = a.shape
    K, N = b.shape

    c = torch.empty((M, N), device=a.device, dtype=a.dtype)

    grid = lambda meta: (
        triton.cdiv(M, meta['BLOCK_M']),
        triton.cdiv(N, meta['BLOCK_N']),
    )

    @triton.jit
    def _kernel(
        a_ptr, b_ptr, c_ptr,
        M, N, K,
        stride_am, stride_ak,
        stride_bk, stride_bn,
        stride_cm, stride_cn,
        BLOCK_M: tl.constexpr, BLOCK_N: tl.constexpr, BLOCK_K: tl.constexpr,
    ):
        pid_m = tl.program_id(0)
        pid_n = tl.program_id(1)

        offs_m = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
        offs_n = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
        offs_k = tl.arange(0, BLOCK_K)

        a_ptrs = a_ptr + offs_m[:, None] * stride_am + offs_k[None, :] * stride_ak
        b_ptrs = b_ptr + offs_k[:, None] * stride_bk + offs_n[None, :] * stride_bn

        acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)

        for k_start in range(0, K, BLOCK_K):
            a_tile = tl.load(a_ptrs, mask=(offs_m[:, None] < M) & (offs_k[None, :] + k_start < K), other=0.0)
            b_tile = tl.load(b_ptrs, mask=(offs_k[:, None] + k_start < K) & (offs_n[None, :] < N), other=0.0)
            acc += tl.dot(a_tile, b_tile)
            a_ptrs += BLOCK_K * stride_ak
            b_ptrs += BLOCK_K * stride_bk

        c_ptrs = c_ptr + offs_m[:, None] * stride_cm + offs_n[None, :] * stride_cn
        mask = (offs_m[:, None] < M) & (offs_n[None, :] < N)
        tl.store(c_ptrs, acc, mask=mask)

    _kernel[grid](
        a, b, c,
        M, N, K,
        a.stride(0), a.stride(1),
        b.stride(0), b.stride(1),
        c.stride(0), c.stride(1),
        BLOCK_M=block_size, BLOCK_N=block_size, BLOCK_K=32,
    )
    return c


# NVSHMEM integration stubs
class NvshmemMatmul:
    """
    RDMA-aware matmul stub for NVSHMEM integration.

    In the full implementation, this would use nvshmem_put/get
    to distribute matrix tiles across GPUs via RDMA.
    """

    def __init__(self, num_gpus: int = 2):
        self.num_gpus = num_gpus

    def distributed_matmul(self, a, b):
        """
        Placeholder for NVSHMEM-distributed matmul.

        Would partition A by rows across GPUs, with each GPU
        computing its shard and using nvshmem_put to write
        partial results to the output buffer.
        """
        # Stub: fall back to local matmul
        return matmul_tiled(a, b)
