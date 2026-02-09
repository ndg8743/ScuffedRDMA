"""Dual-path RDMA routing with hot/cold QP pools."""
from wfa_classifier import TensorClassifier


class DualPathRDMA:
    def __init__(self, ctx, num_hot_qps=4, num_cold_qps=2):
        # Hot path: dedicated QPs, polled completions
        self.hot_qps = [self._create_qp(ctx, poll=True)
                        for _ in range(num_hot_qps)]
        # Cold path: shared QPs, event-driven completions
        self.cold_qps = [self._create_qp(ctx, poll=False)
                         for _ in range(num_cold_qps)]
        self.cold_batch = []  # Accumulate for batching

    def transfer(self, tensor, classification):
        if classification == TensorClassifier.HOT:
            qp = self._get_least_loaded(self.hot_qps)
            self._rdma_write_immediate(qp, tensor)  # Sub-5us
        else:
            self.cold_batch.append(tensor)
            if len(self.cold_batch) >= 8:
                self._flush_cold_batch()
