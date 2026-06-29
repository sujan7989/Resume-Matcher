"""Database engine factory - supports SQLite (local) and PostgreSQL (Supabase).

If DATABASE_URL env var is set, uses PostgreSQL (Supabase).
Otherwise falls back to SQLite for local development.
"""

import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.models import Base

__all__ = ["Base", "make_async_engine", "make_sync_engine", "init_models_sync"]

_DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()


def _is_postgres() -> bool:
    return bool(_DATABASE_URL and "postgres" in _DATABASE_URL.lower())


def _make_async_pg_url() -> str:
    """Build asyncpg URL from DATABASE_URL, handling encoded passwords."""
    from sqlalchemy.engine import make_url
    from urllib.parse import unquote
    # Decode any percent-encoded characters in the full URL first
    decoded = unquote(_DATABASE_URL)
    # Parse and reconstruct with asyncpg driver
    u = make_url(decoded)
    return str(u.set(drivername="postgresql+asyncpg"))


def _make_sync_pg_url() -> str:
    """Build psycopg2 URL from DATABASE_URL, handling encoded passwords."""
    from sqlalchemy.engine import make_url
    from urllib.parse import unquote
    decoded = unquote(_DATABASE_URL)
    u = make_url(decoded)
    return str(u.set(drivername="postgresql+psycopg2"))


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
        url = _make_async_pg_url()
        return create_async_engine(
            url,
            future=True,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_timeout=30,
        )
    engine = create_async_engine(_sqlite_url(path, driver="aiosqlite"), future=True)
    event.listen(engine.sync_engine, "connect", _apply_sqlite_pragmas)
    return engine


def make_sync_engine(path: Path) -> Engine:
    """Create sync engine. Uses PostgreSQL if DATABASE_URL is set, else SQLite."""
    if _is_postgres():
        url = _make_sync_pg_url()
        return create_engine(url, future=True, pool_pre_ping=True, pool_timeout=30)
    engine = create_engine(_sqlite_url(path, driver=""), future=True)
    event.listen(engine, "connect", _apply_sqlite_pragmas)
    return engine


def init_models_sync(engine: Engine) -> None:
    """Create all tables (idempotent)."""
    Base.metadata.create_all(engine)
