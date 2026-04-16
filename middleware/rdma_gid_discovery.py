"""
RDMA GID discovery utilities.

Avoids the hardcoded `gid_index = 0` assumption in the pyverbs
wrapper. Needed because:

- RoCEv2 exposes IPv4-mapped GIDs at higher indices than RoCEv1.
- The "right" index depends on which interface carries the
  RDMA-facing IPv4 address.
- Direct-connect RoCE without a managed switch has no ARP to fall
  back on, so GID selection has to work on first try.

All functions are read-only against the pyverbs Context; they do
not create, modify, or destroy any RDMA resources.
"""

from __future__ import annotations

from typing import List, Optional, Tuple


# IPv4-mapped GID layout: 10 zero bytes, then 0xff 0xff, then 4 IPv4 bytes.
_IPV4_MAPPED_PREFIX = b"\x00" * 10 + b"\xff\xff"


def gid_is_ipv4_mapped(gid: bytes) -> bool:
    """True if `gid` is a 16-byte IPv4-mapped IPv6 address."""
    return len(gid) == 16 and gid.startswith(_IPV4_MAPPED_PREFIX)


def gid_to_ipv4(gid: bytes) -> str:
    """Decode the IPv4 part of an IPv4-mapped GID.

    Raises ValueError if the input is not IPv4-mapped.
    """
    if not gid_is_ipv4_mapped(gid):
        raise ValueError(f"gid is not IPv4-mapped: {gid.hex()}")
    return ".".join(str(b) for b in gid[12:16])


def _gid_raw(entry) -> bytes:
    """Normalize a pyverbs GID result into 16 raw bytes.

    pyverbs exposes `GID` objects with a `.gid` attribute that may be
    a hex string ("fe80:..."), a 16-byte buffer, or an integer.
    """
    raw = getattr(entry, "gid", entry)
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw)
    if isinstance(raw, str):
        # "fe80:0000:...:0001" or "00000000000000000000ffff0a000001"
        cleaned = raw.replace(":", "")
        if len(cleaned) == 32:
            try:
                return bytes.fromhex(cleaned)
            except ValueError:
                pass
        # Fall through: let the caller inspect hex-decoded bytes if possible
    if isinstance(raw, int):
        return raw.to_bytes(16, "big")
    # Last resort: str() and hex-decode
    s = str(raw).replace(":", "")
    if len(s) == 32:
        return bytes.fromhex(s)
    raise TypeError(f"cannot convert GID entry {entry!r} to 16 bytes")


def scan_gid_table(ctx, port: int, max_index: int = 32) -> List[Tuple[int, bytes]]:
    """Return a list of (gid_index, raw_16_byte_gid) for every valid entry.

    Stops at the first index that raises an error or returns all-zero
    bytes. `max_index` is a safety cap so we don't probe forever.
    """
    entries: List[Tuple[int, bytes]] = []
    for idx in range(max_index):
        try:
            entry = ctx.query_gid(port, idx)
        except Exception:
            # pyverbs raises PyverbsError on out-of-range indices; treat
            # that as the end of the table.
            break
        try:
            raw = _gid_raw(entry)
        except TypeError:
            continue
        if raw == b"\x00" * 16:
            continue
        entries.append((idx, raw))
    return entries


def find_ipv4_gid_index(ctx, port: int = 1,
                       preferred_ip: Optional[str] = None,
                       max_index: int = 32) -> int:
    """Scan the GID table and return the best IPv4-mapped index.

    Match order:

    1. If `preferred_ip` is given, the highest-index IPv4-mapped GID
       whose IPv4 equals `preferred_ip` (RoCEv2 entries sit at higher
       indices than RoCEv1).
    2. The highest-index IPv4-mapped GID with any IPv4 address.
    3. Raise RuntimeError with a full scan summary.
    """
    entries = scan_gid_table(ctx, port, max_index=max_index)
    if not entries:
        raise RuntimeError(
            f"no GIDs found on port {port}; rdma_rxe / ConnectX not configured?"
        )

    ipv4_entries = [(idx, raw) for idx, raw in entries if gid_is_ipv4_mapped(raw)]
    if not ipv4_entries:
        summary = ", ".join(f"#{i}={r.hex()}" for i, r in entries)
        raise RuntimeError(
            f"no IPv4-mapped GID on port {port} (scanned {len(entries)} entries: {summary})"
        )

    if preferred_ip is not None:
        matching = [(i, r) for i, r in ipv4_entries if gid_to_ipv4(r) == preferred_ip]
        if matching:
            return max(i for i, _ in matching)

    return max(i for i, _ in ipv4_entries)
