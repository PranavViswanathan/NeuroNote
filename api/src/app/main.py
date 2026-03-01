from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.process import router as process_router

app = FastAPI(title="NeuroNote API", version="0.1.0")
app.include_router(health_router)
app.include_router(process_router, prefix="/v1")
