from __future__ import annotations

from pathlib import Path
import statistics
import time

from app.nlp.config import NlpSettings
from app.nlp.pipeline import NoteNlpPipeline

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def _measure_latencies_ms(pipeline: NoteNlpPipeline, text: str, *, runs: int = 10) -> list[float]:
    durations: list[float] = []
    for index in range(runs):
        start = time.perf_counter()
        pipeline.extract(
            note_id=f"perf-note-{index}",
            content_text=text,
            content_hash=f"hash-{index}",
        )
        durations.append((time.perf_counter() - start) * 1000.0)
    return durations


def test_nlp_pipeline_latency_budget_by_fixture_size() -> None:
    pipeline = NoteNlpPipeline(
        settings=NlpSettings(
            model_name="rule-based-small",
            enable_embeddings=True,
            process_min_text_len=1,
            timeout_ms=2000,
        )
    )

    scenarios = [
        ("short_200w.txt", 35.0, 45.0),
        ("medium_800w.txt", 80.0, 100.0),
        ("long_2000w.txt", 200.0, 250.0),
    ]
    for fixture_name, max_mean_ms, max_p95_ms in scenarios:
        text = _load_fixture(fixture_name)
        durations = _measure_latencies_ms(pipeline, text, runs=10)
        mean_latency = statistics.fmean(durations)
        p95_latency = sorted(durations)[int(len(durations) * 0.95) - 1]
        assert mean_latency <= max_mean_ms, (fixture_name, mean_latency)
        assert p95_latency <= max_p95_ms, (fixture_name, p95_latency)


def test_pipeline_falls_back_when_model_name_is_unavailable() -> None:
    pipeline = NoteNlpPipeline(
        settings=NlpSettings(
            model_name="spacy:missing-model",
            enable_embeddings=False,
            process_min_text_len=1,
            timeout_ms=2000,
        )
    )
    result = pipeline.extract(
        note_id="perf-fallback-1",
        content_text="Machine Learning improves Knowledge Graph retrieval.",
        content_hash="hash-fallback-1",
    )
    assert result.keyphrases
    assert result.relations


def test_pipeline_timeout_guard_returns_partial_result() -> None:
    pipeline = NoteNlpPipeline(
        settings=NlpSettings(
            model_name="rule-based-small",
            enable_embeddings=True,
            process_min_text_len=1,
            timeout_ms=0,
        )
    )

    result = pipeline.extract(
        note_id="perf-timeout-1",
        content_text=_load_fixture("long_2000w.txt"),
        content_hash="hash-timeout-1",
    )
    assert result.entities == []
    assert result.keyphrases == []
    assert result.relations == []
    assert result.embedding is None
    assert "timeout_guard" in pipeline.get_last_stage_timings()
