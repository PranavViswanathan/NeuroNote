from __future__ import annotations

from threading import Event
import time

from app.services.startup_backfill_service import StartupBackfillService


def test_startup_backfill_runs_async_without_blocking() -> None:
    done = Event()
    service = StartupBackfillService()

    def runner() -> None:
        time.sleep(0.05)
        done.set()

    started_at = time.perf_counter()
    service.run_async(runner)
    elapsed = time.perf_counter() - started_at

    assert elapsed < 0.03
    assert done.wait(timeout=1.0)

