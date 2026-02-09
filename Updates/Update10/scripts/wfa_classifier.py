"""WFA tensor classifier and workload phase detection."""
import time


class TensorClassifier:
    COLD, WARM, HOT = 0, 1, 2

    def __init__(self, theta1=10, theta2=100, t_idle=0.1):
        self.state = {}  # tensor_id -> (state, last_access)
        self.theta1, self.theta2 = theta1, theta2
        self.t_idle = t_idle

    def classify(self, tensor_id, access_count, elapsed):
        current = self.state.get(tensor_id, (self.COLD, 0))
        if elapsed > self.t_idle:
            new_state = max(self.COLD, current[0] - 1)
        elif access_count > self.theta2:
            new_state = self.HOT
        elif access_count > self.WARM:
            new_state = self.WARM
        else:
            new_state = current[0]
        self.state[tensor_id] = (new_state, time.monotonic())
        return new_state


def detect_phase(input_batch):
    tokens_per_seq = input_batch.num_tokens / input_batch.num_seqs
    return "prefill" if tokens_per_seq > 8 else "decode"
