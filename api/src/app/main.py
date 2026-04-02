from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
import os
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.db.config import get_database_settings
from app.db.engine import get_session_factory, initialize_database
from app.db.extensions import validate_required_extensions
from app.routes.backfill import router as backfill_router
from app.routes.concepts import router as concepts_router
from app.routes.connections import router as connections_router
from app.routes.backlinks import router as backlinks_router
from app.routes.blocks import router as blocks_router
from app.routes.entity_aliases import router as entity_aliases_router
from app.routes.export import router as export_router
from app.routes.graph import router as graph_router
from app.routes.health import router as health_router
from app.routes.media import router as media_router
from app.routes.notes import router as notes_router
from app.routes.process import router as process_router
from app.core.job_store import mark_stale_jobs_as_failed
from app.core.rate_limiter import limiter
from app.services.startup_backfill_service import StartupBackfillService

# Paths that are always public regardless of API_KEY setting.
_PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

class _RequestIdFilter(logging.Filter):
    """Inject a default request_id on log records that don't have one."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"  # type: ignore[attr-defined]
        return True


logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [%(name)s] [req=%(request_id)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
_request_id_filter = _RequestIdFilter()
logging.getLogger().addFilter(_request_id_filter)
# Also attach to all root handlers so the filter runs before formatting
for _h in logging.getLogger().handlers:
    _h.addFilter(_request_id_filter)
# Suppress httpx HTTP request INFO logs — they don't carry request_id and are noise
logging.getLogger("httpx").setLevel(logging.WARNING)

_LOG = logging.getLogger(__name__)


def _startup_database() -> None:
    initialize_database()
    settings = get_database_settings()
    if not settings.require_postgres_extensions:
        return

    session_factory = get_session_factory()
    with session_factory() as session:
        validate_required_extensions(session)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _startup_database()
    mark_stale_jobs_as_failed()
    backfill_service: StartupBackfillService | None = None
    settings = get_database_settings()
    if settings.database_url.startswith("postgresql"):
        backfill_service = StartupBackfillService()
        backfill_service.run_async(backfill_service.run_note_reprocessing_backfill)

    try:
        yield
    finally:
        if backfill_service is not None:
            backfill_service.shutdown()


app = FastAPI(title="NeuroNote API", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: object) -> object:
    """Attach a unique X-Request-ID to every request for log correlation."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
    # Store on request state so downstream code can read it.
    request.state.request_id = request_id

    # Inject into the logging context for this thread via a LogRecord factory.
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: object, **kwargs: object) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        record.request_id = request_id  # type: ignore[attr-defined]
        return record

    logging.setLogRecordFactory(record_factory)
    try:
        response = await call_next(request)  # type: ignore[operator]
    finally:
        logging.setLogRecordFactory(old_factory)

    response.headers["X-Request-ID"] = request_id  # type: ignore[union-attr]
    return response


@app.middleware("http")
async def api_key_middleware(request: Request, call_next: object) -> object:
    """Enforce API key auth when API_KEY env var is set.

    If API_KEY is empty or unset, all requests pass through (local dev mode).
    Health and docs endpoints are always public.
    """
    required_key = os.environ.get("API_KEY", "").strip()
    if not required_key or request.url.path in _PUBLIC_PATHS:
        return await call_next(request)  # type: ignore[operator]

    provided_key = request.headers.get("X-Api-Key", "")
    if provided_key != required_key:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})

    return await call_next(request)  # type: ignore[operator]


app.include_router(health_router)
app.include_router(notes_router, prefix="/v1")
app.include_router(backlinks_router, prefix="/v1")
app.include_router(blocks_router, prefix="/v1")
app.include_router(process_router, prefix="/v1")
app.include_router(entity_aliases_router, prefix="/v1")
app.include_router(backfill_router, prefix="/v1")
app.include_router(media_router, prefix="/v1")
app.include_router(export_router, prefix="/v1")
app.include_router(graph_router, prefix="/v1")
app.include_router(connections_router, prefix="/v1")
app.include_router(concepts_router, prefix="/v1")
