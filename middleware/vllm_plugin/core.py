"""
vLLM-agnostic connector logic. The vLLM subclass in connector.py delegates
here, so this module is tested with duck-typed Request / SchedulerOutput
objects and numpy (or torch CPU) paged buffers.

Transfer identity
-----------------
vLLM 2026 appends a random suffix to internal request ids, so prefill and
decode never see the same request_id. Transfers are keyed by a transfer id
carried in kv_transfer_params, the same channel NIXL uses:

  proxy -> prefill   kv_transfer_params = {"do_remote_decode": true,
                                           "scuffed_xfer_id": <uuid>}   (id optional)
  prefill response   kv_transfer_params = {"do_remote_prefill": true,
                                           "scuffed_xfer_id": <id>,
                                           "scuffed_num_tokens": N}
  proxy -> decode    forwards the prefill response's kv_transfer_params

Producer pushes "<xfer_id>/<layer_name>" per layer from save_kv_layer, then
a hot control blob "<xfer_id>/__done__" from wait_for_save. Consumer loads
synchronously in start_load_kv (same model as P2pNcclConnector); a layer
that does not arrive within load_timeout_s has its blocks reported through
get_block_ids_with_load_errors so vLLM recomputes them.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from middleware import telemetry as _telemetry

from .kv_codec import control_blob, decode_kv, encode_kv, is_control
from .kv_layout import block_axis, narrow, put_blocks, take_blocks

log = logging.getLogger("scuffed.vllm")

DONE = "__done__"
DEFAULT_PORT = 14600


@dataclass
class ReqMeta:
    request_id: str
    xfer_id: str
    block_ids: List[int]
    num_tokens: int
    load: bool                 # True: consumer injects; False: producer pushes
    skip_blocks: int = 0       # consumer: leading blocks already computed locally


@dataclass
class CoreMetadata:
    requests: List[ReqMeta] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps([asdict(r) for r in self.requests])

    @classmethod
    def from_json(cls, s: str) -> "CoreMetadata":
        return cls([ReqMeta(**d) for d in json.loads(s)])


@dataclass
class ConnectorConfig:
    is_producer: bool
    is_consumer: bool
    block_size: int
    peer: str = "127.0.0.1"
    port: int = DEFAULT_PORT
    bind: str = "0.0.0.0"
    transport: str = "tcp"            # tcp | fabric
    provider: Optional[str] = None    # libfabric provider: verbs, tcp, shm ...
    ep_type: Optional[str] = None     # msg | rdm
    compress: Optional[str] = None    # None | "scuffedquant"
    bits: int = 3
    qjl_dim: int = 256
    load_timeout_s: float = 30.0
    sync_send: bool = False           # wait_for_save blocks until blobs are on the wire
    hot_threshold: int = 4096
    cold_threshold: int = 262144
    layout: Optional[str] = None      # force flash / flashinfer / mla block axis
    metrics_port: Optional[int] = None

    @classmethod
    def from_extra(cls, extra: Dict[str, Any], *, is_producer: bool, is_consumer: bool,
                   block_size: int) -> "ConnectorConfig":
        known = {k: v for k, v in (extra or {}).items() if k in cls.__dataclass_fields__}
        return cls(is_producer=is_producer, is_consumer=is_consumer, block_size=block_size, **known)


def _params(request: Any) -> Dict[str, Any]:
    return getattr(request, "kv_transfer_params", None) or {}


class SchedulerSide:
    """Scheduler-process half. Mirrors the KVConnectorBase_V1 scheduler hooks."""

    def __init__(self, cfg: ConnectorConfig):
        self.cfg = cfg
        self._xfer: Dict[str, str] = {}                       # producer: req_id -> xfer_id
        self._chunked: Dict[str, Tuple[List[int], List[int]]] = {}
        self._need_load: Dict[str, Tuple[str, int]] = {}      # consumer: req_id -> (xfer_id, external tokens)

    # -- consumer: how many prompt tokens will arrive from the producer
    def get_num_new_matched_tokens(self, request: Any, num_computed_tokens: int) -> Tuple[int, bool]:
        if not self.cfg.is_consumer:
            return 0, False
        p = _params(request)
        if not (p.get("do_remote_prefill") and p.get("scuffed_xfer_id")):
            return 0, False
        prompt = getattr(request, "prompt_token_ids", None) or []
        # Last prompt token is recomputed locally so decode produces its logits.
        n = max(len(prompt) - 1 - int(num_computed_tokens), 0)
        return n, False

    def update_state_after_alloc(self, request: Any, blocks: Any, num_external_tokens: int) -> None:
        rid = request.request_id
        p = _params(request)
        if self.cfg.is_producer and p.get("do_remote_decode", not self.cfg.is_consumer):
            self._xfer[rid] = str(p.get("scuffed_xfer_id") or rid)
        if self.cfg.is_consumer and num_external_tokens > 0 and p.get("scuffed_xfer_id"):
            self._need_load[rid] = (str(p["scuffed_xfer_id"]), int(num_external_tokens))

    def build_connector_meta(self, scheduler_output: Any) -> CoreMetadata:
        meta = CoreMetadata()
        bs = self.cfg.block_size
        nsched = getattr(scheduler_output, "num_scheduled_tokens", {}) or {}
        for nr in getattr(scheduler_output, "scheduled_new_reqs", []) or []:
            rid = nr.req_id
            prompt = list(nr.prompt_token_ids or [])
            bids = list(nr.block_ids[0])
            if rid in self._xfer:
                done = int(nsched.get(rid, 0)) + int(nr.num_computed_tokens)
                if done < len(prompt):
                    self._chunked[rid] = (bids, prompt)       # chunked prefill, wait
                else:
                    meta.requests.append(ReqMeta(rid, self._xfer[rid], bids, len(prompt), load=False))
                continue
            if rid in self._need_load:
                xid, n_ext = self._need_load.pop(rid)
                # NewRequestData.num_computed_tokens already counts the external tokens;
                # only the locally computed prefix (prefix-cache hit) is skipped.
                local = max(int(nr.num_computed_tokens) - n_ext, 0)
                meta.requests.append(ReqMeta(
                    rid, xid, bids, max(len(prompt) - 1, 0), load=True, skip_blocks=local // bs))

        cached = getattr(scheduler_output, "scheduled_cached_reqs", None)
        if cached is not None:
            resumed: Set[str] = set(getattr(cached, "resumed_req_ids", ()) or ())
            for i, rid in enumerate(cached.req_ids):
                new_bids = cached.new_block_ids[i]
                ncomp = int(cached.num_computed_tokens[i])
                if rid in self._chunked:
                    prev, prompt = self._chunked[rid]
                    add = list(new_bids[0]) if new_bids is not None else []
                    bids = add if rid in resumed else prev + add
                    done = int(nsched.get(rid, 0)) + ncomp
                    if done < len(prompt):
                        self._chunked[rid] = (bids, prompt)
                    else:
                        self._chunked.pop(rid)
                        meta.requests.append(ReqMeta(rid, self._xfer[rid], bids, len(prompt), load=False))
                elif rid in self._need_load and rid in resumed and new_bids is not None:
                    xid, _ = self._need_load.pop(rid)
                    meta.requests.append(ReqMeta(rid, xid, list(new_bids[0]), ncomp, load=True, skip_blocks=0))
        self._need_load.clear()
        return meta

    def request_finished(self, request: Any, block_ids: List[int]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        rid = request.request_id
        self._chunked.pop(rid, None)
        self._need_load.pop(rid, None)
        xid = self._xfer.pop(rid, None)
        if xid is None:
            return False, None
        prompt = getattr(request, "prompt_token_ids", None) or []
        # Pushes finished their GPU->CPU copy inside save_kv_layer, so blocks can be freed now.
        return False, {
            "do_remote_prefill": True,
            "do_remote_decode": False,
            "scuffed_xfer_id": xid,
            "scuffed_num_tokens": len(prompt),
        }


class WorkerSide:
    """Worker-process half: owns the KV caches, the sender (producer) and receiver (consumer)."""

    def __init__(self, cfg: ConnectorConfig, rank: int = 0, *, sender=None, receiver=None, tel=None):
        self.cfg = cfg
        self.rank = rank
        self.tel = tel or _telemetry.default()
        self._sender = sender
        self._receiver = receiver
        self._kv: Dict[str, Any] = {}
        self._layer_idx: Dict[str, int] = {}
        self._load_errors: Set[int] = set()
        self._pending_done: Dict[str, int] = {}

    # ---- setup -------------------------------------------------------------
    def register_kv_caches(self, kv_caches: Dict[str, Any]) -> None:
        self._kv = dict(kv_caches)
        self._layer_idx = {n: i for i, n in enumerate(self._kv)}
        self._ensure_transport()
        if self.cfg.metrics_port:
            try:
                self.tel.serve(self.cfg.metrics_port + self.rank)
            except OSError as e:
                log.warning("metrics exporter not started: %s", e)

    def _ensure_transport(self) -> None:
        from .transport import KVReceiver, KVSender
        port = self.cfg.port + self.rank
        if self.cfg.is_consumer and self._receiver is None:
            self._receiver = KVReceiver(port, transport=self.cfg.transport, provider=self.cfg.provider,
                                        ep_type=self.cfg.ep_type, bind=self.cfg.bind, tel=self.tel)
        if self.cfg.is_producer and self._sender is None:
            self._sender = KVSender(self.cfg.peer, port, transport=self.cfg.transport,
                                    provider=self.cfg.provider, ep_type=self.cfg.ep_type,
                                    hot_threshold=self.cfg.hot_threshold,
                                    cold_threshold=self.cfg.cold_threshold, tel=self.tel)

    # ---- producer ------------------------------------------------------------
    def save_kv_layer(self, layer_name: str, kv_layer: Any, meta: CoreMetadata) -> int:
        """Push this layer's blocks for every store request. Returns blobs queued."""
        if not self.cfg.is_producer or self._sender is None:
            return 0
        axis = block_axis(tuple(kv_layer.shape), self.cfg.layout)
        n = 0
        for r in meta.requests:
            if r.load:
                continue
            blocks = take_blocks(kv_layer, r.block_ids, axis)   # GPU gather, then CPU copy in encode
            blob = encode_kv(blocks, layer=layer_name, axis=axis, block_size=self.cfg.block_size,
                             num_tokens=r.num_tokens, codec=self.cfg.compress or "raw",
                             bits=self.cfg.bits, qjl_dim=self.cfg.qjl_dim)
            self._sender.send(f"{r.xfer_id}/{layer_name}", blob,
                              layer_idx=self._layer_idx.get(layer_name, -1),
                              seq_len=r.num_tokens, phase="prefill")
            self._pending_done[r.xfer_id] = self._pending_done.get(r.xfer_id, 0) + 1
            n += 1
        return n

    def wait_for_save(self, meta: Optional[CoreMetadata] = None) -> None:
        if not self.cfg.is_producer or self._sender is None:
            return
        for xid, layers in list(self._pending_done.items()):
            self._sender.send(f"{xid}/{DONE}", control_blob(xfer_id=xid, layers=layers),
                              hot=True, role="metadata")
        self._pending_done.clear()
        if self.cfg.sync_send:
            self._sender.flush()

    # ---- consumer ------------------------------------------------------------
    def start_load_kv(self, meta: CoreMetadata) -> int:
        """Inject every load request's layers into the registered paged caches. Returns blocks written."""
        if not self.cfg.is_consumer or self._receiver is None:
            return 0
        written = 0
        for r in meta.requests:
            if not r.load:
                continue
            for name, cache in self._kv.items():
                key = f"{r.xfer_id}/{name}"
                t0 = time.perf_counter()
                blob = self._receiver.wait(key, timeout=self.cfg.load_timeout_s)
                wait_us = (time.perf_counter() - t0) * 1e6
                if blob is None:
                    log.warning("KV for %s not received within %.1fs", key, self.cfg.load_timeout_s)
                    self.tel.event("load", "timeout")
                    self._load_errors.update(r.block_ids[r.skip_blocks:])
                    continue
                hdr, blocks = decode_kv(blob, want_torch=type(cache).__module__.startswith("torch"))
                axis = hdr["axis"]
                if hdr["block_size"] != self.cfg.block_size:
                    raise ValueError(f"block_size mismatch: producer {hdr['block_size']} vs consumer {self.cfg.block_size}")
                avail = int(blocks.shape[axis]) - r.skip_blocks
                if avail <= 0:
                    continue
                src = narrow(blocks, axis, r.skip_blocks, avail)
                written += put_blocks(cache, src, r.block_ids[r.skip_blocks:], axis)
                self.tel.record("load", wait_us, len(blob))
            self._receiver.discard_prefix(f"{r.xfer_id}/{DONE}")
        return written

    def get_block_ids_with_load_errors(self) -> Set[int]:
        out, self._load_errors = self._load_errors, set()
        return out

    def shutdown(self) -> None:
        if self._sender is not None:
            self._sender.flush(timeout=10)
            self._sender.close()
        if self._receiver is not None:
            self._receiver.close()
