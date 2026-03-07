from __future__ import annotations

from collections import Counter
import re

from app.nlp.types import ExtractedKeyphrase

_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}


def _slugify(raw_text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", raw_text.lower()).strip("-")
    return normalized or "phrase"


def extract_keyphrases(text: str) -> list[ExtractedKeyphrase]:
    tokens = [
        token.lower()
        for token in _TOKEN_PATTERN.findall(text)
        if len(token) >= 3 and token.lower() not in _STOP_WORDS
    ]

    if not tokens:
        return []

    counts: Counter[str] = Counter(tokens)
    for first, second in zip(tokens, tokens[1:]):
        counts[f"{first} {second}"] += 1

    total = float(sum(counts.values()))
    ordered = sorted(
        counts.items(),
        key=lambda pair: (-pair[1], pair[0]),
    )[:10]

    return [
        ExtractedKeyphrase(
            phrase_id=f"concept-{_slugify(phrase)}",
            text=phrase,
            score=round(count / total, 6),
        )
        for phrase, count in ordered
    ]
