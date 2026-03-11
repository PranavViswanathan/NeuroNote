from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.config import get_database_settings
from app.db.engine import get_session_factory, initialize_database
from app.db.extensions import validate_required_extensions
from app.routes.entity_aliases import router as entity_aliases_router
from app.routes.health import router as health_router
from app.routes.notes import router as notes_router
from app.routes.process import router as process_router


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
    yield


app = FastAPI(title="NeuroNote API", version="0.1.0", lifespan=lifespan)
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
app.include_router(health_router)
app.include_router(notes_router, prefix="/v1")
app.include_router(process_router, prefix="/v1")
app.include_router(entity_aliases_router, prefix="/v1")
