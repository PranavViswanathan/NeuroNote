from __future__ import annotations

import re

_SEPARATOR_PATTERN = re.compile(r"[-_]+")
_NON_WORD_PATTERN = re.compile(r"[^a-z0-9 ]+")
_SPACE_PATTERN = re.compile(r"\s+")


def normalize_entity_text(raw_text: str) -> str:
    """Normalize entity text for deterministic alias matching."""
    lowered = raw_text.strip().lower()
    with_spaces = _SEPARATOR_PATTERN.sub(" ", lowered)
    alphanumeric = _NON_WORD_PATTERN.sub(" ", with_spaces)
    return _SPACE_PATTERN.sub(" ", alphanumeric).strip()
