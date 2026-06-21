from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from pathlib import Path
import sys

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_application_service.db")
os.environ.setdefault("AUTH_MODE", "development")

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVICE_ROOT.parents[1]
SHARED_AUTH_SRC = REPO_ROOT / "packages" / "shared_auth" / "src"

for path in (SERVICE_ROOT, SHARED_AUTH_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.domain.models import Base
from app.infrastructure.db import get_session
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(os.environ["DATABASE_URL"], future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    db_file = Path("test_application_service.db")
    if db_file.exists():
        db_file.unlink()


@pytest.fixture()
async def db_session(test_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture()
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client
    app.dependency_overrides.clear()
