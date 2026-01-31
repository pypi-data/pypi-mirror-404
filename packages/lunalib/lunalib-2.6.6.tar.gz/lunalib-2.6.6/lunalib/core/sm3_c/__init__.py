try:
    from .sm3_ext import sm3_digest, sm3_hash_compact_88, sm3_mine_compact
    _HAS_SM3_EXT = True
except Exception:
    _HAS_SM3_EXT = False
    from lunalib.core.sm2 import SM3Hash

    def sm3_digest(data: bytes) -> bytes:
        return SM3Hash.hash(data)

    def sm3_hash_compact_88(base80: bytes, nonce: int) -> bytes:
        return SM3Hash.hash(base80 + int(nonce).to_bytes(8, "big", signed=False))

    def sm3_mine_compact(base80: bytes, start_nonce: int, count: int, difficulty: int, threads: int = 1):
        return None

__all__ = [
    "sm3_digest",
    "sm3_hash_compact_88",
    "sm3_mine_compact",
]