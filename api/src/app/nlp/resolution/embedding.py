from __future__ import annotations

import math

from app.nlp.embeddings import build_embedding


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity score in [-1, 1]."""
    if len(left) != len(right):
        raise ValueError("left and right vectors must have the same dimension")

    dot_product = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot_product / (left_norm * right_norm)


def find_embedding_candidate(
    *,
    entity_text: str,
    candidates: list[str],
    threshold: float,
) -> tuple[str, float] | None:
    """Return best embedding-similar candidate when threshold is met."""
    query_embedding = build_embedding(entity_text)

    best_candidate = ""
    best_score = -1.0
    for candidate in candidates:
        score = cosine_similarity(query_embedding, build_embedding(candidate))
        if score > best_score:
            best_score = score
            best_candidate = candidate

    if best_score >= threshold and best_candidate:
        return best_candidate, best_score
    return None
