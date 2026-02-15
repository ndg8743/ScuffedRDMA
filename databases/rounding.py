"""
Stochastic rounding for precision-lossy tensor conversions.

Ensures E[round(x)] = x, preserving unbiased gradient estimates when
transferring FP32 master weights over RDMA in reduced precision.
"""

import numpy as np

from .precision import PrecisionFormat


def stochastic_round_f32_to_f16(values: np.ndarray,
                                 rng: np.random.Generator = None) -> np.ndarray:
    """Round FP32 values to FP16 with probabilistic rounding."""
    if rng is None:
        rng = np.random.default_rng()
    fp32 = values.astype(np.float32)
    down = fp32.astype(np.float16).astype(np.float32)
    up = np.nextafter(down, np.inf).astype(np.float16).astype(np.float32)
    span = up - down
    mask = span != 0
    prob = np.zeros_like(fp32)
    prob[mask] = (fp32[mask] - down[mask]) / span[mask]
    choices = rng.random(fp32.shape) < prob
    return np.where(choices, up, down).astype(np.float16)


def stochastic_round_f32_to_bf16(values: np.ndarray,
                                  rng: np.random.Generator = None) -> np.ndarray:
    """Round FP32 values to BF16 with probabilistic rounding."""
    if rng is None:
        rng = np.random.default_rng()
    fp32 = values.astype(np.float32)
    raw = fp32.view(np.uint32)
    noise = rng.integers(0, 1 << 16, size=fp32.shape, dtype=np.uint32)
    rounded = raw + (noise & 0xFFFF)
    return (rounded >> 16).astype(np.uint16)


def apply_gradient_batch(weights: np.ndarray, gradients: np.ndarray,
                         lr: float, target_format: PrecisionFormat,
                         rng: np.random.Generator = None) -> np.ndarray:
    """
    Apply gradients to FP32 master weights and round to target format.

    Updates in full precision first, then stochastically rounds the result
    for wire transfer. The FP32 master copy is returned for local storage.
    """
    fp32 = weights.astype(np.float32) - lr * gradients.astype(np.float32)
    if target_format == PrecisionFormat.FP16:
        return stochastic_round_f32_to_f16(fp32, rng)
    elif target_format == PrecisionFormat.BF16:
        return stochastic_round_f32_to_bf16(fp32, rng)
    return fp32
