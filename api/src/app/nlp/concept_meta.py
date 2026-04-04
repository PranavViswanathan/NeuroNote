"""Concept meta-layer: classifies synonym and subtopic relationships between concepts.

Calls Claude after each note's graph sync to identify:
- ``SYNONYM_OF`` pairs — same idea, different surface forms (e.g. "ML" ↔ "machine learning")
- ``SUBTOPIC_OF`` pairs — directed specialisation (e.g. "backpropagation" → "neural networks")

Edges are written to the AGE graph so the concept insight service can traverse them.
Only concepts with ``meta_classified_at IS NULL`` in ``concept_registry`` are processed.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

_LOGGER = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a concept taxonomy assistant. Given a list of concepts from a personal \
knowledge base, identify relationships between them.

1. synonym_pairs — concepts that refer to the same idea (abbreviations, aliases, \
different phrasings). Example: "ML" and "machine learning"
2. subtopic_pairs — directed: "specific" is a specialisation of "broader". \
Example: "backpropagation" is a subtopic of "neural networks"

Rules:
- Only pair concepts from the provided list. Do not introduce outside concepts.
- Be conservative — only emit pairs you are highly confident about.
- synonym_pairs are symmetric (order does not matter).

Respond ONLY with valid JSON, no markdown fences:
{
  "synonym_pairs": [{"a": "...", "b": "..."}],
  "subtopic_pairs": [{"specific": "...", "broader": "..."}]
}"""


@dataclass(slots=True)
class ConceptMetaResult:
    synonym_pairs: list[tuple[str, str]] = field(default_factory=list)
    subtopic_pairs: list[tuple[str, str]] = field(default_factory=list)


class ConceptMetaClassifier:
    def __init__(self, *, api_key: str, model: str, timeout_s: float = 15.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_s = timeout_s

    def classify(self, concepts: list[str]) -> ConceptMetaResult:
        """Return synonym/subtopic pairs among *concepts*. Never raises."""
        if len(concepts) < 2:
            return ConceptMetaResult()

        user_msg = "Concepts:\n" + "\n".join(f"- {c}" for c in concepts)

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self._api_key or None)
            msg = client.messages.create(
                model=self._model,
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
                timeout=self._timeout_s,
            )
        except Exception:
            _LOGGER.debug("ConceptMetaClassifier: API call failed", exc_info=True)
            return ConceptMetaResult()

        if not msg.content:
            return ConceptMetaResult()

        raw = msg.content[0].text.strip()  # type: ignore[union-attr]
        # Strip markdown fences if the model wrapped the JSON
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.S).strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            _LOGGER.debug("ConceptMetaClassifier: response is not valid JSON: %r", raw[:200])
            return ConceptMetaResult()

        concepts_set = set(concepts)

        synonym_pairs: list[tuple[str, str]] = []
        for item in data.get("synonym_pairs") or []:
            if not isinstance(item, dict):
                continue
            a = str(item.get("a", "")).strip().lower()
            b = str(item.get("b", "")).strip().lower()
            if a and b and a != b and a in concepts_set and b in concepts_set:
                synonym_pairs.append((a, b))

        subtopic_pairs: list[tuple[str, str]] = []
        for item in data.get("subtopic_pairs") or []:
            if not isinstance(item, dict):
                continue
            specific = str(item.get("specific", "")).strip().lower()
            broader = str(item.get("broader", "")).strip().lower()
            if (
                specific
                and broader
                and specific != broader
                and specific in concepts_set
                and broader in concepts_set
            ):
                subtopic_pairs.append((specific, broader))

        return ConceptMetaResult(
            synonym_pairs=synonym_pairs,
            subtopic_pairs=subtopic_pairs,
        )


__all__ = ["ConceptMetaClassifier", "ConceptMetaResult"]
