"""
scuffedQuant: two-stage KV cache compression.

Stage 1 (rotate + scalar quantize): normalize each vector, apply a
randomized Walsh-Hadamard rotation (random +-1 diagonal, then the fast
WHT) so every coordinate follows the same near-Gaussian marginal, then
quantize each coordinate with a Lloyd-Max codebook precomputed for that
marginal. `bits` bits per coordinate, no calibration data. Plain
Cartesian coordinates; there is no polar transform in this code.

Stage 2 (QJL residual sketch): store sign(S r / ||r||) for the
quantization residual r, with S a random +-1 matrix of shape
(qjl_dim, dim), i.e. qjl_dim sign bits per vector (benchmarks use
qjl_dim = 256), plus ||r||. attention_scores() adds the QJL inner
product estimate to remove the bias of the stage-1 reconstruction.

Individual vectors are lossy; inner products (attention scores) are
what the sketch keeps accurate.

Wire format: CompressedKV.pack() bit-packs indices at `bits` bits per
coordinate and signs at 1 bit each (np.packbits); CompressedKV.nbytes
and packed_bytes() equal len(pack()).

References:
  Zandieh et al., "TurboQuant: Online Vector Quantization with
  Near-optimal Distortion Rate", arXiv:2504.19874 (rotate, scalar
  quantize, QJL on the residual).
  Zandieh, Daliri, Han, "QJL: 1-Bit Quantized JL Transform for KV
  Cache Quantization with Zero Overhead", arXiv:2406.03482 (the sign
  sketch and its unbiased inner-product estimator).
"""

import struct

import numpy as np
from dataclasses import dataclass
from typing import Tuple


# --- Stage 1: randomized Hadamard rotation + Lloyd-Max scalar quantizer ---

def _walsh_hadamard(x: np.ndarray) -> np.ndarray:
    """
    Fast Walsh-Hadamard transform, in-place.
    O(d log d) instead of O(d^2) for a full rotation matrix.
    Input length must be a power of 2.
    """
    d = x.shape[-1]
    h = 1
    while h < d:
        # Butterfly operation on pairs separated by h
        for i in range(0, d, h * 2):
            a = x[..., i:i+h].copy()
            b = x[..., i+h:i+2*h].copy()
            x[..., i:i+h] = a + b
            x[..., i+h:i+2*h] = a - b
        h *= 2
    x /= np.sqrt(d)
    return x


def _random_signs(d: int, seed: int) -> np.ndarray:
    """Random +1/-1 diagonal for randomized Hadamard."""
    rng = np.random.RandomState(seed)
    return (rng.randint(0, 2, size=d) * 2 - 1).astype(np.float32)


def _pad_to_power_of_2(x: np.ndarray) -> Tuple[np.ndarray, int]:
    """Pad last dimension to next power of 2."""
    d = x.shape[-1]
    d2 = 1
    while d2 < d:
        d2 *= 2
    if d2 == d:
        return x, d
    pad_width = [(0, 0)] * (x.ndim - 1) + [(0, d2 - d)]
    return np.pad(x, pad_width), d


def _build_codebook(bits: int, d: int, n_samples: int = 200000,
                    seed: int = 123) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build Lloyd-Max codebook for the post-rotation distribution.

    After a randomized Hadamard rotation, each coordinate of a unit
    vector is approximately Gaussian with mean 0 and variance 1/d.
    The codebook is precomputed once and reused for all vectors.

    Returns (sorted_codebook, boundaries).
    """
    rng = np.random.RandomState(seed)

    # Sample the marginal: first coordinate of random unit vectors
    vecs = rng.randn(n_samples, d).astype(np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    samples = vecs[:, 0]

    n_levels = 2 ** bits

    # Initialize codebook from uniform quantiles
    pcts = np.linspace(0, 100, n_levels + 1)
    boundaries = np.percentile(samples, pcts[1:-1])
    codebook = np.zeros(n_levels, dtype=np.float32)

    # Lloyd-Max: iterate centroid/boundary updates
    for _ in range(50):
        bins = np.digitize(samples, boundaries)
        for i in range(n_levels):
            mask = bins == i
            if mask.any():
                codebook[i] = samples[mask].mean()
        boundaries = (codebook[:-1] + codebook[1:]) / 2

    # Sort for searchsorted
    order = np.argsort(codebook)
    codebook = codebook[order]
    boundaries = (codebook[:-1] + codebook[1:]) / 2

    return codebook, boundaries


def _quantize(values: np.ndarray, codebook: np.ndarray,
              boundaries: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Quantize values using sorted codebook + boundaries.
    O(n log k) via searchsorted instead of O(n * k).
    """
    indices = np.searchsorted(boundaries, values).astype(np.uint8)
    reconstructed = codebook[indices]
    return indices, reconstructed


# --- Stage 2: QJL sign sketch ---

def _qjl_sketch(residual: np.ndarray, S: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute QJL sign sketch of residual vectors.

    residual: (n, d) -- quantization error vectors
    S: (m, d) -- random sign matrix

    Returns:
      signs: (n, m) uint8 -- sign(S @ r_unit) for each vector
      norms: (n,) float32 -- ||r|| for scaling during correction
    """
    norms = np.linalg.norm(residual, axis=1)
    safe_norms = np.maximum(norms, 1e-8)

    # Sketch the unit residual so signs encode direction only
    r_unit = residual / safe_norms[:, None]
    projected = r_unit @ S.T                      # (n, m)
    signs = (projected >= 0).astype(np.uint8)

    return signs, norms.astype(np.float32)


def _qjl_correct(queries: np.ndarray, signs: np.ndarray,
                  residual_norms: np.ndarray, S: np.ndarray) -> np.ndarray:
    """
    Compute QJL inner product correction.

    For jointly Gaussian X, Y with cov(X,Y) = sigma_xy:
      E[sign(X) * Y] = sqrt(2/pi) * sigma_xy / sigma_X

    Applied to X = (S @ r_unit)_j, Y = (S @ q)_j:
      sigma_xy = <r_unit, q>,  sigma_X = 1  (since ||r_unit|| = 1)
      E[z_j * (Sq)_j] = sqrt(2/pi) * <r_unit, q>

    So: <r, q> = ||r|| * sqrt(pi/2) / m * sum_j z_j * (Sq)_j
    """
    m = S.shape[0]
    q_proj = queries @ S.T                        # (n_q, m)
    z = signs.astype(np.float32) * 2 - 1          # (n_k, m): +1/-1
    raw = q_proj @ z.T                            # (n_q, n_k)
    return raw * residual_norms[None, :] * (np.sqrt(np.pi / 2.0) / m)


# --- Main class ---

_PACK_MAGIC = b"SCQ1"
_PACK_VERSION = 1
# magic, version, bits, qjl_dim, n_vectors, dim, d_pad
_PACK_HDR = struct.Struct("<4sBBHIII")


def _pack_uint(values: np.ndarray, bits: int) -> bytes:
    """Pack small unsigned ints (< 2**bits) at `bits` bits each, LSB first."""
    v = np.ascontiguousarray(values, dtype=np.uint8).reshape(-1)
    shifts = np.arange(bits, dtype=np.uint8)
    planes = ((v[:, None] >> shifts) & 1).astype(np.uint8)
    return np.packbits(planes.reshape(-1), bitorder="little").tobytes()


def _unpack_uint(buf: bytes, count: int, bits: int) -> np.ndarray:
    raw = np.frombuffer(buf, dtype=np.uint8)
    planes = np.unpackbits(raw, count=count * bits, bitorder="little").reshape(count, bits)
    weights = (1 << np.arange(bits, dtype=np.uint16)).astype(np.uint16)
    return (planes.astype(np.uint16) * weights).sum(axis=1).astype(np.uint8)


@dataclass
class CompressedKV:
    """Compressed KV cache block. Arrays are unpacked in memory; pack() for the wire."""
    indices: np.ndarray       # (n, d_padded) uint8 codebook indices, values < 2**bits
    norms: np.ndarray         # (n,) float32 original vector norms
    qjl_signs: np.ndarray     # (n, m) uint8 sign bits (0/1)
    residual_norms: np.ndarray  # (n,) float32 residual norms
    n_vectors: int
    dim: int
    bits: int
    qjl_dim: int

    @property
    def d_pad(self) -> int:
        return int(self.indices.shape[1]) if self.indices.ndim == 2 else self.dim

    def packed_bytes(self) -> int:
        """Exact size of pack(): header + norms + residual norms + bit-packed indices + bit-packed signs."""
        n = self.n_vectors
        return (_PACK_HDR.size + 4 * n + 4 * n
                + (n * self.d_pad * self.bits + 7) // 8
                + (n * self.qjl_dim + 7) // 8)

    @property
    def nbytes(self) -> int:
        """Wire size in bytes (bit-packed). Equals len(self.pack())."""
        return self.packed_bytes()

    @property
    def unpacked_nbytes(self) -> int:
        """In-memory size of the unpacked arrays (one byte per index and per sign)."""
        return (self.indices.nbytes + self.norms.nbytes +
                self.qjl_signs.nbytes + self.residual_norms.nbytes)

    def pack(self) -> bytes:
        n, d_pad = self.n_vectors, self.d_pad
        if self.indices.size and int(self.indices.max()) >= (1 << self.bits):
            raise ValueError("index exceeds bit width")
        hdr = _PACK_HDR.pack(_PACK_MAGIC, _PACK_VERSION, self.bits, self.qjl_dim, n, self.dim, d_pad)
        out = b"".join([
            hdr,
            np.ascontiguousarray(self.norms, dtype="<f4").tobytes(),
            np.ascontiguousarray(self.residual_norms, dtype="<f4").tobytes(),
            _pack_uint(self.indices, self.bits),
            np.packbits(np.ascontiguousarray(self.qjl_signs, dtype=np.uint8).reshape(-1),
                        bitorder="little").tobytes(),
        ])
        assert len(out) == self.packed_bytes()
        return out

    @classmethod
    def unpack(cls, buf: bytes) -> "CompressedKV":
        mv = memoryview(buf)
        magic, ver, bits, qjl_dim, n, dim, d_pad = _PACK_HDR.unpack_from(mv, 0)
        if magic != _PACK_MAGIC or ver != _PACK_VERSION:
            raise ValueError("not a scuffedQuant v1 block")
        off = _PACK_HDR.size
        norms = np.frombuffer(mv[off:off + 4 * n], dtype="<f4").astype(np.float32)
        off += 4 * n
        rnorms = np.frombuffer(mv[off:off + 4 * n], dtype="<f4").astype(np.float32)
        off += 4 * n
        ib = (n * d_pad * bits + 7) // 8
        indices = _unpack_uint(bytes(mv[off:off + ib]), n * d_pad, bits).reshape(n, d_pad)
        off += ib
        sb = (n * qjl_dim + 7) // 8
        signs = np.unpackbits(np.frombuffer(mv[off:off + sb], dtype=np.uint8),
                              count=n * qjl_dim, bitorder="little").reshape(n, qjl_dim)
        off += sb
        if off != len(mv):
            raise ValueError(f"trailing bytes: parsed {off}, got {len(mv)}")
        return cls(indices=indices, norms=norms, qjl_signs=signs, residual_norms=rnorms,
                   n_vectors=n, dim=dim, bits=bits, qjl_dim=qjl_dim)


class ScuffedQuant:
    """
    KV cache quantizer: randomized Hadamard rotation + Lloyd-Max codebook + QJL residual sketch.

        sq = ScuffedQuant(dim=128, bits=3)
        compressed = sq.compress(keys)
        scores = sq.attention_scores(queries, compressed)
    """

    def __init__(self, dim: int, bits: int = 3, qjl_dim: int = 64,
                 seed: int = 42):
        self.dim = dim
        self.bits = bits
        self.qjl_dim = qjl_dim

        # Pad dim to power of 2 for Walsh-Hadamard
        self._d_pad = 1
        while self._d_pad < dim:
            self._d_pad *= 2

        # Stage 1: randomized Hadamard = diag(signs) @ WHT
        self._signs = _random_signs(self._d_pad, seed)
        self.codebook, self.boundaries = _build_codebook(bits, self._d_pad, seed=seed + 1)

        # Stage 2: random sign matrix for QJL
        rng = np.random.RandomState(seed + 2)
        self.S = (rng.randint(0, 2, size=(qjl_dim, dim)) * 2 - 1).astype(np.float32)

    def _rotate(self, x: np.ndarray) -> np.ndarray:
        """Randomized Walsh-Hadamard: multiply by signs, then WHT."""
        x = x * self._signs[:x.shape[-1]]
        return _walsh_hadamard(x)

    def _unrotate(self, x: np.ndarray) -> np.ndarray:
        """Inverse: WHT is self-inverse, then multiply by signs."""
        x = _walsh_hadamard(x)
        return x * self._signs[:x.shape[-1]]

    def compress(self, vectors: np.ndarray) -> CompressedKV:
        """Compress (n, dim) float32 vectors."""
        n, d = vectors.shape

        # Normalize to unit vectors (store norms for rescaling)
        norms = np.linalg.norm(vectors, axis=1)
        safe_norms = np.maximum(norms, 1e-8)
        unit = vectors / safe_norms[:, None]

        # Pad and rotate
        padded, _ = _pad_to_power_of_2(unit)
        rotated = self._rotate(padded.copy())

        # Quantize each coordinate
        flat = rotated.reshape(-1)
        indices, recon_flat = _quantize(flat, self.codebook, self.boundaries)
        indices = indices.reshape(n, self._d_pad)
        recon_rotated = recon_flat.reshape(n, self._d_pad)

        # Unrotate and rescale to get MSE reconstruction
        recon_unit = self._unrotate(recon_rotated.copy())[:, :d]
        recon = recon_unit * safe_norms[:, None]

        # QJL sketch of the residual
        residual = vectors - recon
        qjl_signs, residual_norms = _qjl_sketch(residual, self.S)

        return CompressedKV(
            indices=indices, norms=norms.astype(np.float32),
            qjl_signs=qjl_signs, residual_norms=residual_norms,
            n_vectors=n, dim=d, bits=self.bits, qjl_dim=self.qjl_dim,
        )

    def decompress(self, c: CompressedKV) -> np.ndarray:
        """Lossy reconstruction. Use attention_scores() for accurate inner products."""
        recon_rotated = self.codebook[c.indices]
        recon_unit = self._unrotate(recon_rotated.copy())[:, :c.dim]
        return recon_unit * c.norms[:, None]

    def attention_scores(self, queries: np.ndarray, c: CompressedKV) -> np.ndarray:
        """
        Compute query @ key^T with QJL bias correction.

        More accurate than queries @ decompress().T because the QJL
        correction removes systematic quantization bias from inner products.
        """
        scores = queries @ self.decompress(c).T
        scores += _qjl_correct(queries, c.qjl_signs, c.residual_norms, self.S)
        return scores

    def compress_ssm_state(self, state: np.ndarray) -> CompressedKV:
        """
        Compress an SSM hidden state (Mamba-family).

        The state typically arrives shaped (batch, d_state, d_model) or
        (batch, n_layers, d_state, d_model). We flatten every axis except
        the last (which must match self.dim) and delegate to compress().
        """
        if state.shape[-1] != self.dim:
            raise ValueError(
                f"compress_ssm_state: last dim {state.shape[-1]} != {self.dim}")
        flat = state.reshape(-1, self.dim).astype(np.float32, copy=False)
        return self.compress(flat)

    def compress_expert_activation(self, activation: np.ndarray) -> CompressedKV:
        """
        Compress an MoE expert-output activation before all-to-all dispatch.

        Activations are (n_tokens_per_expert, d_model) after routing. If the
        caller passes a 3D (n_experts, n_tokens, d_model) tensor, we flatten
        experts and tokens together; the receiving side re-splits by the
        expert-count it already knows.
        """
        if activation.shape[-1] != self.dim:
            raise ValueError(
                f"compress_expert_activation: last dim {activation.shape[-1]} "
                f"!= {self.dim}")
        flat = activation.reshape(-1, self.dim).astype(np.float32, copy=False)
        return self.compress(flat)

    def _build_hadamard(self, device):
        """Construct a (d_pad, d_pad) normalized Hadamard matrix on `device`.

        Cached per-device so the cost is one-time. The normalization is
        H = W / sqrt(d), which makes H orthonormal (H @ H = I) so a
        single matmul inverts the forward rotation. This replaces the
        butterfly loop in decompress_torch with one BLAS call that
        torch.compile can fuse into a fast autotuned kernel.
        """
        import torch
        attr = f"_hadamard_{device}"
        if hasattr(self, attr):
            return getattr(self, attr)
        d = self._d_pad
        h = torch.tensor([[1.0]], device=device, dtype=torch.float32)
        while h.shape[0] < d:
            h = torch.cat([torch.cat([h, h], dim=1), torch.cat([h, -h], dim=1)], dim=0)
        h = h / (d ** 0.5)
        setattr(self, attr, h)
        return h

    def decompress_torch(self, c: CompressedKV, device: str):
        """
        GPU decompression path using a single Hadamard matmul. Returns a
        (n, dim) float32 tensor on `device`. Eager / non-autotuned.
        """
        import torch
        attr = f"_torch_state_{device}"
        if not hasattr(self, attr):
            codebook = torch.from_numpy(self.codebook).to(device=device, dtype=torch.float32)
            signs = torch.from_numpy(self._signs[:self._d_pad]).to(device=device, dtype=torch.float32)
            setattr(self, attr, (codebook, signs))
        codebook_t, signs_t = getattr(self, attr)
        H = self._build_hadamard(device)

        indices_t = torch.from_numpy(c.indices).to(device=device, dtype=torch.long)
        norms_t = torch.from_numpy(c.norms).to(device=device, dtype=torch.float32)

        x = codebook_t[indices_t]                    # (n, d_pad) gather
        x = x @ H                                    # inverse Hadamard
        x = x * signs_t                              # undo the random sign diag
        x = x[:, :c.dim] * norms_t.unsqueeze(-1)     # truncate + rescale
        return x

    def decompress_torch_autotune(self, c: CompressedKV, device: str, mode: str = "max-autotune"):
        """
        Autotuned decompression. Compiles the inner kernel with
        torch.compile on first call (mode="reduce-overhead" or
        "max-autotune"); subsequent calls reuse the tuned kernel. The
        output is bit-identical to decompress_torch.
        """
        import torch
        attr = f"_torch_state_{device}"
        if not hasattr(self, attr):
            codebook = torch.from_numpy(self.codebook).to(device=device, dtype=torch.float32)
            signs = torch.from_numpy(self._signs[:self._d_pad]).to(device=device, dtype=torch.float32)
            setattr(self, attr, (codebook, signs))
        codebook_t, signs_t = getattr(self, attr)
        H = self._build_hadamard(device)

        compiled_attr = f"_compiled_{device}_{mode}"
        if not hasattr(self, compiled_attr):
            def _kernel(codebook_t, indices_t, H, signs_t, norms_t, dim):
                x = codebook_t[indices_t]
                x = x @ H
                x = x * signs_t
                x = x[:, :dim] * norms_t.unsqueeze(-1)
                return x
            compiled = torch.compile(_kernel, mode=mode, dynamic=False)
            setattr(self, compiled_attr, compiled)
        compiled = getattr(self, compiled_attr)

        indices_t = torch.from_numpy(c.indices).to(device=device, dtype=torch.long)
        norms_t = torch.from_numpy(c.norms).to(device=device, dtype=torch.float32)
        return compiled(codebook_t, indices_t, H, signs_t, norms_t, c.dim)

    def compression_ratio(self, n_vectors: int) -> float:
        """Payload compression ratio vs FP32 (bit-packed sizes, header excluded).

        Vs FP16 the ratio is half of this. For the exact wire size of a
        block use CompressedKV.packed_bytes()."""
        original = n_vectors * self.dim * 4
        compressed = (
            n_vectors * self._d_pad * self.bits / 8 +  # indices
            n_vectors * 4 +                              # norms
            n_vectors * self.qjl_dim / 8 +               # qjl signs
            n_vectors * 4                                # residual norms
        )
        return original / compressed
