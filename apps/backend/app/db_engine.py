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


def _parse_db_url():
    """Parse DATABASE_URL robustly, handling both encoded and plain passwords.

    The URL may arrive from Render/environment in two forms:
      1. Already-decoded: postgresql://user:pass@word@host/db
         (Render may decode %40 → @ before injecting the env var)
      2. Still-encoded:   postgresql://user:pass%40word@host/db

    Strategy: try SQLAlchemy's make_url directly first (handles case 2).
    If that produces a host that contains '@' (case 1, double-@ confusion),
    fall back to manual parsing: split on '://', then find the LAST '@' to
    separate credentials from host.
    """
    from sqlalchemy.engine import make_url
    from sqlalchemy.engine.url import URL

    raw = _DATABASE_URL

    # First attempt: let SQLAlchemy parse as-is (works for properly encoded URLs)
    try:
        u = make_url(raw)
        # Sanity check: host must not contain '@'
        if u.host and "@" not in u.host:
            return u
    except Exception:
        pass

    # Fallback: manual parse for already-decoded URLs with literal '@' in password.
    # Format: scheme://user:password@host:port/database
    # Split scheme
    scheme, rest = raw.split("://", 1)
    # The LAST '@' separates credentials from host
    cred_part, hostdb_part = rest.rsplit("@", 1)
    # Split credentials — FIRST ':' separates user from password
    username, password = cred_part.split(":", 1)
    # Split host:port/database
    if "/" in hostdb_part:
        host_port, database = hostdb_part.split("/", 1)
    else:
        host_port, database = hostdb_part, "postgres"
    if ":" in host_port:
        host, port_str = host_port.rsplit(":", 1)
        port = int(port_str)
    else:
        host, port = host_port, 5432

    return URL.create(
        drivername=scheme,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def _make_async_pg_url() -> str:
    """Build asyncpg URL from DATABASE_URL, handling encoded/decoded passwords."""
    u = _parse_db_url()
    return str(u.set(drivername="postgresql+asyncpg"))


def _make_sync_pg_url() -> str:
    """Build psycopg2 URL from DATABASE_URL, handling encoded/decoded passwords."""
    u = _parse_db_url()
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
