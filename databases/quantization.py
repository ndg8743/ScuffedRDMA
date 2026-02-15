"""
Adaptive quantization for bandwidth-constrained tensor transfers.

Selects quantization level based on available bandwidth and latency
targets, trading off fidelity for transfer speed.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from .precision import PrecisionFormat, PrecisionManager, _BYTES_PER_ELEMENT


@dataclass
class QuantizationMeta:
    """Metadata needed to dequantize a tensor."""
    format: PrecisionFormat
    original_shape: Tuple[int, ...]
    original_dtype: str
    scale: Optional[float] = None
    zero_point: Optional[float] = None
    num_elements: Optional[int] = None


class AdaptiveQuantizer:
    """
    Bandwidth-adaptive tensor quantization.

    Automatically selects the most aggressive quantization that stays
    within fidelity constraints, based on current link conditions.
    """

    def __init__(self, precision_mgr: Optional[PrecisionManager] = None,
                 max_relative_error: float = 0.01):
        self._pm = precision_mgr or PrecisionManager()
        self._max_rel_error = max_relative_error

    def quantize(self, tensor: np.ndarray,
                 fmt: PrecisionFormat) -> Tuple[np.ndarray, QuantizationMeta]:
        """
        Quantize tensor to the specified format.

        Args:
            tensor: Input tensor (any dtype, converted to FP32 internally).
            fmt: Target precision format.

        Returns:
            (quantized_data, metadata) tuple.
        """
        fp32 = tensor.astype(np.float32)
        meta = QuantizationMeta(
            format=fmt,
            original_shape=tensor.shape,
            original_dtype=str(tensor.dtype),
            num_elements=tensor.size,
        )

        if fmt in (PrecisionFormat.INT8, PrecisionFormat.MXFP4):
            amax = np.abs(fp32).max()
            meta.scale = float(amax) if amax > 0 else 1.0

        quantized = self._pm.convert(fp32, fmt, stochastic=True)
        return quantized, meta

    def dequantize(self, data: np.ndarray, meta: QuantizationMeta) -> np.ndarray:
        """
        Restore tensor from quantized representation.

        Args:
            data: Quantized data.
            meta: Metadata from quantize().

        Returns:
            Reconstructed FP32 tensor.
        """
        fmt = meta.format

        if fmt == PrecisionFormat.FP32:
            return data.reshape(meta.original_shape)

        if fmt == PrecisionFormat.FP16:
            return data.astype(np.float32).reshape(meta.original_shape)

        if fmt == PrecisionFormat.BF16:
            return self._pm.bf16_to_fp32(data).reshape(meta.original_shape)

        if fmt == PrecisionFormat.INT8:
            scale = meta.scale or 1.0
            restored = data.astype(np.float32) * (scale / 127.0)
            return restored.reshape(meta.original_shape)

        if fmt == PrecisionFormat.MXFP4:
            return self._pm.mxfp4_to_fp32(
                data, meta.num_elements
            ).reshape(meta.original_shape)

        return data.astype(np.float32).reshape(meta.original_shape)

    def select_quantization(self, tensor_bytes: int,
                            bandwidth_gbps: float,
                            latency_target_ms: float) -> PrecisionFormat:
        """
        Choose optimal quantization given link constraints.

        Args:
            tensor_bytes: Tensor size in FP32 bytes.
            bandwidth_gbps: Current link bandwidth.
            latency_target_ms: Maximum transfer time.

        Returns:
            Selected precision format.
        """
        return self._pm.optimal_format(tensor_bytes, bandwidth_gbps, latency_target_ms)

    def compression_ratio(self, fmt: PrecisionFormat) -> float:
        """Compression ratio relative to FP32."""
        return _BYTES_PER_ELEMENT[PrecisionFormat.FP32] / _BYTES_PER_ELEMENT[fmt]

    def estimate_error(self, tensor: np.ndarray, fmt: PrecisionFormat) -> float:
        """
        Estimate relative quantization error for a given format.

        Args:
            tensor: Sample tensor.
            fmt: Target format.

        Returns:
            Mean relative error.
        """
        quantized, meta = self.quantize(tensor, fmt)
        restored = self.dequantize(quantized, meta)
        fp32 = tensor.astype(np.float32)
        denom = np.abs(fp32).mean()
        if denom < 1e-12:
            return 0.0
        return float(np.abs(fp32 - restored).mean() / denom)
