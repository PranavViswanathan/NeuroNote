from __future__ import annotations

import logging
from threading import Lock
import time

from app.nlp.config import NlpSettings, get_nlp_settings
from app.nlp.embeddings import build_embedding
from app.nlp.entities import extract_entities
from app.nlp.keyphrases import extract_keyphrases
from app.nlp.metrics import StageTiming, format_stage_timings
from app.nlp.relations import extract_relations
from app.nlp.types import NoteExtractionResult

_LOGGER = logging.getLogger(__name__)


class NoteNlpPipeline:
    _MODEL_HANDLE_CACHE: dict[str, object | None] = {}
    _MODEL_CACHE_LOCK = Lock()

    def __init__(self, settings: NlpSettings | None = None) -> None:
        self._settings = settings or get_nlp_settings()
        self._last_stage_timings: dict[str, float] = {}

    def _get_model_handle(self, model_name: str) -> object | None:
        with self._MODEL_CACHE_LOCK:
            if model_name in self._MODEL_HANDLE_CACHE:
                return self._MODEL_HANDLE_CACHE[model_name]

            if model_name.startswith("spacy:"):
                model_id = model_name.split(":", maxsplit=1)[1]
                try:
                    import spacy  # type: ignore[import-not-found]

                    handle = spacy.load(model_id)
                except Exception:
                    # Missing model should not fail processing; we fall back to rule-based extraction.
                    handle = None
            else:
                handle = object()

            self._MODEL_HANDLE_CACHE[model_name] = handle
            return handle

    def _is_timed_out(self, started_at: float) -> bool:
        return (time.perf_counter() - started_at) * 1000.0 > float(self._settings.timeout_ms)

    def _empty_result(self, *, note_id: str, content_hash: str) -> NoteExtractionResult:
        return NoteExtractionResult(
            note_id=note_id,
            content_hash=content_hash,
            entities=[],
            keyphrases=[],
            relations=[],
            embedding=None,
        )

    def get_last_stage_timings(self) -> dict[str, float]:
        return dict(self._last_stage_timings)

    def extract(
        self,
        *,
        note_id: str,
        content_text: str,
        content_hash: str,
    ) -> NoteExtractionResult:
        stage_timings: list[StageTiming] = []
        started_at = time.perf_counter()

        if self._settings.timeout_ms <= 0:
            stage_timings.append(StageTiming(stage="timeout_guard", duration_ms=0.0))
            self._last_stage_timings = format_stage_timings(stage_timings)
            return self._empty_result(note_id=note_id, content_hash=content_hash)

        if len(content_text.strip().split()) < self._settings.process_min_text_len:
            stage_timings.append(StageTiming(stage="min_text_guard", duration_ms=0.0))
            self._last_stage_timings = format_stage_timings(stage_timings)
            return self._empty_result(note_id=note_id, content_hash=content_hash)

        _ = self._get_model_handle(self._settings.model_name)
        stage_timings.append(StageTiming(stage="model_handle_ready", duration_ms=0.0))

        entities_started = time.perf_counter()
        entities = extract_entities(content_text)
        stage_timings.append(
            StageTiming(
                stage="entities",
                duration_ms=(time.perf_counter() - entities_started) * 1000.0,
            )
        )
        if self._is_timed_out(started_at):
            stage_timings.append(StageTiming(stage="timeout_guard", duration_ms=0.0))
            self._last_stage_timings = format_stage_timings(stage_timings)
            return self._empty_result(note_id=note_id, content_hash=content_hash)

        keyphrases_started = time.perf_counter()
        keyphrases = extract_keyphrases(content_text)
        stage_timings.append(
            StageTiming(
                stage="keyphrases",
                duration_ms=(time.perf_counter() - keyphrases_started) * 1000.0,
            )
        )
        if self._is_timed_out(started_at):
            stage_timings.append(StageTiming(stage="timeout_guard", duration_ms=0.0))
            self._last_stage_timings = format_stage_timings(stage_timings)
            return self._empty_result(note_id=note_id, content_hash=content_hash)

        relations_started = time.perf_counter()
        relations = extract_relations(content_text)
        stage_timings.append(
            StageTiming(
                stage="relations",
                duration_ms=(time.perf_counter() - relations_started) * 1000.0,
            )
        )
        if self._is_timed_out(started_at):
            stage_timings.append(StageTiming(stage="timeout_guard", duration_ms=0.0))
            self._last_stage_timings = format_stage_timings(stage_timings)
            return self._empty_result(note_id=note_id, content_hash=content_hash)

        embedding = None
        if self._settings.enable_embeddings:
            embedding_started = time.perf_counter()
            embedding = build_embedding(content_text)
            stage_timings.append(
                StageTiming(
                    stage="embedding",
                    duration_ms=(time.perf_counter() - embedding_started) * 1000.0,
                )
            )

        stage_timings.append(
            StageTiming(
                stage="total",
                duration_ms=(time.perf_counter() - started_at) * 1000.0,
            )
        )
        self._last_stage_timings = format_stage_timings(stage_timings)
        _LOGGER.debug("NLP stage timings: %s", self._last_stage_timings)

        return NoteExtractionResult(
            note_id=note_id,
            content_hash=content_hash,
            entities=entities,
            keyphrases=keyphrases,
            relations=relations,
            embedding=embedding,
        )
