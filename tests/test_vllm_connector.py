"""
Tests for middleware/vllm_plugin (ScuffedRdmaConnector).

Run here without vLLM, CUDA, or RDMA:
  - paged-buffer block gather/scatter (numpy and torch CPU, all three layouts)
  - KV blob codec (raw incl. bfloat16, scuffedquant)
  - BlobChannel round trips with out-of-order arrival
  - scheduler-side bookkeeping incl. chunked prefill and prefix-cache skip
  - full producer -> consumer flow through the real ScuffedRdmaConnector class,
    imported against a stub of vLLM's KVConnectorBase_V1 (signatures copied from
    vLLM 620e8924), over real TCP sockets
  - WFA hot/cold tagging and telemetry
  - signature check against real vLLM source when it is on disk (VLLM_SRC or
    /tmp/vllm-src), and a real-import check when vllm is installed (cluster)
"""

from __future__ import annotations

import abc
import ast
import enum
import importlib
import os
import socket
import sys
import threading
import time
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from middleware.fabric.channel import TcpBlobChannel
from middleware.telemetry import Telemetry
from middleware.vllm_plugin.core import (
    ConnectorConfig, CoreMetadata, ReqMeta, SchedulerSide, WorkerSide,
)
from middleware.vllm_plugin.kv_codec import (
    control_blob, decode_kv, encode_kv, is_control, read_control, read_header,
)
from middleware.vllm_plugin.kv_layout import block_axis, put_blocks, take_blocks
from middleware.vllm_plugin.transport import KVReceiver, KVSender

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None

RNG = np.random.default_rng(0)
LAYOUTS = {
    "flash": lambda nb, bs, h, d: (2, nb, bs, h, d),
    "flashinfer": lambda nb, bs, h, d: (nb, 2, bs, h, d),
    "mla": lambda nb, bs, h, d: (nb, bs, d),
}


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


# ---------------------------------------------------------------- layout ----

@pytest.mark.parametrize("layout", list(LAYOUTS))
def test_block_axis_heuristic(layout):
    shape = LAYOUTS[layout](37, 16, 4, 64)
    assert block_axis(shape) == {"flash": 1, "flashinfer": 0, "mla": 0}[layout]


@pytest.mark.parametrize("layout", list(LAYOUTS))
@pytest.mark.parametrize("backend", ["numpy", "torch"])
def test_extract_inject_roundtrip_random_block_tables(layout, backend):
    if backend == "torch" and torch is None:
        pytest.skip("torch not installed")
    nb, bs, h, d = 64, 16, 4, 32
    shape = LAYOUTS[layout](nb, bs, h, d)
    src = RNG.standard_normal(shape).astype(np.float32)
    dst = np.zeros_like(src)
    if backend == "torch":
        src, dst = torch.from_numpy(src), torch.from_numpy(dst)
    axis = block_axis(tuple(src.shape))
    for _ in range(5):
        k = int(RNG.integers(1, 20))
        src_ids = RNG.choice(nb, size=k, replace=False).tolist()
        dst_ids = RNG.choice(nb, size=k, replace=False).tolist()
        blocks = take_blocks(src, src_ids, axis)
        assert blocks.shape[axis] == k
        n = put_blocks(dst, blocks, dst_ids, axis)
        assert n == k
        for s, t in zip(src_ids, dst_ids):
            a = np.take(np.asarray(src), s, axis=axis)
            b = np.take(np.asarray(dst), t, axis=axis)
            np.testing.assert_array_equal(a, b)


def test_put_blocks_partial_and_shape_check():
    src = RNG.standard_normal((2, 10, 4, 2, 8)).astype(np.float32)
    dst = np.zeros((2, 10, 4, 2, 8), np.float32)
    blocks = take_blocks(src, [0, 1, 2], 1)
    assert put_blocks(dst, blocks, [5, 6], 1) == 2          # fewer dst ids than blocks
    assert put_blocks(dst, blocks, [7, 8, 9, 3], 1) == 3    # more dst ids than blocks
    with pytest.raises(ValueError):
        put_blocks(np.zeros((2, 10, 4, 2, 16), np.float32), blocks, [0], 1)


# ----------------------------------------------------------------- codec ----

def test_codec_raw_roundtrip_numpy_dtypes():
    for dt in (np.float16, np.float32, np.int8):
        a = (RNG.standard_normal((3, 2, 16, 4, 8)) * 10).astype(dt)
        blob = encode_kv(a, layer="model.layers.0.self_attn.attn", axis=0, block_size=16, num_tokens=40)
        hdr, b = decode_kv(blob)
        assert hdr["layer"].endswith("attn") and hdr["num_tokens"] == 40 and hdr["codec"] == "raw"
        assert b.dtype == a.dtype and b.shape == a.shape
        np.testing.assert_array_equal(a, b)


@pytest.mark.skipif(torch is None, reason="torch not installed")
def test_codec_raw_roundtrip_torch_bfloat16():
    t = torch.randn(2, 5, 16, 2, 64).to(torch.bfloat16)
    blob = encode_kv(t, layer="l0", axis=1, block_size=16, num_tokens=70)
    hdr, back = decode_kv(blob, want_torch=True)
    assert hdr["orig_dtype"] == "bfloat16" and back.dtype == torch.bfloat16
    assert torch.equal(t, back)
    _, as_np = decode_kv(blob, want_torch=False)            # numpy side gets float32
    np.testing.assert_allclose(as_np, t.float().numpy())


def test_codec_scuffedquant_shape_dtype_topk():
    # Keys with a few dominant directions, like real attention keys.
    n, d = 256, 64
    base = RNG.standard_normal((8, d)).astype(np.float32)
    keys = (RNG.standard_normal((n, 8)) @ base + 0.1 * RNG.standard_normal((n, d))).astype(np.float32)
    blocks = keys.reshape(2, 8, 16, d).astype(np.float16)    # MLA-like [nb, bs, d] with extra dim
    blob = encode_kv(blocks, layer="l3", axis=0, block_size=16, num_tokens=128,
                     codec="scuffedquant", bits=3, qjl_dim=256)
    raw = encode_kv(blocks, layer="l3", axis=0, block_size=16, num_tokens=128)
    assert len(blob) < len(raw)
    hdr, rec = decode_kv(blob)
    assert hdr["codec"] == "scuffedquant"
    assert rec.shape == blocks.shape and rec.dtype == np.float16
    q = RNG.standard_normal((16, d)).astype(np.float32)
    k_true = blocks.reshape(-1, d).astype(np.float32)
    k_rec = rec.reshape(-1, d).astype(np.float32)
    top_true = np.argsort(-(q @ k_true.T), axis=1)[:, :8]
    top_rec = np.argsort(-(q @ k_rec.T), axis=1)[:, :8]
    overlap = np.mean([len(set(a) & set(b)) / 8 for a, b in zip(top_true, top_rec)])
    assert overlap > 0.5, overlap                          # sanity floor, not a result


def test_control_blob():
    c = control_blob(xfer_id="x", layers=28)
    assert is_control(c) and read_control(c) == {"xfer_id": "x", "layers": 28}
    assert not is_control(encode_kv(np.zeros((1, 2, 2), np.float32), layer="l", axis=0,
                                    block_size=2, num_tokens=1))


# ------------------------------------------------------------- channels ----

def test_channel_roundtrip_out_of_order_multi_request():
    a, b = TcpBlobChannel.pair()
    tel = Telemetry(node="t")
    rx = KVReceiver(0, channel=b, tel=tel)
    keys = [f"req{r}/model.layers.{l}.attn" for r in range(3) for l in range(4)]
    payloads = {k: RNG.integers(0, 255, size=int(RNG.integers(10, 5000)), dtype=np.uint8).tobytes() for k in keys}
    order = list(keys)
    RNG.shuffle(order)
    for k in order:
        a.send(k, payloads[k], hot=len(payloads[k]) < 1000)
    for k in reversed(keys):                                # consumer asks in a different order
        assert rx.wait(k, timeout=5) == payloads[k]
    assert rx.wait("missing", timeout=0.05) is None
    rx.close()
    a.close()


def test_sender_wfa_tagging_and_telemetry():
    a, b = TcpBlobChannel.pair()
    tel = Telemetry(node="t")
    tx = KVSender("unused", 0, channel=a, tel=tel, hot_threshold=4096, cold_threshold=262144)
    rx = KVReceiver(0, channel=b, tel=tel)
    small = b"x" * 512
    big = b"y" * (1 << 20)
    assert tx.send("r/small", small) is True
    assert tx.send("r/big", big) is False
    assert tx.send("r/__done__", b"c", hot=True) is True
    assert tx.flush(timeout=10)
    assert rx.wait("r/big", 5) == big and rx.wait("r/small", 5) == small
    snap = tel.snapshot()["classes"]
    assert snap["hot"]["ops"] == 2 and snap["cold"]["ops"] == 1
    assert snap["cold"]["bytes"] == len(big)
    sigs = tel.signals()
    assert {s.qp_class for s in sigs} == {"hot", "cold"}
    assert all(s.completion_us >= 0 for s in sigs)
    tx.close(); rx.close()


# -------------------------------------------------------- scheduler side ----

@dataclass
class FakeRequest:
    request_id: str
    prompt_token_ids: list
    kv_transfer_params: dict | None = None


@dataclass
class FakeNewReq:
    req_id: str
    prompt_token_ids: list
    block_ids: tuple
    num_computed_tokens: int = 0


@dataclass
class FakeCached:
    req_ids: list = field(default_factory=list)
    new_block_ids: list = field(default_factory=list)
    num_computed_tokens: list = field(default_factory=list)
    resumed_req_ids: set = field(default_factory=set)


@dataclass
class FakeSchedOut:
    scheduled_new_reqs: list = field(default_factory=list)
    scheduled_cached_reqs: FakeCached = field(default_factory=FakeCached)
    num_scheduled_tokens: dict = field(default_factory=dict)


def _cfg(prod, cons, **kw):
    return ConnectorConfig(is_producer=prod, is_consumer=cons, block_size=16, **kw)


def test_scheduler_producer_full_and_chunked_prefill():
    s = SchedulerSide(_cfg(True, False))
    r1 = FakeRequest("p-1-aaaa", list(range(40)), {"do_remote_decode": True, "scuffed_xfer_id": "X1"})
    r2 = FakeRequest("p-2-bbbb", list(range(100)), {"do_remote_decode": True})   # no id: falls back to request id
    for r in (r1, r2):
        assert s.get_num_new_matched_tokens(r, 0) == (0, False)
        s.update_state_after_alloc(r, None, 0)
    out = FakeSchedOut(
        scheduled_new_reqs=[FakeNewReq(r1.request_id, r1.prompt_token_ids, ([1, 2, 3],)),
                            FakeNewReq(r2.request_id, r2.prompt_token_ids, ([4, 5, 6, 7],))],
        num_scheduled_tokens={r1.request_id: 40, r2.request_id: 64})   # r2 chunked: 64 < 100
    m = s.build_connector_meta(out)
    assert [(q.xfer_id, q.block_ids, q.load) for q in m.requests] == [("X1", [1, 2, 3], False)]
    out2 = FakeSchedOut(scheduled_cached_reqs=FakeCached([r2.request_id], [([8, 9, 10],)], [64]),
                        num_scheduled_tokens={r2.request_id: 36})
    m2 = s.build_connector_meta(out2)
    assert len(m2.requests) == 1 and m2.requests[0].xfer_id == r2.request_id
    assert m2.requests[0].block_ids == [4, 5, 6, 7, 8, 9, 10] and m2.requests[0].num_tokens == 100
    free_now, params = s.request_finished(r1, [1, 2, 3])
    assert free_now is False
    assert params == {"do_remote_prefill": True, "do_remote_decode": False,
                      "scuffed_xfer_id": "X1", "scuffed_num_tokens": 40}


def test_scheduler_consumer_matched_tokens_and_prefix_skip():
    s = SchedulerSide(_cfg(False, True))
    params = {"do_remote_prefill": True, "scuffed_xfer_id": "X9", "scuffed_num_tokens": 70}
    r = FakeRequest("d-1-cccc", list(range(70)), params)
    assert s.get_num_new_matched_tokens(r, 0) == (69, False)
    assert s.get_num_new_matched_tokens(r, 32) == (37, False)          # 32 local prefix-cache hit
    assert s.get_num_new_matched_tokens(FakeRequest("other", [1, 2, 3]), 0) == (0, False)
    s.update_state_after_alloc(r, None, 37)
    # NewRequestData.num_computed_tokens counts local + external tokens.
    out = FakeSchedOut(scheduled_new_reqs=[FakeNewReq(r.request_id, r.prompt_token_ids,
                                                      ([11, 12, 13, 14, 15],), num_computed_tokens=32 + 37)],
                       num_scheduled_tokens={r.request_id: 1})
    m = s.build_connector_meta(out)
    assert len(m.requests) == 1
    q = m.requests[0]
    assert q.load and q.xfer_id == "X9" and q.skip_blocks == 2 and q.num_tokens == 69


def test_metadata_serialization():
    m = CoreMetadata([ReqMeta("a", "x", [1, 2], 30, False), ReqMeta("b", "y", [3], 5, True, 1)])
    back = CoreMetadata.from_json(m.to_json())
    assert back == m
    import pickle
    assert pickle.loads(pickle.dumps(m)) == m


# ------------------------------------------- worker side over real TCP ----

def _paged(layout, nb=48, bs=16, h=2, d=32, dtype=np.float32, fill=True):
    shape = LAYOUTS[layout](nb, bs, h, d)
    return RNG.standard_normal(shape).astype(dtype) if fill else np.zeros(shape, dtype)


@pytest.mark.parametrize("layout", list(LAYOUTS))
def test_worker_push_load_over_tcp(layout):
    port = _free_port()
    tel_p, tel_c = Telemetry(node="prefill"), Telemetry(node="decode")
    layers = [f"model.layers.{i}.self_attn.attn" for i in range(4)]
    prod_kv = {n: _paged(layout) for n in layers}
    cons_kv = {n: _paged(layout, fill=False) for n in layers}
    consumer = WorkerSide(_cfg(False, True, port=port, bind="127.0.0.1"), tel=tel_c)
    consumer.register_kv_caches(cons_kv)
    producer = WorkerSide(_cfg(True, False, peer="127.0.0.1", port=port), tel=tel_p)
    producer.register_kv_caches(prod_kv)
    src_ids, dst_ids = [3, 9, 20, 31], [40, 2, 17, 5]
    pmeta = CoreMetadata([ReqMeta("p-req", "XF", src_ids, 60, load=False)])
    for n in layers:
        assert producer.save_kv_layer(n, prod_kv[n], pmeta) == 1
    producer.wait_for_save()
    cmeta = CoreMetadata([ReqMeta("d-req", "XF", dst_ids, 59, load=True, skip_blocks=1)])
    written = consumer.start_load_kv(cmeta)
    assert written == 3 * len(layers)                      # first block skipped (local prefix hit)
    axis = block_axis(prod_kv[layers[0]].shape)
    for n in layers:
        for s, t in list(zip(src_ids, dst_ids))[1:]:
            np.testing.assert_array_equal(np.take(prod_kv[n], s, axis), np.take(cons_kv[n], t, axis))
        assert not np.take(cons_kv[n], dst_ids[0], axis).any()
    assert consumer.get_block_ids_with_load_errors() == set()
    assert producer._sender.flush(timeout=10)             # done marker may still be in flight
    assert tel_p.snapshot()["classes"]["cold"]["ops"] + tel_p.snapshot()["classes"]["hot"]["ops"] == len(layers) + 1
    assert tel_c.snapshot()["classes"]["load"]["ops"] == len(layers)
    producer.shutdown(); consumer.shutdown()


def test_worker_load_timeout_reports_error_blocks():
    port = _free_port()
    consumer = WorkerSide(_cfg(False, True, port=port, bind="127.0.0.1", load_timeout_s=0.2), tel=Telemetry())
    consumer.register_kv_caches({"l0": _paged("flash", fill=False)})
    meta = CoreMetadata([ReqMeta("d", "never-sent", [4, 5, 6], 40, load=True, skip_blocks=1)])
    assert consumer.start_load_kv(meta) == 0
    assert consumer.get_block_ids_with_load_errors() == {5, 6}
    assert consumer.get_block_ids_with_load_errors() == set()
    consumer.shutdown()


def test_fabric_transport_falls_back_or_works():
    """transport='fabric' must either use the libfabric pool or fall back to TCP and say so."""
    port = _free_port()
    tel = Telemetry()
    cons = WorkerSide(_cfg(False, True, port=port, bind="127.0.0.1", transport="fabric",
                           provider="tcp", ep_type="msg"), tel=tel)
    cons.register_kv_caches({"l0": _paged("flash", fill=False)})
    prod = WorkerSide(_cfg(True, False, peer="127.0.0.1", port=port, transport="fabric",
                           provider="tcp", ep_type="msg"), tel=tel)
    src = {"l0": _paged("flash")}
    prod.register_kv_caches(src)
    prod.save_kv_layer("l0", src["l0"], CoreMetadata([ReqMeta("p", "F", [1, 2], 20, False)]))
    prod.wait_for_save()
    got = cons.start_load_kv(CoreMetadata([ReqMeta("d", "F", [7, 8], 19, True)]))
    assert got == 2
    used = {prod._sender.transport_used, cons._receiver.transport_used}
    events = tel.snapshot()["classes"].get("hot", {}).get("events", {})
    assert used == {"fabric"} or (used == {"tcp"} and events.get("tcp_fallback", 0) >= 1)
    prod.shutdown(); cons.shutdown()


# ---------------------------------------- the real connector, stub vLLM ----

class _Role(enum.Enum):
    SCHEDULER = 0
    WORKER = 1


def _install_vllm_stub(monkeypatch, rank=0):
    """Minimal vllm modules with KVConnectorBase_V1 abstract API as of vLLM 620e8924."""

    class KVConnectorMetadata(abc.ABC):  # noqa: B024
        pass

    class KVConnectorBase_V1(abc.ABC):
        def __init__(self, vllm_config, role, kv_cache_config=None):
            self._connector_metadata = None
            self._vllm_config = vllm_config
            if vllm_config.kv_transfer_config is None:
                raise ValueError("kv_transfer_config must be set")
            self._kv_transfer_config = vllm_config.kv_transfer_config
            self._kv_cache_config = kv_cache_config
            self._role = role

        def bind_connector_metadata(self, m):
            self._connector_metadata = m

        def clear_connector_metadata(self):
            self._connector_metadata = None

        def _get_connector_metadata(self):
            assert self._connector_metadata is not None
            return self._connector_metadata

        @abc.abstractmethod
        def start_load_kv(self, forward_context, **kwargs): ...
        @abc.abstractmethod
        def wait_for_layer_load(self, layer_name): ...
        @abc.abstractmethod
        def save_kv_layer(self, layer_name, kv_layer, attn_metadata, **kwargs): ...
        @abc.abstractmethod
        def wait_for_save(self): ...
        @abc.abstractmethod
        def get_num_new_matched_tokens(self, request, num_computed_tokens): ...
        @abc.abstractmethod
        def update_state_after_alloc(self, request, blocks, num_external_tokens): ...
        @abc.abstractmethod
        def build_connector_meta(self, scheduler_output): ...

    base = types.ModuleType("vllm.distributed.kv_transfer.kv_connector.v1.base")
    base.KVConnectorBase_V1 = KVConnectorBase_V1
    base.KVConnectorMetadata = KVConnectorMetadata
    base.KVConnectorRole = _Role
    logger_mod = types.ModuleType("vllm.logger")
    import logging
    logger_mod.init_logger = logging.getLogger
    ps = types.ModuleType("vllm.distributed.parallel_state")
    ps.get_world_group = lambda: types.SimpleNamespace(rank=rank, local_rank=rank)
    mods = {
        "vllm": types.ModuleType("vllm"),
        "vllm.distributed": types.ModuleType("vllm.distributed"),
        "vllm.distributed.kv_transfer": types.ModuleType("vllm.distributed.kv_transfer"),
        "vllm.distributed.kv_transfer.kv_connector": types.ModuleType("vllm.distributed.kv_transfer.kv_connector"),
        "vllm.distributed.kv_transfer.kv_connector.v1": types.ModuleType("vllm.distributed.kv_transfer.kv_connector.v1"),
        "vllm.distributed.kv_transfer.kv_connector.v1.base": base,
        "vllm.distributed.parallel_state": ps,
        "vllm.logger": logger_mod,
    }
    for k, v in mods.items():
        monkeypatch.setitem(sys.modules, k, v)
    monkeypatch.delitem(sys.modules, "middleware.vllm_plugin.connector", raising=False)
    return importlib.import_module("middleware.vllm_plugin.connector"), base


def _vllm_config(role: str, extra: dict, block_size=16):
    tc = types.SimpleNamespace(
        kv_role=role, kv_connector_extra_config=extra,
        is_kv_producer=role in ("kv_producer", "kv_both"),
        is_kv_consumer=role in ("kv_consumer", "kv_both"))
    return types.SimpleNamespace(kv_transfer_config=tc,
                                 cache_config=types.SimpleNamespace(block_size=block_size))


@pytest.mark.skipif(torch is None, reason="torch not installed")
def test_real_connector_class_end_to_end_with_stub_vllm(monkeypatch):
    conn_mod, base = _install_vllm_stub(monkeypatch)
    _connector_e2e(conn_mod, base.KVConnectorBase_V1, _Role)


def _connector_e2e(conn_mod, base_cls, Role):
    C = conn_mod.ScuffedRdmaConnector
    assert issubclass(C, base_cls) and not C.__abstractmethods__
    _Role = Role
    port = _free_port()
    extra_p = {"peer": "127.0.0.1", "port": port, "transport": "tcp"}
    extra_c = {"port": port, "bind": "127.0.0.1", "transport": "tcp", "load_timeout_s": 10}
    ps, pw = C(_vllm_config("kv_producer", extra_p), _Role.SCHEDULER), C(_vllm_config("kv_producer", extra_p), _Role.WORKER)
    cs, cw = C(_vllm_config("kv_consumer", extra_c), _Role.SCHEDULER), C(_vllm_config("kv_consumer", extra_c), _Role.WORKER)

    layers = [f"model.layers.{i}.self_attn.attn" for i in range(3)]
    pk = {n: torch.randn(2, 32, 16, 2, 64, dtype=torch.bfloat16) for n in layers}   # FlashAttention layout
    ck = {n: torch.zeros(2, 32, 16, 2, 64, dtype=torch.bfloat16) for n in layers}
    cw.register_kv_caches(ck)
    pw.register_kv_caches(pk)

    prompt = list(range(50))                               # 4 blocks of 16
    preq = FakeRequest("cmpl-1-0-1a2b3c4d", prompt, {"do_remote_decode": True, "scuffed_xfer_id": "abc"})
    ps.update_state_after_alloc(preq, None, 0)
    pmeta = ps.build_connector_meta(FakeSchedOut(
        scheduled_new_reqs=[FakeNewReq(preq.request_id, prompt, ([5, 6, 7, 8],))],
        num_scheduled_tokens={preq.request_id: 50}))
    assert isinstance(pmeta, conn_mod.ScuffedConnectorMetadata)
    pw.bind_connector_metadata(pmeta)
    for n in layers:
        pw.save_kv_layer(n, pk[n], attn_metadata=None)
    pw.wait_for_save()
    pw.clear_connector_metadata()
    _, params = ps.request_finished(preq, [5, 6, 7, 8])

    dreq = FakeRequest("cmpl-1-0-9f8e7d6c", prompt, params)
    n_ext, is_async = cs.get_num_new_matched_tokens(dreq, 0)
    assert (n_ext, is_async) == (49, False)
    cs.update_state_after_alloc(dreq, None, n_ext)
    cmeta = cs.build_connector_meta(FakeSchedOut(
        scheduled_new_reqs=[FakeNewReq(dreq.request_id, prompt, ([20, 21, 22, 23],), num_computed_tokens=49)],
        num_scheduled_tokens={dreq.request_id: 1}))
    cw.bind_connector_metadata(cmeta)
    cw.start_load_kv(forward_context=None)
    for n in layers:
        assert torch.equal(pk[n][:, [5, 6, 7, 8]], ck[n][:, [20, 21, 22, 23]])
    assert cw.get_block_ids_with_load_errors() == set()
    assert cw.get_finished(set()) == (None, None)
    pw.shutdown(); cw.shutdown()


# ---------------------------------------- checks against real vLLM ----

def _vllm_src() -> Path | None:
    for p in (os.environ.get("VLLM_SRC"), "/tmp/vllm-src", str(Path(__file__).resolve().parents[1] / "vllm")):
        if p and (Path(p) / "vllm/distributed/kv_transfer/kv_connector/v1/base.py").is_file():
            return Path(p)
    return None


@pytest.mark.skipif(_vllm_src() is None, reason="vLLM source not on disk (set VLLM_SRC or init the vllm submodule)")
def test_signatures_match_vllm_source():
    tree = ast.parse((_vllm_src() / "vllm/distributed/kv_transfer/kv_connector/v1/base.py").read_text())
    base = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "KVConnectorBase_V1")
    want = {}
    for fn in base.body:
        if isinstance(fn, ast.FunctionDef):
            abstract = any(getattr(d, "id", getattr(d, "attr", None)) == "abstractmethod" for d in fn.decorator_list)
            want[fn.name] = ([a.arg for a in fn.args.args], abstract)
    src = (Path(__file__).resolve().parents[1] / "middleware/vllm_plugin/connector.py").read_text()
    ours = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == "ScuffedRdmaConnector")
    have = {fn.name: [a.arg for a in fn.args.args] for fn in ours.body if isinstance(fn, ast.FunctionDef)}
    for name, (args, abstract) in want.items():
        if abstract:
            assert name in have, f"abstract method {name} not implemented"
        if name in have:
            assert have[name] == args, f"{name}: ours {have[name]} vs vLLM {args}"


def _real_vllm_importable() -> bool:
    try:
        importlib.import_module("vllm.distributed.kv_transfer.kv_connector.v1.base")
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _real_vllm_importable(), reason="vllm not installed here; runs on the cluster")
def test_real_vllm_import():
    from vllm.distributed.kv_transfer.kv_connector.v1.base import KVConnectorBase_V1
    sys.modules.pop("middleware.vllm_plugin.connector", None)
    from middleware.vllm_plugin.connector import ScuffedRdmaConnector
    assert issubclass(ScuffedRdmaConnector, KVConnectorBase_V1)
    assert not ScuffedRdmaConnector.__abstractmethods__


@pytest.mark.skipif(not _real_vllm_importable() or torch is None, reason="vllm not importable here")
def test_real_vllm_base_end_to_end(monkeypatch):
    """Same producer -> consumer flow, but through vLLM's own KVConnectorBase_V1."""
    import vllm.distributed.parallel_state as ps
    from vllm.distributed.kv_transfer.kv_connector.v1.base import KVConnectorBase_V1, KVConnectorRole
    monkeypatch.setattr(ps, "get_world_group", lambda: types.SimpleNamespace(rank=0, local_rank=0))
    sys.modules.pop("middleware.vllm_plugin.connector", None)
    conn_mod = importlib.import_module("middleware.vllm_plugin.connector")
    _connector_e2e(conn_mod, KVConnectorBase_V1, KVConnectorRole)


# ------------------------------------------------------------- proxy ----

def test_proxy_payloads():
    from middleware.vllm_plugin.proxy import decode_payload, prefill_payload
    req = {"model": "m", "prompt": [1, 2, 3], "max_tokens": 64, "stream": True,
           "stream_options": {"include_usage": True}}
    p = prefill_payload(req, "XID", "scuffed")
    assert p["max_tokens"] == 1 and p["stream"] is False and "stream_options" not in p
    assert p["kv_transfer_params"]["do_remote_decode"] is True
    assert p["kv_transfer_params"]["scuffed_xfer_id"] == "XID"
    assert "scuffed_xfer_id" not in prefill_payload(req, "XID", "nixl")["kv_transfer_params"]
    assert req["max_tokens"] == 64                           # original untouched
    d = decode_payload(req, {"kv_transfer_params": {"do_remote_prefill": True, "scuffed_xfer_id": "XID"}}, "XID", "scuffed")
    assert d["kv_transfer_params"]["scuffed_xfer_id"] == "XID" and d["max_tokens"] == 64
    d2 = decode_payload(req, {}, "XID", "scuffed")             # prefill returned nothing: synthesize
    assert d2["kv_transfer_params"] == {"do_remote_prefill": True, "do_remote_decode": False, "scuffed_xfer_id": "XID"}


def test_proxy_app_against_mock_servers():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    import json as _json
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    seen = {}

    class Prefill(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            body = _json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen["prefill"] = body
            out = _json.dumps({"choices": [{"text": "a"}], "kv_transfer_params": {
                "do_remote_prefill": True, "scuffed_xfer_id": body["kv_transfer_params"]["scuffed_xfer_id"],
                "scuffed_num_tokens": len(body["prompt"])}}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out))); self.end_headers(); self.wfile.write(out)

        def log_message(self, *a):
            pass

    class Decode(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            seen["decode"] = _json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.end_headers()
            for t in ("b", "c"):
                self.wfile.write(f"data: {_json.dumps({'choices': [{'text': t}]})}\n\n".encode())
            self.wfile.write(b"data: [DONE]\n\n")

        def log_message(self, *a):
            pass

    sp, sd = ThreadingHTTPServer(("127.0.0.1", 0), Prefill), ThreadingHTTPServer(("127.0.0.1", 0), Decode)
    for s in (sp, sd):
        threading.Thread(target=s.serve_forever, daemon=True).start()
    from middleware.vllm_plugin.proxy import build_app
    app = build_app([f"http://127.0.0.1:{sp.server_address[1]}"], [f"http://127.0.0.1:{sd.server_address[1]}"])
    with TestClient(app) as c:
        r = c.post("/v1/completions", json={"model": "m", "prompt": [5, 6, 7, 8], "max_tokens": 16, "stream": True})
        assert r.status_code == 200
        assert "data: [DONE]" in r.text and float(r.headers["x-scuffed-prefill-ms"]) >= 0
        assert c.get("/healthcheck").json()["mode"] == "scuffed"
    xid = seen["prefill"]["kv_transfer_params"]["scuffed_xfer_id"]
    assert seen["prefill"]["max_tokens"] == 1
    assert seen["decode"]["kv_transfer_params"]["scuffed_xfer_id"] == xid
    assert seen["decode"]["kv_transfer_params"]["scuffed_num_tokens"] == 4 and seen["decode"]["max_tokens"] == 16
    sp.shutdown(); sd.shutdown()


def test_ttft_runner_selftest(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmarks" / "vllm_disagg"))
    import run_ttft_sweep
    res = run_ttft_sweep.selftest(str(tmp_path))
    assert res["label"] == "selftest-mock" and list(tmp_path.glob("*.json"))


def test_loopback_two_process_tcp():
    from middleware.vllm_plugin.loopback import default_args, run_both
    out = run_both(default_args(layers=4, num_blocks=64, prompt_lens=[64, 200], dtype="float16", timeout=60))
    assert out["all_match"], out["match"]
    assert out["consumer"]["load_errors"] == []
