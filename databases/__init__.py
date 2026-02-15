"""
RDMA Tensor Database.

Precision-aware tensor storage and transport for distributed LLM inference.
Supports pluggable backends (pyverbs on Linux, TCP simulation on Windows)
with adaptive quantization, stochastic rounding, and predictive prefetching.
"""

from .precision import PrecisionFormat, DeviceProfile, PrecisionManager
from .precision import V100_PROFILE, RTX5070TI_PROFILE
from .prefetch import AccessPattern, PrefetchEngine
from .quantization import AdaptiveQuantizer
from .cache import RdmaTensorCache
from .connector import RDMAKVCacheConnector, TensorClassifier
from .sae_steering import SAEFeatureStore, steer_model
from .config import DatabaseConfig

__all__ = [
    'PrecisionFormat',
    'DeviceProfile',
    'PrecisionManager',
    'V100_PROFILE',
    'RTX5070TI_PROFILE',
    'AccessPattern',
    'PrefetchEngine',
    'AdaptiveQuantizer',
    'RdmaTensorCache',
    'RDMAKVCacheConnector',
    'TensorClassifier',
    'SAEFeatureStore',
    'steer_model',
    'DatabaseConfig',
]

__version__ = '0.1.0'
