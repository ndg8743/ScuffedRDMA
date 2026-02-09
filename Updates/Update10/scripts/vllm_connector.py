"""Adaptive RDMA connector and instrumented KV cache for vLLM."""
import time
from collections import defaultdict
from dual_path_rdma import DualPathRDMA
from wfa_classifier import TensorClassifier


class AdaptiveRDMAConnector:  # extends KVConnectorBase
    def __init__(self, config):
        self.rdma = DualPathRDMA(...)
        self.classifier = TensorClassifier()

    def save_kv_layer(self, layer_id, kv_tensors):
        for block_id, kv in enumerate(kv_tensors):
            cls = self.classifier.classify(
                f"{layer_id}:{block_id}",
                self.access_counts[block_id],
                time.monotonic() - self.last_access[block_id])
            self.rdma.transfer(kv, cls)


class InstrumentedKVCacheManager:  # extends KVCacheManager
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_log = defaultdict(list)

    def allocate_slots(self, request, num_tokens):
        blocks = super().allocate_slots(request, num_tokens)
        for block in blocks:
            self.access_log[block.id].append(
                time.monotonic_ns())
        return blocks
