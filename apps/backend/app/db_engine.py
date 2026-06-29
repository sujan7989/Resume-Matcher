"""Database engine factory - supports SQLite (local) and PostgreSQL (Supabase).

If DATABASE_URL env var is set (PostgreSQL/Supabase), uses that.
Otherwise falls back to SQLite for local development.
"""

import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.models import Base

__all__ = ["Base", "make_async_engine", "make_sync_engine", "init_models_sync"]

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def _is_postgres() -> bool:
    return bool(DATABASE_URL and ("postgres" in DATABASE_URL or "postgresql" in DATABASE_URL))


def _async_url() -> str:
    """Return async database URL for asyncpg driver."""
    if not _is_postgres():
        return ""
    url = DATABASE_URL
    # Ensure correct driver prefix
    url = url.replace("postgresql://", "postgresql+asyncpg://")
    url = url.replace("postgres://", "postgresql+asyncpg://")
    # asyncpg requires already-decoded URL - decode %40 → @ etc.
    from urllib.parse import unquote
    # Only decode the password portion safely
    if "postgresql+asyncpg://" in url:
        url = url.replace("postgresql+asyncpg://", "")
        parts = url.split("@", 1)
        if len(parts) == 2:
            credentials = unquote(parts[0])
            host_part = parts[1]
            url = f"postgresql+asyncpg://{credentials}@{host_part}"
    return url


def _sync_url() -> str:
    """Return sync database URL for psycopg2 driver."""
    if not _is_postgres():
        return ""
    url = DATABASE_URL
    # psycopg2 handles %40 encoding fine, just ensure correct driver
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://")
    return url


def _apply_sqlite_pragmas(dbapi_connection: Any, _connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
    finally:
        cursor.close()


def _sqlite_url(path: Path, *, driver: str) -> str:
    return f"sqlite+{driver}:///{path}" if driver else f"sqlite:///{path}"


def make_async_engine(path: Path) -> AsyncEngine:
    """Create async engine. Uses PostgreSQL if DATABASE_URL is set, else SQLite."""
    if _is_postgres():
        url = _async_url()
        return create_async_engine(
            url,
            future=True,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    # SQLite fallback
    engine = create_async_engine(_sqlite_url(path, driver="aiosqlite"), future=True)
    event.listen(engine.sync_engine, "connect", _apply_sqlite_pragmas)
    return engine


def make_sync_engine(path: Path) -> Engine:
    """Create sync engine. Uses PostgreSQL if DATABASE_URL is set, else SQLite."""
    if _is_postgres():
        url = _sync_url()
        return create_engine(url, future=True, pool_pre_ping=True)
    # SQLite fallback
    engine = create_engine(_sqlite_url(path, driver=""), future=True)
    event.listen(engine, "connect", _apply_sqlite_pragmas)
    return engine


def init_models_sync(engine: Engine) -> None:
    """Create all tables (idempotent)."""
    Base.metadata.create_all(engine)
