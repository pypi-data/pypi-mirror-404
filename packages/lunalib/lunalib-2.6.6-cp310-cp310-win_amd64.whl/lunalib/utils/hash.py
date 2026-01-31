from __future__ import annotations

from typing import Iterable
from lunalib.core.sm2 import SM3Hash


def sm3_digest(data: bytes) -> bytes:
    return SM3Hash.hash(data)


def sm3_hex(data: bytes) -> str:
    return sm3_digest(data).hex()


def hmac_sm3(key: bytes, data: bytes) -> bytes:
    """HMAC-SM3 implementation."""
    block_size = 64
    if len(key) > block_size:
        key = sm3_digest(key)
    if len(key) < block_size:
        key = key + b"\x00" * (block_size - len(key))
    o_key_pad = bytes((b ^ 0x5C) for b in key)
    i_key_pad = bytes((b ^ 0x36) for b in key)
    return sm3_digest(o_key_pad + sm3_digest(i_key_pad + data))


def derive_key_sm3(password: str, salt: bytes, iterations: int = 100000, dklen: int = 32) -> bytes:
    """Derive a key using iterative SM3 hashing (dev-only KDF)."""
    if iterations < 1:
        iterations = 1
    pwd = password.encode()
    key = sm3_digest(pwd + salt)
    for _ in range(iterations - 1):
        key = sm3_digest(key + pwd + salt)
    return key[:dklen]
