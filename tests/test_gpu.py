"""
GPU-resident paths. Skipped without CUDA; run on any one machine with an
NVIDIA GPU (desktop under WSL2, Cerberus or Chimera alone) via notebook 08.
"""
import os

import numpy as np
import pytest

pytestmark = pytest.mark.gpu

torch = pytest.importorskip("torch")


def _cuda():
    return torch.device("cuda", int(os.environ.get("SCUFFED_GPU", "0")))


@pytest.mark.parametrize("dtype", ["bfloat16", "float16"])
def test_kv_layout_roundtrip_on_gpu(dtype):
    from middleware.vllm_plugin.kv_layout import block_axis, put_blocks, take_blocks

    dev, tdt = _cuda(), getattr(torch, dtype)
    shape = (2, 64, 16, 8, 64)  # (K/V, blocks, block_size, kv_heads, head_dim)
    src = torch.randn(shape, device=dev).to(tdt)
    dst = torch.zeros(shape, device=dev, dtype=tdt)
    ax = block_axis(shape)
    rng = np.random.default_rng(0)
    a = rng.choice(64, 12, replace=False).tolist()
    b = rng.choice(64, 12, replace=False).tolist()
    blocks = take_blocks(src, a, ax)
    assert blocks.is_cuda
    assert put_blocks(dst, blocks, b, ax) == len(b)
    torch.cuda.synchronize()
    assert torch.equal(dst[:, b], src[:, a])


@pytest.mark.parametrize("codec", ["raw", "scuffedquant"])
def test_codec_roundtrip_from_gpu(codec):
    from middleware.vllm_plugin.kv_codec import decode_kv, encode_kv

    t = torch.randn(2, 4, 16, 8, 64, device=_cuda()).to(torch.bfloat16)
    blob = encode_kv(t, layer="l0", axis=1, block_size=16, num_tokens=64, codec=codec)
    hdr, out = decode_kv(blob, want_torch=True)
    out = torch.as_tensor(out).to(t.device).to(t.dtype)
    assert out.shape == t.shape
    if codec == "raw":
        assert torch.equal(out, t)
    else:  # lossy: inner products preserved, values approximate
        cos = torch.nn.functional.cosine_similarity(out.float().reshape(-1, 64), t.float().reshape(-1, 64), dim=1)
        assert cos.mean().item() > 0.9


@pytest.mark.parametrize("transport,provider,ep", [("tcp", None, None), ("fabric", "shm", "rdm"), ("fabric", "tcp", "msg")])
def test_connector_loopback_cuda_caches(transport, provider, ep):
    from middleware.vllm_plugin.loopback import default_args, run_both

    args = default_args(layers=4, prompt_lens=[64, 512], transport=transport, provider=provider,
                        ep_type=ep, device=str(_cuda()), timeout=120.0)
    out = run_both(args)
    assert out["all_match"], out["match"]
