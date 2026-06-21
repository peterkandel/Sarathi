from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.domain.models import Base
from app.infrastructure.db import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="SARATHI Identity Service", version="0.1.0", lifespan=lifespan)
app.include_router(router, prefix="/api/v1")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/api/v1/me")
async def me() -> dict[str, str]:
    return {"message": "identity service ready"}
