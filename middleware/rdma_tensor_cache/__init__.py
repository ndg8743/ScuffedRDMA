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
from .vllm_connector import RDMAKVCacheConnector, TensorClassifier
from .sae_steering import SAEFeatureStore, steer_model
from .dual_qp_pool import DualQPPool, QueueSelection, QueueStats, RegisteredBuffer
from .wfa_classifier import WFAClassifier, Phase
from .pmp_controller import PMPController

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
    'DualQPPool',
    'QueueSelection',
    'QueueStats',
    'RegisteredBuffer',
    'WFAClassifier',
    'Phase',
    'PMPController',
]

__version__ = '0.1.0'
