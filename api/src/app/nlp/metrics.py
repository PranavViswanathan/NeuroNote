from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StageTiming:
    stage: str
    duration_ms: float


def format_stage_timings(timings: list[StageTiming]) -> dict[str, float]:
    return {timing.stage: timing.duration_ms for timing in timings}
