"""LLM-based concept and relation extractor.

Single structured JSON call that extracts:
- concepts: key ideas in normalised canonical form
- relations: typed semantic relations between concepts
- summary: one-sentence note summary

Returns None on any failure so the pipeline falls back to rule-based extraction.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from app.nlp.llm_client import LLMClient

_LOGGER = logging.getLogger(__name__)

_RELATION_TYPES = frozenset(
    {"IS_A", "PART_OF", "CAUSES", "CONTRASTS_WITH", "USES", "PRODUCES", "RELATED_TO"}
)

_SYSTEM_PROMPT = """You are a knowledge graph extraction engine. Extract from the given note:
1. concepts — the key ideas, entities, and topics, each in canonical lowercase form
   (expand acronyms: "ML" → "machine learning"; prefer singular form; reuse names from the known list)
2. relations — typed semantic relations between concepts using ONLY these relation types:
   IS_A, PART_OF, CAUSES, CONTRASTS_WITH, USES, PRODUCES, RELATED_TO
3. summary — one sentence capturing the note's main idea

Return ONLY valid JSON matching this schema — no markdown fences, no extra keys:
{{
  "concepts": [{{"text": "<string>", "confidence": <0.0-1.0>}}],
  "relations": [{{"source": "<string>", "type": "<RELATION_TYPE>", "target": "<string>", "confidence": <0.0-1.0>}}],
  "summary": "<string>"
}}

Known concepts already in the knowledge base (reuse these exact forms where applicable):
{known_concepts_csv}"""

_USER_TEMPLATE = "Title: {title}\nContent: {content}"


@dataclass(slots=True)
class SLMConcept:
    text: str
    confidence: float


@dataclass(slots=True)
class SLMRelation:
    source: str
    type: str
    target: str
    confidence: float


@dataclass(slots=True)
class SLMExtractionResult:
    concepts: list[SLMConcept]
    relations: list[SLMRelation]
    summary: str


def _parse_result(raw: str) -> SLMExtractionResult | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        _LOGGER.warning("SLM response is not valid JSON: %s", exc)
        return None

    if not isinstance(data, dict):
        return None

    concepts: list[SLMConcept] = []
    for item in data.get("concepts") or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip().lower()
        if not text:
            continue
        try:
            confidence = float(item.get("confidence", 0.8))
        except (TypeError, ValueError):
            confidence = 0.8
        concepts.append(SLMConcept(text=text, confidence=min(max(confidence, 0.0), 1.0)))

    relations: list[SLMRelation] = []
    for item in data.get("relations") or []:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source", "")).strip().lower()
        target = str(item.get("target", "")).strip().lower()
        rel_type = str(item.get("type", "")).strip().upper()
        if not source or not target or rel_type not in _RELATION_TYPES:
            continue
        try:
            confidence = float(item.get("confidence", 0.7))
        except (TypeError, ValueError):
            confidence = 0.7
        relations.append(
            SLMRelation(
                source=source,
                type=rel_type,
                target=target,
                confidence=min(max(confidence, 0.0), 1.0),
            )
        )

    summary = str(data.get("summary", "")).strip()
    return SLMExtractionResult(concepts=concepts, relations=relations, summary=summary)


class SLMExtractor:
    """Extracts concepts and relations from a note using a configurable LLM."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        base_url: str,
        timeout_ms: int = 8000,
    ) -> None:
        self._model = model
        self._api_key = api_key
        self._base_url = base_url
        self._timeout_s = timeout_ms / 1000.0

    def extract(
        self,
        *,
        title: str,
        content: str,
        known_concepts: list[str],
    ) -> SLMExtractionResult | None:
        """Call the LLM and parse the result.

        Returns None on any error so the caller can fall back to rule-based extraction.
        """
        known_csv = ", ".join(known_concepts[:200]) if known_concepts else "none yet"
        system = _SYSTEM_PROMPT.format(known_concepts_csv=known_csv)
        user = _USER_TEMPLATE.format(title=title or "(untitled)", content=content[:4000])

        raw = LLMClient(
            api_key=self._api_key,
            model=self._model,
            base_url=self._base_url,
            timeout_s=self._timeout_s,
        ).complete(system=system, user=user, max_tokens=2048)

        if not raw:
            _LOGGER.warning("LLM returned empty response; falling back to rule-based")
            return None

        _LOGGER.debug("LLM raw response (%d chars): %s", len(raw), raw[:200])

        # Strip markdown code fences if the model wrapped the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return _parse_result(raw)


__all__ = ["SLMConcept", "SLMRelation", "SLMExtractionResult", "SLMExtractor"]
