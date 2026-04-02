"""Concept insight generation grounded in the user's own notes.

When a user clicks a concept node in any graph view the frontend calls
``GET /v1/concepts/insight?label=<concept>``.  This service:

1. Full-text searches all notes for the concept label (title + body).
2. Builds a context string of up to ``_MAX_NOTES`` notes (600 chars each).
3. If ``ANTHROPIC_API_KEY`` is configured, calls Claude with a strictly-grounded
   system prompt that forbids external knowledge in the insight paragraph.
4. Returns note references (with snippets), the insight, and learning links.

Graceful degradation:
- No API key → ``insight`` is ``None``; note references still return.
- Claude timeout / parse error → same as no API key for that request.
- No matching notes → empty ``note_refs``, ``notes_found = 0``.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import anthropic
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models.note import Note
from app.nlp.config import NlpSettings, get_nlp_settings
from shared.contracts.python.v1.graph import (
    ConceptInsightResponse,
    ConceptLearningLink,
    ConceptNoteRef,
)

_SYSTEM_PROMPT = """\
You are a knowledge synthesis assistant. Generate an insight about a concept based \
SOLELY on the user's own notes.

Rules:
- The insight must draw only from the provided notes. Do not add external knowledge.
- Reference note titles explicitly, e.g. "In your note 'Title'...".
- Keep the insight to 2–3 focused paragraphs.
- For learning_links: suggest 3–4 genuinely reputable URLs (Wikipedia, official \
documentation, well-known academic sources). Use only real, widely-known URLs.

Respond ONLY with valid JSON in exactly this shape (no markdown fences):
{
  "insight": "...",
  "learning_links": [
    {"title": "...", "url": "https://...", "description": "..."}
  ]
}"""

_MAX_NOTES = 10
_MAX_CONTENT_PER_NOTE = 600   # chars of content passed to Claude per note
_SNIPPET_BEFORE = 60          # chars before the match in the UI snippet
_SNIPPET_AFTER = 90           # chars after the match in the UI snippet


class ConceptInsightService:
    def __init__(
        self,
        session: Session,
        settings: NlpSettings | None = None,
    ) -> None:
        self._session = session
        cfg = settings or get_nlp_settings()
        self._api_key: str = cfg.llm_api_key
        self._model: str = cfg.llm_model

    # ── Public ──────────────────────────────────────────────────────────────

    async def get_insight(
        self,
        concept_label: str,
        limit_notes: int = _MAX_NOTES,
    ) -> ConceptInsightResponse:
        notes = self._find_notes(concept_label, limit=min(limit_notes, _MAX_NOTES))
        note_refs = [self._make_ref(note, concept_label) for note in notes]

        insight: str | None = None
        links: list[ConceptLearningLink] = []

        if notes and self._api_key:
            context = self._build_context(concept_label, notes)
            raw = await self._call_claude(concept_label, context)
            insight = raw.get("insight") or None
            links = [
                ConceptLearningLink(**lnk)
                for lnk in raw.get("learning_links", [])
                if isinstance(lnk, dict)
                and all(k in lnk for k in ("title", "url", "description"))
            ]

        return ConceptInsightResponse(
            concept_label=concept_label,
            notes_found=len(notes),
            note_refs=note_refs,
            insight=insight,
            learning_links=links,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # ── Private ─────────────────────────────────────────────────────────────

    def _find_notes(self, label: str, limit: int) -> list[Note]:
        like = f"%{label.lower()}%"
        rows = self._session.execute(
            select(Note)
            .where(
                or_(
                    func.lower(Note.note_title).like(like),
                    func.lower(Note.content_text).like(like),
                )
            )
            .order_by(Note.updated_at.desc())
            .limit(limit)
        ).scalars().all()
        return list(rows)

    def _make_ref(self, note: Note, label: str) -> ConceptNoteRef:
        raw_text: str = note.content_text or ""
        lower_text = raw_text.lower()
        pos = lower_text.find(label.lower())
        if pos >= 0:
            start = max(0, pos - _SNIPPET_BEFORE)
            end = min(len(raw_text), pos + len(label) + _SNIPPET_AFTER)
            snippet = ("…" if start > 0 else "") + raw_text[start:end].strip() + "…"
        else:
            snippet = raw_text[:150].strip() + ("…" if len(raw_text) > 150 else "")
        return ConceptNoteRef(
            note_id=note.note_id,
            note_title=note.note_title,
            snippet=snippet,
        )

    def _build_context(self, label: str, notes: list[Note]) -> str:
        parts: list[str] = []
        for i, note in enumerate(notes, 1):
            content = (note.content_text or "")[:_MAX_CONTENT_PER_NOTE]
            parts.append(f"[Note {i}: {note.note_title!r}]\n{content}")
        return "\n\n---\n\n".join(parts)

    async def _call_claude(self, label: str, context: str) -> dict:  # type: ignore[type-arg]
        user_msg = (
            f'Concept to analyse: "{label}"\n\n'
            f"User notes mentioning this concept:\n\n{context}"
        )
        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        try:
            msg = await client.messages.create(
                model=self._model,
                max_tokens=1024,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
                timeout=12.0,
            )
            raw = msg.content[0].text.strip()
            # Strip markdown fences if the model wraps the JSON
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.S).strip()
            return json.loads(raw)  # type: ignore[no-any-return]
        except Exception:  # noqa: BLE001
            return {}
