"""
Precision format management for mixed-precision tensor transfers.

Handles FP32/FP16/BF16/INT8/MXFP4 conversions with stochastic rounding
to preserve unbiased gradient estimates across precision boundaries.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Set

import numpy as np


class PrecisionFormat(Enum):
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"
    MXFP4 = "mxfp4"


@dataclass(frozen=True)
class DeviceProfile:
    """Hardware capability profile for precision selection."""
    name: str
    vram_gb: float
    supported_formats: Set[PrecisionFormat]
    native_accumulation: PrecisionFormat
    peak_bandwidth_gbps: float
    tensor_core_formats: Set[PrecisionFormat] = field(default_factory=set)

    @property
    def supports_bf16(self) -> bool:
        return PrecisionFormat.BF16 in self.supported_formats


V100_PROFILE = DeviceProfile(
    name="Tesla V100 32GB",
    vram_gb=32.0,
    supported_formats={
        PrecisionFormat.FP32, PrecisionFormat.FP16, PrecisionFormat.INT8,
    },
    native_accumulation=PrecisionFormat.FP32,
    peak_bandwidth_gbps=900.0,
    tensor_core_formats={PrecisionFormat.FP16},
)

RTX5070TI_PROFILE = DeviceProfile(
    name="RTX 5070 Ti 16GB",
    vram_gb=16.0,
    supported_formats={
        PrecisionFormat.FP32, PrecisionFormat.FP16, PrecisionFormat.BF16,
        PrecisionFormat.INT8, PrecisionFormat.MXFP4,
    },
    native_accumulation=PrecisionFormat.FP32,
    peak_bandwidth_gbps=896.0,
    tensor_core_formats={
        PrecisionFormat.FP16, PrecisionFormat.BF16,
        PrecisionFormat.INT8, PrecisionFormat.MXFP4,
    },
)

# Bytes per element for each format
_BYTES_PER_ELEMENT: Dict[PrecisionFormat, float] = {
    PrecisionFormat.FP32: 4.0,
    PrecisionFormat.FP16: 2.0,
    PrecisionFormat.BF16: 2.0,
    PrecisionFormat.INT8: 1.0,
    PrecisionFormat.MXFP4: 0.5,
}

_NUMPY_DTYPES: Dict[PrecisionFormat, np.dtype] = {
    PrecisionFormat.FP32: np.float32,
    PrecisionFormat.FP16: np.float16,
    PrecisionFormat.INT8: np.int8,
}


class PrecisionManager:
    """Manages tensor precision conversions with stochastic rounding."""

    def __init__(self, device: Optional[DeviceProfile] = None):
        self._device = device
        self._rng = np.random.default_rng()

    @property
    def device(self) -> Optional[DeviceProfile]:
        return self._device

    def convert(self, data: np.ndarray, target: PrecisionFormat,
                stochastic: bool = False) -> np.ndarray:
        """
        Convert tensor to target precision.

        Args:
            data: Source tensor.
            target: Target precision format.
            stochastic: Use stochastic rounding for downcast.

        Returns:
            Converted tensor.
        """
        if target == PrecisionFormat.MXFP4:
            return self._to_mxfp4(data, stochastic)
        if target == PrecisionFormat.BF16:
            return self._to_bf16(data, stochastic)
        if target == PrecisionFormat.INT8:
            return self._to_int8(data, stochastic)

        target_dtype = _NUMPY_DTYPES.get(target, np.float32)
        if stochastic and data.dtype != target_dtype:
            return self.stochastic_round(data, target_dtype)
        return data.astype(target_dtype)

    def stochastic_round(self, data: np.ndarray, target_dtype: np.dtype) -> np.ndarray:
        """
        Stochastic rounding: P(round up) = (x - floor(x)) / (ceil(x) - floor(x)).
        Ensures E[round(x)] = x, preserving unbiased gradient estimates.

        Args:
            data: Source tensor in higher precision.
            target_dtype: Target numpy dtype.

        Returns:
            Stochastically rounded tensor.
        """
        down = data.astype(target_dtype).astype(data.dtype)
        up = np.nextafter(down, np.inf).astype(target_dtype).astype(data.dtype)
        span = up - down
        mask = span != 0
        prob = np.zeros_like(data)
        prob[mask] = (data[mask] - down[mask]) / span[mask]
        choices = self._rng.random(data.shape) < prob
        result = np.where(choices, up, down)
        return result.astype(target_dtype)

    def _to_bf16(self, data: np.ndarray, stochastic: bool) -> np.ndarray:
        """Convert to BF16 via FP32 truncation of mantissa bits."""
        fp32 = data.astype(np.float32)
        raw = fp32.view(np.uint32)
        if stochastic:
            noise = self._rng.integers(0, 1 << 16, size=data.shape, dtype=np.uint32)
            raw = raw + (noise & 0xFFFF)
        truncated = (raw >> 16).astype(np.uint16)
        return truncated

    def bf16_to_fp32(self, data: np.ndarray) -> np.ndarray:
        """Restore BF16 (stored as uint16) back to FP32."""
        padded = data.astype(np.uint32) << 16
        return padded.view(np.float32)

    def _to_int8(self, data: np.ndarray, stochastic: bool) -> np.ndarray:
        """Per-tensor symmetric INT8 quantization."""
        fp32 = data.astype(np.float32)
        amax = np.abs(fp32).max()
        if amax == 0:
            return np.zeros(data.shape, dtype=np.int8)
        scale = 127.0 / amax
        scaled = fp32 * scale
        if stochastic:
            noise = self._rng.random(data.shape).astype(np.float32) - 0.5
            scaled = scaled + noise
        return np.clip(np.round(scaled), -127, 127).astype(np.int8)

    def _to_mxfp4(self, data: np.ndarray, stochastic: bool) -> np.ndarray:
        """
        MXFP4 quantization (4-bit, block size 32).
        Packs two 4-bit values per byte. Returns uint8 array of half the
        element count, with per-block shared exponents prepended.
        """
        fp32 = data.astype(np.float32).ravel()
        block_size = 32
        pad_len = (-len(fp32)) % block_size
        if pad_len:
            fp32 = np.concatenate([fp32, np.zeros(pad_len, dtype=np.float32)])
        blocks = fp32.reshape(-1, block_size)
        block_max = np.abs(blocks).max(axis=1, keepdims=True)
        block_max = np.maximum(block_max, 1e-12)
        scale = 7.0 / block_max
        scaled = blocks * scale
        if stochastic:
            noise = self._rng.random(scaled.shape).astype(np.float32) - 0.5
            scaled = scaled + noise
        quantized = np.clip(np.round(scaled), -7, 7).astype(np.int8)
        # Pack pairs into uint8: high nibble + low nibble
        flat = quantized.ravel()
        even = (flat[0::2].astype(np.uint8) & 0x0F)
        odd = (flat[1::2].astype(np.uint8) & 0x0F) << 4
        packed = even | odd
        shared_exp = np.log2(block_max.ravel() + 1e-12).astype(np.int8)
        return np.concatenate([shared_exp.view(np.uint8), packed])

    def mxfp4_to_fp32(self, packed: np.ndarray, num_elements: int) -> np.ndarray:
        """Restore MXFP4 packed data to FP32."""
        block_size = 32
        total = num_elements + ((-num_elements) % block_size)
        n_blocks = total // block_size
        shared_exp = packed[:n_blocks].view(np.int8).astype(np.float32)
        payload = packed[n_blocks:]
        even = (payload & 0x0F).astype(np.int8)
        even = np.where(even > 7, even - 16, even).astype(np.float32)
        odd = ((payload >> 4) & 0x0F).astype(np.int8)
        odd = np.where(odd > 7, odd - 16, odd).astype(np.float32)
        interleaved = np.empty(len(payload) * 2, dtype=np.float32)
        interleaved[0::2] = even
        interleaved[1::2] = odd
        blocks = interleaved[:total].reshape(n_blocks, block_size)
        block_max = np.power(2.0, shared_exp).reshape(-1, 1)
        return (blocks / 7.0 * block_max).ravel()[:num_elements]

    def optimal_format(self, tensor_bytes: int,
                       bandwidth_gbps: float,
                       latency_budget_ms: float) -> PrecisionFormat:
        """
        Select optimal wire format given bandwidth and latency constraints.

        Args:
            tensor_bytes: Size of tensor in FP32 bytes.
            bandwidth_gbps: Available link bandwidth.
            latency_budget_ms: Maximum acceptable transfer time.

        Returns:
            Best precision format that fits within the budget.
        """
        fp32_elements = tensor_bytes / 4
        bandwidth_bytes_per_ms = (bandwidth_gbps * 1e9 / 8) / 1000

        candidates = [
            PrecisionFormat.FP32,
            PrecisionFormat.FP16,
            PrecisionFormat.BF16,
            PrecisionFormat.INT8,
            PrecisionFormat.MXFP4,
        ]

        if self._device:
            candidates = [f for f in candidates if f in self._device.supported_formats]

        for fmt in reversed(candidates):
            wire_bytes = fp32_elements * _BYTES_PER_ELEMENT[fmt]
            transfer_ms = wire_bytes / bandwidth_bytes_per_ms
            if transfer_ms <= latency_budget_ms:
                return fmt

        return candidates[-1] if candidates else PrecisionFormat.MXFP4

    @staticmethod
    def bytes_per_element(fmt: PrecisionFormat) -> float:
        return _BYTES_PER_ELEMENT[fmt]
