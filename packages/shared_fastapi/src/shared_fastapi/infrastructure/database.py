from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine as sqlalchemy_create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import DatabaseSettings


class Base(DeclarativeBase):
    pass


def create_async_engine(settings: DatabaseSettings) -> AsyncEngine:
    return sqlalchemy_create_async_engine(
        settings.url,
        echo=settings.echo,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout,
        future=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def ensure_database_ready(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.execute(text("SELECT 1"))
