from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import settings
from app.domain.models import Base
from app.infrastructure.db import engine
from shared_auth import AuditLoggingMiddleware, AuthSettings, PrincipalMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="SARATHI Integration Service", version="0.1.0", lifespan=lifespan)
app.add_middleware(PrincipalMiddleware, settings=AuthSettings())
app.add_middleware(AuditLoggingMiddleware)
app.include_router(router, prefix="/integration/v1")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
