from __future__ import annotations

import hashlib
import math
import re

_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def build_embedding(text: str, *, dimensions: int = 384) -> list[float]:
    if dimensions < 1:
        raise ValueError("dimensions must be >= 1")

    vector = [0.0] * dimensions
    tokens = [token.lower() for token in _TOKEN_PATTERN.findall(text)]
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        token_hash = int.from_bytes(digest[:8], "big", signed=False)
        index = token_hash % dimensions
        sign = -1.0 if ((token_hash >> 13) & 1) == 1 else 1.0
        weight = 1.0 + min(len(token), 12) / 12.0
        vector[index] += sign * weight

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]
