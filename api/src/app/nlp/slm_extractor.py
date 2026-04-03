"""SLM-based concept and relation extractor using Claude Haiku.

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
    """Extracts concepts and relations from a note using a Claude Haiku LLM call."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        timeout_ms: int = 8000,
    ) -> None:
        self._model = model
        self._api_key = api_key
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
        try:
            import anthropic  # type: ignore[import-not-found]
        except ImportError:
            _LOGGER.debug("anthropic package not installed; SLM extraction unavailable")
            return None

        known_csv = ", ".join(known_concepts[:200]) if known_concepts else "none yet"
        system = _SYSTEM_PROMPT.format(known_concepts_csv=known_csv)
        user = _USER_TEMPLATE.format(title=title or "(untitled)", content=content[:4000])

        try:
            client = anthropic.Anthropic(api_key=self._api_key or None)
            message = client.messages.create(
                model=self._model,
                max_tokens=2048,
                system=system,
                messages=[{"role": "user", "content": user}],
                timeout=self._timeout_s,
            )
        except Exception as exc:
            _LOGGER.warning(
                "SLM extraction failed (%s: %s); falling back to rule-based",
                type(exc).__name__,
                exc,
            )
            return None

        if not message.content:
            _LOGGER.warning(
                "SLM returned empty content (stop_reason=%s); falling back to rule-based",
                getattr(message, "stop_reason", "unknown"),
            )
            return None

        raw = message.content[0].text.strip()  # type: ignore[union-attr]
        _LOGGER.debug("SLM raw response (%d chars): %s", len(raw), raw[:200])

        if not raw:
            _LOGGER.warning("SLM returned blank text; falling back to rule-based")
            return None

        # Strip markdown code fences if the model wrapped the JSON
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return _parse_result(raw)


__all__ = ["SLMConcept", "SLMRelation", "SLMExtractionResult", "SLMExtractor"]
