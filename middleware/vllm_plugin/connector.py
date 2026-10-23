"""
ScuffedRdmaConnector: out-of-tree vLLM V1 KV connector.

Loaded by vLLM through kv_connector_module_path; importing this module
imports vLLM. Everything with logic lives in core.py and is tested without
vLLM. Written against vLLM 620e8924 (2026-04-12), the commit pinned by the
vllm/ submodule; KVConnectorBase_V1 is marked experimental upstream, so
re-check the signatures below when the submodule moves.

    --kv-transfer-config '{"kv_connector":"ScuffedRdmaConnector",
        "kv_connector_module_path":"middleware.vllm_plugin.connector",
        "kv_role":"kv_producer",
        "kv_connector_extra_config":{"peer":"server2","port":14600,
            "transport":"fabric","provider":"verbs","ep_type":"msg"}}'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from vllm.distributed.kv_transfer.kv_connector.v1.base import (
    KVConnectorBase_V1,
    KVConnectorMetadata,
    KVConnectorRole,
)
from vllm.logger import init_logger

from .core import ConnectorConfig, CoreMetadata, ReqMeta, SchedulerSide, WorkerSide

if TYPE_CHECKING:
    import torch
    from vllm.config import VllmConfig
    from vllm.forward_context import ForwardContext
    from vllm.v1.attention.backend import AttentionMetadata
    from vllm.v1.core.kv_cache_manager import KVCacheBlocks
    from vllm.v1.core.sched.output import SchedulerOutput
    from vllm.v1.kv_cache_interface import KVCacheConfig
    from vllm.v1.request import Request

logger = init_logger(__name__)


@dataclass
class ScuffedConnectorMetadata(KVConnectorMetadata):
    requests: list[ReqMeta] = field(default_factory=list)

    def core(self) -> CoreMetadata:
        return CoreMetadata(self.requests)


class ScuffedRdmaConnector(KVConnectorBase_V1):
    def __init__(
        self,
        vllm_config: "VllmConfig",
        role: KVConnectorRole,
        kv_cache_config: "KVCacheConfig | None" = None,
    ):
        super().__init__(vllm_config=vllm_config, role=role, kv_cache_config=kv_cache_config)
        tc = self._kv_transfer_config
        self._cfg = ConnectorConfig.from_extra(
            tc.kv_connector_extra_config or {},
            is_producer=tc.is_kv_producer,
            is_consumer=tc.is_kv_consumer,
            block_size=vllm_config.cache_config.block_size,
        )
        self._sched: Optional[SchedulerSide] = None
        self._worker: Optional[WorkerSide] = None
        if role == KVConnectorRole.SCHEDULER:
            self._sched = SchedulerSide(self._cfg)
        else:
            from vllm.distributed.parallel_state import get_world_group
            rank = get_world_group().rank
            self._worker = WorkerSide(self._cfg, rank=rank)
        logger.info("ScuffedRdmaConnector role=%s producer=%s consumer=%s transport=%s peer=%s port=%s",
                    role, self._cfg.is_producer, self._cfg.is_consumer,
                    self._cfg.transport, self._cfg.peer, self._cfg.port)

    # ==============================
    # Worker-side methods
    # ==============================

    def register_kv_caches(self, kv_caches: dict[str, "torch.Tensor"]):
        assert self._worker is not None
        self._worker.register_kv_caches(kv_caches)

    def start_load_kv(self, forward_context: "ForwardContext", **kwargs: Any) -> None:
        assert self._worker is not None
        if not self._cfg.is_consumer:
            return
        meta = self._get_connector_metadata()
        assert isinstance(meta, ScuffedConnectorMetadata)
        self._worker.start_load_kv(meta.core())

    def wait_for_layer_load(self, layer_name: str) -> None:
        # Loads are synchronous in start_load_kv.
        return

    def save_kv_layer(
        self,
        layer_name: str,
        kv_layer: "torch.Tensor",
        attn_metadata: "AttentionMetadata",
        **kwargs: Any,
    ) -> None:
        assert self._worker is not None
        if not self._cfg.is_producer:
            return
        meta = self._get_connector_metadata()
        assert isinstance(meta, ScuffedConnectorMetadata)
        self._worker.save_kv_layer(layer_name, kv_layer, meta.core())

    def wait_for_save(self):
        assert self._worker is not None
        self._worker.wait_for_save()

    def get_finished(
        self, finished_req_ids: set[str]
    ) -> tuple[set[str] | None, set[str] | None]:
        return None, None

    def get_block_ids_with_load_errors(self) -> set[int]:
        if self._worker is None:
            return set()
        return self._worker.get_block_ids_with_load_errors()

    def shutdown(self):
        if self._worker is not None:
            self._worker.shutdown()

    # ==============================
    # Scheduler-side methods
    # ==============================

    def get_num_new_matched_tokens(
        self,
        request: "Request",
        num_computed_tokens: int,
    ) -> tuple[int | None, bool]:
        assert self._sched is not None
        return self._sched.get_num_new_matched_tokens(request, num_computed_tokens)

    def update_state_after_alloc(
        self, request: "Request", blocks: "KVCacheBlocks", num_external_tokens: int
    ):
        assert self._sched is not None
        self._sched.update_state_after_alloc(request, blocks, num_external_tokens)

    def build_connector_meta(
        self, scheduler_output: "SchedulerOutput"
    ) -> KVConnectorMetadata:
        assert self._sched is not None
        return ScuffedConnectorMetadata(self._sched.build_connector_meta(scheduler_output).requests)

    def request_finished(
        self,
        request: "Request",
        block_ids: list[int],
    ) -> tuple[bool, dict[str, Any] | None]:
        assert self._sched is not None
        return self._sched.request_finished(request, block_ids)
