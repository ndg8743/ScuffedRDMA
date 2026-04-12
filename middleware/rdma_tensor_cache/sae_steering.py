"""
Sparse Autoencoder (SAE) feature storage and model steering.

Stores learned SAE features as sparse vectors and applies feature-level
clamping to steer model behavior without fine-tuning. SAE features are
inherently sparse, making them efficient to transfer over RDMA.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# Upper bounds for wire-parsed sparse vectors. These are defense-in-depth
# against crafted peers: a header claiming nnz=2^31-1 would otherwise
# walk off the end of the data buffer in from_bytes().
MAX_SPARSE_NNZ = 10_000_000      # 10M nonzeros — fits any realistic SAE feature
MAX_SPARSE_DIM = 1_000_000_000   # 1B dimensions — loose upper bound


@dataclass
class SparseVector:
    """Sparse representation: only store nonzero indices and values."""
    indices: np.ndarray
    values: np.ndarray
    dim: int

    def to_dense(self) -> np.ndarray:
        dense = np.zeros(self.dim, dtype=np.float32)
        if len(self.indices) > 0:
            dense[self.indices] = self.values
        return dense

    @classmethod
    def from_dense(cls, dense: np.ndarray, threshold: float = 1e-6) -> 'SparseVector':
        mask = np.abs(dense) > threshold
        return cls(
            indices=np.where(mask)[0].astype(np.int32),
            values=dense[mask].astype(np.float32),
            dim=len(dense),
        )

    def to_bytes(self) -> bytes:
        header = np.array([self.dim, len(self.indices)], dtype=np.int32).tobytes()
        return header + self.indices.tobytes() + self.values.tobytes()

    @classmethod
    def from_bytes(cls, data: bytes) -> 'SparseVector':
        if len(data) < 8:
            raise ValueError(f"sparse vector header truncated: {len(data)} bytes")
        header = np.frombuffer(data[:8], dtype=np.int32)
        dim, nnz = int(header[0]), int(header[1])
        if not 0 <= nnz <= MAX_SPARSE_NNZ:
            raise ValueError(f"sparse vector nnz out of range: {nnz}")
        if not 0 <= dim <= MAX_SPARSE_DIM:
            raise ValueError(f"sparse vector dim out of range: {dim}")
        idx_end = 8 + nnz * 4
        val_end = idx_end + nnz * 4
        if val_end > len(data):
            raise ValueError(
                f"sparse vector truncated: need {val_end} bytes, got {len(data)}"
            )
        indices = np.frombuffer(data[8:idx_end], dtype=np.int32)
        values = np.frombuffer(data[idx_end:val_end], dtype=np.float32)
        return cls(indices=indices, values=values, dim=dim)

    @property
    def sparsity(self) -> float:
        return 1.0 - len(self.indices) / self.dim if self.dim > 0 else 1.0

    @property
    def nnz(self) -> int:
        return len(self.indices)


class SAEFeatureStore:
    """
    Storage and retrieval of SAE feature dictionaries.

    Each feature is a sparse vector representing a learned direction
    in activation space. Features are keyed by (layer, feature_idx).
    """

    def __init__(self, feature_dim: int, transport: Any = None):
        """
        Args:
            feature_dim: Dimensionality of each feature vector.
            transport: Optional RDMA transport for remote sync.
        """
        self._dim = feature_dim
        self._transport = transport
        self._features: Dict[Tuple[int, int], SparseVector] = {}
        self._labels: Dict[Tuple[int, int], str] = {}

    @property
    def feature_dim(self) -> int:
        return self._dim

    def store_feature(self, layer: int, feature_idx: int,
                      direction: np.ndarray, label: str = "") -> None:
        """
        Store an SAE feature direction.

        Args:
            layer: Layer index where the feature was extracted.
            feature_idx: Feature index within the SAE dictionary.
            direction: Dense feature direction vector.
            label: Human-readable label for the feature.
        """
        key = (layer, feature_idx)
        self._features[key] = SparseVector.from_dense(direction)
        if label:
            self._labels[key] = label

    def get_feature(self, layer: int, feature_idx: int) -> Optional[SparseVector]:
        return self._features.get((layer, feature_idx))

    def get_dense(self, layer: int, feature_idx: int) -> Optional[np.ndarray]:
        sv = self.get_feature(layer, feature_idx)
        return sv.to_dense() if sv is not None else None

    def list_features(self, layer: Optional[int] = None) -> List[Tuple[int, int, str]]:
        """List stored features, optionally filtered by layer."""
        result = []
        for (l, f), sv in self._features.items():
            if layer is not None and l != layer:
                continue
            label = self._labels.get((l, f), "")
            result.append((l, f, label))
        return sorted(result)

    def batch_store(self, layer: int, directions: np.ndarray,
                    labels: Optional[List[str]] = None) -> int:
        """
        Store a batch of feature directions for a layer.

        Args:
            layer: Layer index.
            directions: (num_features, feature_dim) array.
            labels: Optional label per feature.

        Returns:
            Number of features stored.
        """
        n = directions.shape[0]
        for i in range(n):
            label = labels[i] if labels and i < len(labels) else ""
            self.store_feature(layer, i, directions[i], label)
        return n

    def sync_to_remote(self, layer: int, feature_idx: int) -> bool:
        """Send a feature to the remote store via transport."""
        if self._transport is None:
            return False
        sv = self.get_feature(layer, feature_idx)
        if sv is None:
            return False
        payload = sv.to_bytes()
        try:
            self._transport.send(payload)
            return True
        except Exception:
            return False

    def sync_from_remote(self, layer: int, feature_idx: int) -> bool:
        """Receive a feature from the remote store."""
        if self._transport is None:
            return False
        try:
            data = self._transport.recv(65536)
        except (OSError, TimeoutError):
            return False
        try:
            sv = SparseVector.from_bytes(data)
        except ValueError:
            # Malformed header or truncated payload — see MAX_SPARSE_* bounds
            # in from_bytes(). Swallowing MemoryError or IndexError would hide
            # real bugs, so only the deliberate ValueError path returns False.
            return False
        self._features[(layer, feature_idx)] = sv
        return True

    @property
    def total_features(self) -> int:
        return len(self._features)

    @property
    def avg_sparsity(self) -> float:
        if not self._features:
            return 1.0
        return float(np.mean([sv.sparsity for sv in self._features.values()]))


def steer_model(activations: np.ndarray,
                features: Dict[int, float],
                feature_store: SAEFeatureStore,
                layer: int) -> np.ndarray:
    """
    Steer model activations by clamping SAE features.

    Adds or removes feature directions from the residual stream
    without fine-tuning. Each feature_idx maps to a clamp value:
      positive = amplify the feature
      negative = suppress the feature
      zero     = remove entirely

    Args:
        activations: (seq_len, hidden_dim) activation tensor.
        features: {feature_idx: clamp_value} mapping.
        feature_store: Store containing feature directions.
        layer: Layer index for feature lookup.

    Returns:
        Modified activations.
    """
    result = activations.astype(np.float32).copy()

    for feat_idx, clamp_val in features.items():
        direction = feature_store.get_dense(layer, feat_idx)
        if direction is None:
            continue

        norm = np.linalg.norm(direction)
        if norm < 1e-12:
            continue
        unit = direction / norm

        # Project activations onto feature direction
        proj = result @ unit
        # Remove current projection, add clamped version
        result -= proj[:, np.newaxis] * unit[np.newaxis, :]
        result += (clamp_val * unit)[np.newaxis, :]

    return result
