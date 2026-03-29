from __future__ import annotations

import logging
from threading import Lock
import time

from app.nlp.config import NlpSettings, get_nlp_settings
from app.nlp.embeddings import build_embedding
from app.nlp.keyphrases import extract_keyphrases
from app.nlp.metrics import StageTiming, format_stage_timings
from app.nlp.relations import extract_relations
from app.nlp.spotting import extract_entities_with_mentions_and_metrics
from app.nlp.types import BlockTextInput, NoteExtractionResult

_LOGGER = logging.getLogger(__name__)


class NoteNlpPipeline:
    _MODEL_HANDLE_CACHE: dict[str, object | None] = {}
    _MODEL_CACHE_LOCK = Lock()

    def __init__(self, settings: NlpSettings | None = None) -> None:
        self._settings = settings or get_nlp_settings()
        self._last_stage_timings: dict[str, float] = {}
        self._last_extraction_hit_counts: dict[str, int] = {}

    def _get_model_handle(self, model_name: str) -> object | None:
        with self._MODEL_CACHE_LOCK:
            if model_name in self._MODEL_HANDLE_CACHE:
                return self._MODEL_HANDLE_CACHE[model_name]

            if model_name.startswith("spacy:"):
                model_id = model_name.split(":", maxsplit=1)[1]
                handle: object | None
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
        self._last_extraction_hit_counts = {}
        return NoteExtractionResult(
            note_id=note_id,
            content_hash=content_hash,
            entities=[],
            keyphrases=[],
            relations=[],
            embedding=None,
            entity_mentions=[],
        )

    def get_last_stage_timings(self) -> dict[str, float]:
        return dict(self._last_stage_timings)

    def get_last_extraction_hit_counts(self) -> dict[str, int]:
        return dict(self._last_extraction_hit_counts)

    def extract(
        self,
        *,
        note_id: str,
        content_text: str,
        content_hash: str,
        blocks: list[BlockTextInput] | None = None,
        dictionary_terms: list[str] | None = None,
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

        model_handle = None
        if self._settings.extraction_profile == "hybrid-spacy":
            model_handle = self._get_model_handle(self._settings.model_name)
        stage_timings.append(StageTiming(stage="model_handle_ready", duration_ms=0.0))

        entities_started = time.perf_counter()
        extraction_blocks = list(blocks or [BlockTextInput(block_index=0, content_text=content_text)])
        entities, entity_mentions, extraction_metrics = extract_entities_with_mentions_and_metrics(
            blocks=extraction_blocks,
            dictionary_terms=dictionary_terms or [],
            extraction_profile=self._settings.extraction_profile,
            model_handle=model_handle,
            seed_terms=list(self._settings.entity_seed_terms),
            enable_regex_fallback=self._settings.enable_regex_fallback,
        )
        self._last_extraction_hit_counts = {
            "dictionary_hits": extraction_metrics.dictionary_hits,
            "spacy_hits": extraction_metrics.spacy_hits,
            "regex_hits": extraction_metrics.regex_hits,
            "merged_mentions": extraction_metrics.merged_mentions,
        }
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
            entity_mentions=entity_mentions,
        )
