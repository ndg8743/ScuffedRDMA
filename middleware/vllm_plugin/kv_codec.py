"""
KV blob encoding for the wire.

Blob = b"SKV1" | u32 header_len | header (JSON, utf-8) | array bytes.

Header carries the layer name, block axis, block size, token count, codec,
and one entry per array (name, dtype, shape, offset, nbytes). Dtypes travel
as names so bfloat16 works (numpy has no bfloat16; torch views it as bytes).

Codecs:
  raw           the gathered blocks as-is
  scuffedquant  experimental lossy cold-path compression: vectors along the
                last axis (head_size) go through ScuffedQuant.compress;
                receiver reconstructs with decompress() (stage-1 MSE
                reconstruction; the QJL sketch only corrects inner products
                and is carried for completeness). Use it to study bytes on
                the wire vs. output quality, not as a default.
"""

from __future__ import annotations

import dataclasses
import json
import struct
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

import numpy as np

MAGIC = b"SKV1"
_LEN = struct.Struct("!I")


def _is_torch(x: Any) -> bool:
    return type(x).__module__.startswith("torch")


def _dtype_name(x: Any) -> str:
    if _is_torch(x):
        return str(x.dtype).replace("torch.", "")
    return np.dtype(x.dtype).name


def _as_bytes(x: Any) -> memoryview:
    if _is_torch(x):
        t = x.detach().to("cpu").contiguous()
        return memoryview(t.view(-1).view(_torch().uint8).numpy())
    return memoryview(np.ascontiguousarray(x).reshape(-1).view(np.uint8))


def _torch():
    import torch
    return torch


def _from_bytes(buf: memoryview, dtype: str, shape, want_torch: bool) -> Any:
    shape = tuple(int(s) for s in shape)
    if want_torch:
        torch = _torch()
        raw = np.frombuffer(buf, dtype=np.uint8).copy()
        t = torch.from_numpy(raw).view(getattr(torch, dtype))
        return t.reshape(shape)
    if dtype == "bfloat16":
        torch = _torch()  # only path to bf16 without torch output is via torch
        raw = np.frombuffer(buf, dtype=np.uint8).copy()
        return torch.from_numpy(raw).view(torch.bfloat16).reshape(shape).float().numpy()
    return np.frombuffer(buf, dtype=np.dtype(dtype)).reshape(shape).copy()


def _pack(header: Dict[str, Any], arrays: Dict[str, Any]) -> bytes:
    entries = []
    chunks = []
    off = 0
    for name, a in arrays.items():
        mv = _as_bytes(a)
        entries.append({"name": name, "dtype": _dtype_name(a), "shape": list(a.shape),
                        "offset": off, "nbytes": mv.nbytes})
        chunks.append(mv)
        off += mv.nbytes
    header = dict(header, arrays=entries)
    h = json.dumps(header, separators=(",", ":")).encode()
    out = bytearray(len(MAGIC) + _LEN.size + len(h) + off)
    out[0:4] = MAGIC
    _LEN.pack_into(out, 4, len(h))
    p = 8 + len(h)
    out[8:p] = h
    for mv in chunks:
        out[p:p + mv.nbytes] = mv
        p += mv.nbytes
    return bytes(out)


def read_header(blob: bytes) -> Dict[str, Any]:
    if blob[:4] != MAGIC:
        raise ValueError("not a KV blob")
    (hl,) = _LEN.unpack_from(blob, 4)
    return json.loads(bytes(blob[8:8 + hl]))


def _unpack(blob: bytes, want_torch: bool) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    header = read_header(blob)
    (hl,) = _LEN.unpack_from(blob, 4)
    base = 8 + hl
    mv = memoryview(blob)
    arrays = {}
    for e in header["arrays"]:
        s = base + e["offset"]
        arrays[e["name"]] = _from_bytes(mv[s:s + e["nbytes"]], e["dtype"], e["shape"], want_torch)
    return header, arrays


@lru_cache(maxsize=16)
def _quantizer(dim: int, bits: int, qjl_dim: int, seed: int):
    from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant
    return ScuffedQuant(dim=dim, bits=bits, qjl_dim=qjl_dim, seed=seed)


def encode_kv(blocks: Any, *, layer: str, axis: int, block_size: int, num_tokens: int,
              codec: str = "raw", bits: int = 3, qjl_dim: int = 256, seed: int = 42,
              extra: Optional[Dict[str, Any]] = None) -> bytes:
    """Encode gathered KV blocks (numpy or torch) into a blob."""
    header: Dict[str, Any] = {
        "v": 1, "layer": layer, "axis": int(axis), "block_size": int(block_size),
        "num_tokens": int(num_tokens), "codec": codec,
        "orig_dtype": _dtype_name(blocks), "orig_shape": list(blocks.shape),
    }
    if extra:
        header["extra"] = extra
    if codec == "raw":
        return _pack(header, {"kv": blocks})
    if codec != "scuffedquant":
        raise ValueError(f"unknown codec {codec}")
    if _is_torch(blocks):
        vec = blocks.detach().to("cpu").float().numpy()
    else:
        vec = np.asarray(blocks, dtype=np.float32)
    dim = int(vec.shape[-1])
    sq = _quantizer(dim, bits, qjl_dim, seed)
    c = sq.compress(vec.reshape(-1, dim).astype(np.float32))
    arrays, scalars = {}, {}
    for f in dataclasses.fields(c):
        v = getattr(c, f.name)
        if isinstance(v, np.ndarray):
            arrays[f.name] = v
        else:
            scalars[f.name] = v.item() if hasattr(v, "item") else v
    packed = {}
    for name, a in list(arrays.items()):
        b = _pack_bits_for(name, a, bits)
        if b is not None:
            arrays[name] = _bitpack(a, b)
            packed[name] = {"bits": b, "shape": list(a.shape)}
    header["sq"] = {"dim": dim, "bits": bits, "qjl_dim": qjl_dim, "seed": seed,
                    "scalars": scalars, "packed": packed}
    return _pack(header, arrays)


def _pack_bits_for(name: str, a: np.ndarray, bits: int) -> Optional[int]:
    """Wire bit width for an unpacked uint8 array, or None to send as-is.
    Codebook indices go at `bits` per value, QJL signs at 1 bit; arrays that
    ScuffedQuant already packs are left alone."""
    if a.dtype != np.uint8 or a.size == 0:
        return None
    hi = int(a.max())
    if "sign" in name and hi <= 1:
        return 1
    if "ind" in name and bits < 8 and hi < (1 << bits):
        return bits
    return None


def _bitpack(a: np.ndarray, b: int) -> np.ndarray:
    bitsarr = np.unpackbits(a.reshape(-1, 1), axis=1, bitorder="little")[:, :b]
    return np.packbits(bitsarr.reshape(-1), bitorder="little")


def _bitunpack(p: np.ndarray, b: int, shape) -> np.ndarray:
    n = int(np.prod(shape))
    bitsarr = np.unpackbits(p, bitorder="little")[: n * b].reshape(n, b)
    full = np.zeros((n, 8), np.uint8)
    full[:, :b] = bitsarr
    return np.packbits(full, axis=1, bitorder="little").reshape(shape)


def decode_kv(blob: bytes, *, want_torch: bool = False) -> Tuple[Dict[str, Any], Any]:
    """Return (header, blocks). blocks has the original shape; dtype is the original
    dtype for raw, and the original dtype (cast) for scuffedquant."""
    header, arrays = _unpack(blob, want_torch=False if header_codec(blob) == "scuffedquant" else want_torch)
    if header["codec"] == "raw":
        return header, arrays["kv"]
    from middleware.rdma_tensor_cache.scuffed_quant import CompressedKV
    sqh = header["sq"]
    sq = _quantizer(sqh["dim"], sqh["bits"], sqh["qjl_dim"], sqh["seed"])
    for name, info in sqh.get("packed", {}).items():
        arrays[name] = _bitunpack(arrays[name], info["bits"], info["shape"])
    c = CompressedKV(**arrays, **sqh["scalars"])
    rec = sq.decompress(c).reshape(header["orig_shape"])
    od = header["orig_dtype"]
    if want_torch:
        torch = _torch()
        return header, torch.from_numpy(rec.astype(np.float32)).to(getattr(torch, od))
    if od == "bfloat16":
        return header, rec.astype(np.float32)
    return header, rec.astype(np.dtype(od))


def header_codec(blob: bytes) -> str:
    return read_header(blob)["codec"]


def control_blob(**fields: Any) -> bytes:
    """Small JSON control message (sent on the hot class)."""
    return MAGIC + _LEN.pack(0) + json.dumps(fields, separators=(",", ":")).encode()


def is_control(blob: bytes) -> bool:
    return blob[:4] == MAGIC and _LEN.unpack_from(blob, 4)[0] == 0


def read_control(blob: bytes) -> Dict[str, Any]:
    return json.loads(bytes(blob[8:]))
