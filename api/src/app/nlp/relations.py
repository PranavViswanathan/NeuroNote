from __future__ import annotations

import re

from app.nlp.types import ExtractedRelation

_VERB_ALIASES = {
    "are": "ARE",
    "connect": "CONNECTS",
    "connects": "CONNECTS",
    "contains": "CONTAINS",
    "drives": "DRIVES",
    "enables": "ENABLES",
    "helps": "HELPS",
    "improve": "IMPROVES",
    "improves": "IMPROVES",
    "is": "IS",
    "links": "LINKS",
    "represents": "REPRESENTS",
    "support": "SUPPORTS",
    "supports": "SUPPORTS",
    "uses": "USES",
}
_TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def _slugify(raw_text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", raw_text.lower()).strip("-")
    return normalized or "concept"


def extract_relations(text: str) -> list[ExtractedRelation]:
    relations: list[ExtractedRelation] = []
    sentences = re.split(r"[.!?\n;]+", text)
    for sentence in sentences:
        tokens = _TOKEN_PATTERN.findall(sentence)
        if len(tokens) < 3:
            continue

        verb_index = -1
        predicate = ""
        for index, token in enumerate(tokens):
            normalized = token.lower()
            if normalized in _VERB_ALIASES:
                verb_index = index
                predicate = _VERB_ALIASES[normalized]
                break

        if verb_index <= 0 or verb_index >= len(tokens) - 1:
            continue

        subject_text = " ".join(tokens[:verb_index]).strip()
        object_text = " ".join(tokens[verb_index + 1 :]).strip()
        if not subject_text or not object_text:
            continue

        relations.append(
            ExtractedRelation(
                subject_id=f"concept-{_slugify(subject_text)}",
                subject_text=subject_text,
                predicate=predicate,
                object_id=f"concept-{_slugify(object_text)}",
                object_text=object_text,
                confidence=0.72,
            )
        )
    return relations
