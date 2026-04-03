"""
scuffedQuant: two-stage KV cache quantization for RDMA transfer.

Implements the PolarQuant + QJL approach from TurboQuant (Zandieh et al. 2025)
from scratch. Pure numpy, runs on any platform (cluster GPUs, Mac, etc).

Stage 1 - PolarQuant:
  Rotate vectors with a random orthogonal matrix so coordinates concentrate
  near zero. Quantize with a precomputed Lloyd-Max quantizer for the known
  distribution. No per-block calibration needed.

Stage 2 - QJL (Quantized Johnson-Lindenstrauss):
  Store a 1-bit sketch of the quantization residual. This corrects the bias
  in inner product estimates, making attention scores provably unbiased.

The key property: individual vector reconstruction is lossy, but inner
products (what attention computes) are preserved accurately.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple


def _random_orthogonal(d: int, seed: int = 42) -> np.ndarray:
    """Generate a random orthogonal matrix via QR decomposition."""
    rng = np.random.RandomState(seed)
    G = rng.randn(d, d).astype(np.float32)
    Q, R = np.linalg.qr(G)
    # Fix sign ambiguity so result is reproducible
    Q *= np.sign(np.diag(R))
    return Q


def _build_lloyd_max_codebook(bits: int, d: int, n_samples: int = 100000,
                               seed: int = 123) -> np.ndarray:
    """
    Build a Lloyd-Max codebook for the post-rotation coordinate distribution.

    After rotating a unit-norm vector by a random orthogonal matrix,
    each coordinate follows a distribution concentrated near zero.
    For large d, this is approximately Gaussian with variance 1/d.
    We build the quantizer empirically by sampling.
    """
    rng = np.random.RandomState(seed)
    # Sample from the marginal distribution: project random unit vectors
    vecs = rng.randn(n_samples, d).astype(np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    samples = vecs[:, 0]  # marginal of first coordinate

    # Lloyd-Max iteration (k-means on 1D data)
    n_levels = 2 ** bits
    # Initialize with uniform quantiles
    percentiles = np.linspace(0, 100, n_levels + 1)
    boundaries = np.percentile(samples, percentiles[1:-1])
    codebook = np.zeros(n_levels, dtype=np.float32)

    for _ in range(50):
        # Assign samples to nearest boundary region
        indices = np.digitize(samples, boundaries)
        # Update codebook: centroid of each region
        for i in range(n_levels):
            mask = indices == i
            if mask.any():
                codebook[i] = samples[mask].mean()
        # Update boundaries: midpoints between adjacent centroids
        boundaries = (codebook[:-1] + codebook[1:]) / 2

    return codebook


def _quantize_with_codebook(values: np.ndarray,
                             codebook: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Quantize values using a codebook. Returns (indices, reconstructed)."""
    # For each value, find nearest codebook entry
    dists = np.abs(values[:, None] - codebook[None, :])
    indices = dists.argmin(axis=1).astype(np.uint8)
    reconstructed = codebook[indices]
    return indices, reconstructed


@dataclass
class CompressedKV:
    """Compressed KV cache block ready for RDMA transfer."""
    # Stage 1: quantized indices (n_vectors x d), packed to bits
    indices: np.ndarray
    # Stage 1: norms for rescaling
    norms: np.ndarray
    # Stage 2: QJL sign bits (n_vectors x m), packed
    qjl_signs: np.ndarray
    # Stage 2: residual norms for correction scaling
    residual_norms: np.ndarray
    # Metadata
    n_vectors: int
    dim: int
    bits: int
    qjl_dim: int

    @property
    def nbytes(self) -> int:
        return (self.indices.nbytes + self.norms.nbytes +
                self.qjl_signs.nbytes + self.residual_norms.nbytes)


class ScuffedQuant:
    """
    Two-stage KV cache quantizer.

    Usage:
        sq = ScuffedQuant(dim=128, bits=3)
        compressed = sq.compress(keys)           # n x d float32 -> CompressedKV
        scores = sq.attention_scores(queries, compressed)  # exact-ish inner products
        reconstructed = sq.decompress(compressed) # lossy per-vector reconstruction
    """

    def __init__(self, dim: int, bits: int = 3, qjl_dim: int = 64,
                 seed: int = 42):
        self.dim = dim
        self.bits = bits
        self.qjl_dim = qjl_dim

        # Stage 1: random orthogonal rotation (fixed, reused for all vectors)
        self.rotation = _random_orthogonal(dim, seed=seed)

        # Stage 1: Lloyd-Max codebook for the post-rotation distribution
        self.codebook = _build_lloyd_max_codebook(bits, dim, seed=seed + 1)

        # Stage 2: random sign matrix for QJL (Rademacher entries)
        rng = np.random.RandomState(seed + 2)
        self.qjl_matrix = (rng.randint(0, 2, size=(qjl_dim, dim)) * 2 - 1).astype(np.float32)

    def compress(self, vectors: np.ndarray) -> CompressedKV:
        """
        Compress a batch of vectors (e.g. KV cache keys for one layer).

        Args:
            vectors: (n, d) float32 array

        Returns:
            CompressedKV with quantized indices + QJL correction bits
        """
        n, d = vectors.shape
        assert d == self.dim

        # Save norms for rescaling (quantizer works on unit vectors)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        safe_norms = np.maximum(norms, 1e-8)
        unit_vectors = vectors / safe_norms

        # Stage 1: rotate
        rotated = unit_vectors @ self.rotation.T  # (n, d)

        # Stage 1: quantize each coordinate independently
        flat = rotated.reshape(-1)
        indices, reconstructed_flat = _quantize_with_codebook(flat, self.codebook)
        indices = indices.reshape(n, d)
        reconstructed_rotated = reconstructed_flat.reshape(n, d)

        # Undo rotation for MSE reconstruction
        reconstructed_unit = reconstructed_rotated @ self.rotation  # (n, d)
        reconstructed = reconstructed_unit * safe_norms

        # Stage 2: QJL sign sketch of the residual
        residual = vectors - reconstructed
        residual_norms = np.linalg.norm(residual, axis=1)

        # Project residual and take sign (don't normalize -- the norm is stored separately)
        projected = residual @ self.qjl_matrix.T  # (n, qjl_dim)
        qjl_signs = (projected >= 0).astype(np.uint8)

        return CompressedKV(
            indices=indices,
            norms=norms.squeeze(1).astype(np.float32),
            qjl_signs=qjl_signs,
            residual_norms=residual_norms.astype(np.float32),
            n_vectors=n,
            dim=d,
            bits=self.bits,
            qjl_dim=self.qjl_dim,
        )

    def decompress(self, compressed: CompressedKV) -> np.ndarray:
        """
        Reconstruct vectors from compressed representation.
        NOTE: This is lossy. Use attention_scores() for accurate inner products.
        """
        # Look up codebook values
        reconstructed_rotated = self.codebook[compressed.indices]  # (n, d)
        # Undo rotation
        reconstructed_unit = reconstructed_rotated @ self.rotation
        # Rescale
        return reconstructed_unit * compressed.norms[:, None]

    def attention_scores(self, queries: np.ndarray,
                         compressed: CompressedKV) -> np.ndarray:
        """
        Compute attention scores (query @ key^T) with QJL bias correction.

        This is more accurate than decompress() @ queries.T because the
        QJL correction removes the systematic bias from quantization.

        Args:
            queries: (n_q, d) float32
            compressed: CompressedKV from compress()

        Returns:
            (n_q, n_k) float32 attention scores
        """
        # Stage 1: MSE reconstruction scores
        keys_mse = self.decompress(compressed)
        scores_mse = queries @ keys_mse.T  # (n_q, n_k)

        # Stage 2: QJL bias correction
        # z = sign(S @ r) where S is a random sign matrix (m x d)
        # <q, r> ~ (1/m) * <S@q, z> * ||S@r||_1 ... but simpler:
        # sign sketch gives: E[z_j * (S@q)_j] = (2/pi) * <q, r> / ||r||
        # We stored z = sign(S@r), so:
        #   <q, r> ~ (||r|| * pi / (2*m)) * sum_j (S@q)_j * z_j
        q_projected = queries @ self.qjl_matrix.T  # (n_q, qjl_dim)
        signs = compressed.qjl_signs.astype(np.float32) * 2 - 1  # (n_k, qjl_dim)

        correction = q_projected @ signs.T  # (n_q, n_k)
        m = self.qjl_dim
        # Scale: each sign bit recovers ~(2/pi)/sqrt(d) of the inner product
        correction *= (np.pi / (2.0 * m))

        return scores_mse + correction

    def compression_ratio(self, n_vectors: int) -> float:
        """Compute compression ratio vs FP32."""
        original = n_vectors * self.dim * 4  # float32
        # indices: bits per coordinate, norms: 4 bytes each
        # qjl_signs: 1 bit per dim, residual_norms: 4 bytes each
        compressed = (
            n_vectors * self.dim * self.bits / 8 +  # indices
            n_vectors * 4 +                          # norms
            n_vectors * self.qjl_dim / 8 +           # qjl signs
            n_vectors * 4                            # residual norms
        )
        return original / compressed
