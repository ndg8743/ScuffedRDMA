import numpy as np
import pytest

from middleware.rdma_tensor_cache.scuffed_quant import CompressedKV, ScuffedQuant


@pytest.fixture(scope="module")
def sq64():
    return ScuffedQuant(dim=64, bits=3, qjl_dim=256, seed=42)


def _keys(n=512, d=64, seed=0):
    return np.random.RandomState(seed).randn(n, d).astype(np.float32)


def test_pack_unpack_roundtrip_exact(sq64):
    c = sq64.compress(_keys())
    c2 = CompressedKV.unpack(c.pack())
    assert np.array_equal(c.indices, c2.indices)
    assert np.array_equal(c.qjl_signs, c2.qjl_signs)
    assert np.array_equal(c.norms, c2.norms)
    assert np.array_equal(c.residual_norms, c2.residual_norms)
    assert (c2.n_vectors, c2.dim, c2.bits, c2.qjl_dim) == (c.n_vectors, c.dim, c.bits, c.qjl_dim)
    # decompression and scores identical after the round trip
    q = _keys(4, 64, seed=9)
    assert np.array_equal(sq64.decompress(c), sq64.decompress(c2))
    assert np.array_equal(sq64.attention_scores(q, c), sq64.attention_scores(q, c2))


@pytest.mark.parametrize("dim,bits,qjl", [(64, 2, 64), (64, 3, 256), (128, 4, 256), (96, 3, 64)])
def test_nbytes_matches_wire(dim, bits, qjl):
    sq = ScuffedQuant(dim=dim, bits=bits, qjl_dim=qjl, seed=1)
    c = sq.compress(_keys(37, dim, seed=2))  # odd count exercises bit padding
    wire = c.pack()
    assert c.nbytes == len(wire) == c.packed_bytes()
    assert c.unpacked_nbytes > c.nbytes
    assert CompressedKV.unpack(wire).indices.shape == (37, c.d_pad)


def test_compression_ratio_from_packed_bytes(sq64):
    n = 1024
    c = sq64.compress(_keys(n))
    payload = c.packed_bytes()
    fp32 = n * 64 * 4
    fp16 = n * 64 * 2
    # 3-bit indices (24 B) + 256 sign bits (32 B) + two fp32 norms (8 B) = 64 B per vector
    assert payload - 20 == n * 64
    assert abs(fp32 / payload - 4.0) < 0.01
    assert abs(fp16 / payload - 2.0) < 0.01
    assert abs(sq64.compression_ratio(n) - 4.0) < 1e-9


def test_qjl_reduces_inner_product_error(sq64):
    k = _keys(2048, 64, seed=3)
    q = _keys(32, 64, seed=4)
    c = sq64.compress(k)
    exact = q @ k.T
    naive = q @ sq64.decompress(c).T
    corrected = sq64.attention_scores(q, c)
    err_naive = np.abs(exact - naive).mean()
    err_qjl = np.abs(exact - corrected).mean()
    assert err_qjl < err_naive


def test_unpack_rejects_garbage(sq64):
    c = sq64.compress(_keys(8))
    with pytest.raises(ValueError):
        CompressedKV.unpack(b"XXXX" + c.pack()[4:])
    with pytest.raises(ValueError):
        CompressedKV.unpack(c.pack() + b"\x00")


def test_per_architecture_entry_points_still_work():
    sq = ScuffedQuant(dim=32, bits=3, qjl_dim=64)
    state = np.random.RandomState(0).randn(2, 16, 32).astype(np.float32)
    c = sq.compress_ssm_state(state)
    assert c.n_vectors == 32
    act = np.random.RandomState(1).randn(4, 8, 32).astype(np.float32)
    assert sq.compress_expert_activation(act).n_vectors == 32
    with pytest.raises(ValueError):
        sq.compress_ssm_state(np.zeros((2, 3, 31), np.float32))
