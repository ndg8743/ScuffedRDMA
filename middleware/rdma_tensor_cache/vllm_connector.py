"""
vLLM KV cache connector for Neumann-backed disaggregated prefill/decode.

Follows the MooncakeConnector/NixlConnector pattern: the prefill node
produces KV cache blocks and ships them over RDMA to the decode node
via a centralized Neumann tensor cache.
"""

import struct
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .precision import PrecisionFormat


@dataclass
class KVCacheBlock:
    """A single KV cache block for one layer."""
    layer_idx: int
    key_data: np.ndarray
    value_data: np.ndarray
    seq_len: int
    token_offset: int = 0


@dataclass
class KVCacheMetadata:
    """Routing metadata for a KV cache transfer."""
    request_id: str
    num_layers: int
    num_heads: int
    head_dim: int
    seq_len: int
    wire_format: PrecisionFormat = PrecisionFormat.FP16
    timestamp: float = field(default_factory=time.monotonic)

    def to_bytes(self) -> bytes:
        req_bytes = self.request_id.encode('utf-8')[:64].ljust(64, b'\x00')
        return req_bytes + struct.pack(
            '<IIIIIf',
            self.num_layers,
            self.num_heads,
            self.head_dim,
            self.seq_len,
            list(PrecisionFormat).index(self.wire_format),
            self.timestamp,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> 'KVCacheMetadata':
        req_id = data[:64].rstrip(b'\x00').decode('utf-8')
        fields = struct.unpack('<IIIIIf', data[64:64+24])
        return cls(
            request_id=req_id,
            num_layers=fields[0],
            num_heads=fields[1],
            head_dim=fields[2],
            seq_len=fields[3],
            wire_format=list(PrecisionFormat)[fields[4]],
            timestamp=fields[5],
        )


class NeumannKVCacheConnector:
    """
    KV cache connector for vLLM disaggregated prefill/decode.

    On the prefill side, call send_kv_cache() after attention computation
    to ship KV blocks to the centralized Neumann cache. On the decode
    side, call recv_kv_cache() to pull them before decoding starts.

    Designed for the two-tower setup:
      Tower 1 (RTX 5070 Ti) - decode
      Tower 2 (2x V100)     - prefill
      Connected via 100GbE ConnectX-4
    """

    def __init__(self, transport: Any = None,
                 cache: Any = None,
                 wire_format: PrecisionFormat = PrecisionFormat.FP16):
        """
        Args:
            transport: RDMA or TCP-sim transport backend.
            cache: RdmaTensorCache instance for local buffering.
            wire_format: Precision for KV data on the wire.
        """
        self._transport = transport
        self._cache = cache
        self._wire_format = wire_format
        self._pending: Dict[str, KVCacheMetadata] = {}

    def send_kv_cache(self, request_id: str,
                      blocks: List[KVCacheBlock],
                      num_heads: int,
                      head_dim: int) -> KVCacheMetadata:
        """
        Send KV cache blocks to the remote decode node.

        Args:
            request_id: Unique request identifier.
            blocks: List of per-layer KV cache blocks.
            num_heads: Number of attention heads.
            head_dim: Dimension per head.

        Returns:
            Metadata describing the transfer.
        """
        if not blocks:
            raise ValueError("No KV cache blocks to send")

        meta = KVCacheMetadata(
            request_id=request_id,
            num_layers=len(blocks),
            num_heads=num_heads,
            head_dim=head_dim,
            seq_len=blocks[0].seq_len,
            wire_format=self._wire_format,
        )

        if self._cache is not None:
            for block in blocks:
                k_key = f"kv:{request_id}:L{block.layer_idx}:K"
                v_key = f"kv:{request_id}:L{block.layer_idx}:V"
                self._cache.put_tensor(k_key, block.key_data, self._wire_format)
                self._cache.put_tensor(v_key, block.value_data, self._wire_format)

        if self._transport is not None:
            self._send_via_transport(meta, blocks)

        self._pending[request_id] = meta
        return meta

    def recv_kv_cache(self, request_id: str,
                      meta: Optional[KVCacheMetadata] = None) -> List[KVCacheBlock]:
        """
        Receive KV cache blocks from the remote prefill node.

        Args:
            request_id: Request identifier to fetch.
            meta: Optional metadata (if already received out-of-band).

        Returns:
            List of KV cache blocks per layer.
        """
        if meta is None:
            meta = self._pending.get(request_id)
        if meta is None:
            if self._transport is not None:
                meta = self._recv_metadata()
            else:
                raise KeyError(f"No metadata for request {request_id}")

        blocks = []
        for layer in range(meta.num_layers):
            k_key = f"kv:{request_id}:L{layer}:K"
            v_key = f"kv:{request_id}:L{layer}:V"

            if self._cache is not None:
                k_data = self._cache.get_tensor(k_key, layer_idx=layer)
                v_data = self._cache.get_tensor(v_key, layer_idx=layer)
            elif self._transport is not None:
                k_data, v_data = self._recv_layer(layer, meta)
            else:
                raise RuntimeError("No transport or cache configured")

            if k_data is None or v_data is None:
                raise RuntimeError(f"Missing KV data for layer {layer}")

            blocks.append(KVCacheBlock(
                layer_idx=layer,
                key_data=k_data,
                value_data=v_data,
                seq_len=meta.seq_len,
            ))

        return blocks

    def _send_via_transport(self, meta: KVCacheMetadata,
                            blocks: List[KVCacheBlock]) -> None:
        """Serialize and send KV data over the transport."""
        meta_bytes = meta.to_bytes()
        self._transport.send(meta_bytes)

        for block in blocks:
            k_wire = block.key_data.astype(np.float16).tobytes()
            v_wire = block.value_data.astype(np.float16).tobytes()
            header = struct.pack('<III', block.layer_idx, len(k_wire), len(v_wire))
            self._transport.send(header + k_wire + v_wire)

    def _recv_metadata(self) -> KVCacheMetadata:
        raw = self._transport.recv(88)
        return KVCacheMetadata.from_bytes(raw)

    def _recv_layer(self, layer: int,
                    meta: KVCacheMetadata) -> Tuple[np.ndarray, np.ndarray]:
        header = self._transport.recv(12)
        _, k_len, v_len = struct.unpack('<III', header)
        k_wire = self._transport.recv(k_len)
        v_wire = self._transport.recv(v_len)
        k_data = np.frombuffer(k_wire, dtype=np.float16).astype(np.float32)
        v_data = np.frombuffer(v_wire, dtype=np.float16).astype(np.float32)
        shape = (meta.num_heads, meta.seq_len, meta.head_dim)
        return k_data.reshape(shape), v_data.reshape(shape)

    @property
    def pending_requests(self) -> List[str]:
        return list(self._pending.keys())

    def clear_request(self, request_id: str) -> None:
        self._pending.pop(request_id, None)
        if self._cache is not None:
            to_remove = [k for k in self._cache.keys() if k.startswith(f"kv:{request_id}:")]
            for k in to_remove:
                self._cache._store.pop(k, None)
