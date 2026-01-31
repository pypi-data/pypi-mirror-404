"""
SM3 wrapper utilities with optional accelerated backend.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, List

from lunalib.core.sm2 import SM3Hash

try:  # Optional C extension
    from lunalib.core.sm3_c import sm3_ext as _sm3_ext  # type: ignore
    _HAS_SM3_EXT = True
except Exception:  # pragma: no cover - optional
    _HAS_SM3_EXT = False

try:  # Optional fast backend
    from gmssl import sm3 as gmssl_sm3  # type: ignore
    from gmssl import func as gmssl_func  # type: ignore
    _HAS_GMSSL = True
except Exception:  # pragma: no cover - optional
    _HAS_GMSSL = False


def sm3_digest(data: bytes) -> bytes:
    if _HAS_SM3_EXT:
        return _sm3_ext.sm3_digest(data)
    if _HAS_GMSSL:
        return bytes.fromhex(gmssl_sm3.sm3_hash(gmssl_func.bytes_to_list(data)))
    return SM3Hash.hash(data)


def sm3_hex(data: bytes) -> str:
    return sm3_digest(data).hex()


def sm3_compact_hash(base80: bytes, nonce: int) -> bytes:
    """Hash compact 80-byte base + 8-byte nonce (88 bytes total)."""
    if _HAS_SM3_EXT:
        return _sm3_ext.sm3_hash_compact_88(base80, int(nonce))
    return sm3_digest(base80 + int(nonce).to_bytes(8, "big", signed=False))


def sm3_mine_compact(base80: bytes, start_nonce: int, count: int, difficulty: int, threads: int = 1):
    """Search for a nonce meeting difficulty in a contiguous range (compact header)."""
    if _HAS_SM3_EXT:
        try:
            return _sm3_ext.sm3_mine_compact(base80, int(start_nonce), int(count), int(difficulty), int(threads))
        except TypeError:
            return _sm3_ext.sm3_mine_compact(base80, int(start_nonce), int(count), int(difficulty))
    return None


def sm3_set_abort(flag: bool) -> None:
    """Set/clear SM3 mining abort flag in the C extension (no-op if unavailable)."""
    if _HAS_SM3_EXT:
        try:
            _sm3_ext.sm3_set_abort(bool(flag))
        except Exception:
            pass


def sm3_batch(data_items: Iterable[bytes], max_workers: int = 0) -> List[bytes]:
    """Batch SM3 hashing with optional threading."""
    items = list(data_items)
    if not items:
        return []
    if max_workers and max_workers > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            return list(pool.map(sm3_digest, items))
    return [sm3_digest(item) for item in items]
