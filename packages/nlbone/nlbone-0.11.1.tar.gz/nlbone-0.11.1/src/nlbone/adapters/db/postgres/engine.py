from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from nlbone.config.settings import get_settings

_settings = get_settings()

_dsn = _settings.POSTGRES_DB_DSN

if "+asyncpg" in _dsn:
    ASYNC_DSN = _dsn.replace("+asyncpg", "+psycopg")
elif "+psycopg" not in _dsn:
    ASYNC_DSN = _dsn.replace("postgresql://", "postgresql+psycopg://")
else:
    ASYNC_DSN = _dsn

SYNC_DSN = ASYNC_DSN

_async_engine: Optional[AsyncEngine] = None
_async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None

_sync_engine: Optional[Engine] = None
_sync_session_factory: Optional[sessionmaker[Session]] = None


def init_async_engine(echo: Optional[bool] = None) -> AsyncEngine:
    global _async_engine, _async_session_factory
    if _async_engine is not None:
        return _async_engine

    _async_engine = create_async_engine(
        ASYNC_DSN,
        echo=_settings.DEBUG if echo is None else echo,
        pool_pre_ping=True,
        pool_size=_settings.POSTGRES_POOL_SIZE,
        max_overflow=_settings.POSTGRES_MAX_OVERFLOW,
        pool_recycle=_settings.POSTGRES_POOL_RECYCLE,
        pool_timeout=_settings.POSTGRES_POOL_TIMEOUT,
    )

    _async_session_factory = async_sessionmaker(
        bind=_async_engine,
        expire_on_commit=False,
        autoflush=False,
        class_=AsyncSession,
    )

    return _async_engine


@asynccontextmanager
async def async_session() -> AsyncGenerator[AsyncSession, Any]:
    if _async_session_factory is None:
        init_async_engine()
    assert _async_session_factory is not None

    session = _async_session_factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def init_sync_engine(echo: Optional[bool] = None) -> Engine:
    global _sync_engine, _sync_session_factory
    if _sync_engine is not None:
        return _sync_engine

    _sync_engine = create_engine(
        SYNC_DSN,
        echo=_settings.DEBUG if echo is None else echo,
        pool_pre_ping=True,
        pool_size=_settings.POSTGRES_POOL_SIZE,
        max_overflow=_settings.POSTGRES_MAX_OVERFLOW,
        pool_recycle=_settings.POSTGRES_POOL_RECYCLE,
        pool_timeout=_settings.POSTGRES_POOL_TIMEOUT,
        future=True,
    )

    _sync_session_factory = sessionmaker(
        bind=_sync_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )
    return _sync_engine


@contextmanager
def sync_session() -> Generator[Session, None, None]:
    if _sync_session_factory is None:
        init_sync_engine()
    assert _sync_session_factory is not None
    s = _sync_session_factory()
    try:
        yield s
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


# --- Health Checks & Getters ---


async def async_ping() -> None:
    async with async_session() as session:
        await session.execute(text("SELECT 1"))


def sync_ping() -> None:
    with sync_session() as session:
        session.execute(text("SELECT 1"))


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    if _async_session_factory is None:
        init_async_engine()
    assert _async_session_factory is not None
    return _async_session_factory


def get_sync_session_factory() -> sessionmaker[Session]:
    if _sync_session_factory is None:
        init_sync_engine()
    assert _sync_session_factory is not None
    return _sync_session_factory
