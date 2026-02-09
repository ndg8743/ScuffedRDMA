"""
RDMA Tensor Cache

Precision-aware tensor caching over RDMA transports for distributed
LLM inference. Supports pluggable backends (pyverbs on Linux,
TCP simulation on Windows) with adaptive quantization and prefetching.
"""

from .precision import PrecisionFormat, DeviceProfile, PrecisionManager
from .precision import V100_PROFILE, RTX5070TI_PROFILE
from .prefetch import AccessPattern, PrefetchEngine
from .quantization import AdaptiveQuantizer
from .cache import RdmaTensorCache
from .vllm_connector import NeumannKVCacheConnector
from .sae_steering import SAEFeatureStore, steer_model

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
    'NeumannKVCacheConnector',
    'SAEFeatureStore',
    'steer_model',
]

__version__ = '0.1.0'
