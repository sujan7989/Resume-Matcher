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


def _parse_db_components() -> dict:
    """Parse DATABASE_URL into components using only string operations.

    Bypasses all URL parsers (SQLAlchemy, urllib) which may mangle usernames
    containing dots (e.g. postgres.projectref) or passwords with special chars.

    Handles both:
      postgresql://user:password@host:port/database
      postgresql://user:pass@word@host:port/database  (literal @ in password)
    """
    raw = _DATABASE_URL
    # Strip scheme
    _, rest = raw.split("://", 1)
    # LAST '@' always separates credentials from host
    cred_part, hostdb_part = rest.rsplit("@", 1)
    # FIRST ':' separates username from password
    colon_idx = cred_part.index(":")
    username = cred_part[:colon_idx].strip()
    password = cred_part[colon_idx + 1:].strip()
    # Split host/port from database
    if "/" in hostdb_part:
        host_port, database = hostdb_part.split("/", 1)
    else:
        host_port, database = hostdb_part, "postgres"
    if ":" in host_port:
        host, port_str = host_port.rsplit(":", 1)
        port = int(port_str)
    else:
        host, port = host_port, 5432
    return {
        "username": username,
        "password": password,
        "host": host,
        "port": port,
        "database": database,
    }


def _make_async_pg_url() -> str:
    """Build asyncpg URL from DATABASE_URL components."""
    c = _parse_db_components()
    import logging
    logging.getLogger(__name__).info(
        "DB async: user=%r host=%r port=%r db=%r",
        c["username"], c["host"], c["port"], c["database"]
    )
    # Build URL manually — avoids SQLAlchemy URL.create() mangling usernames with dots
    from urllib.parse import quote
    user = quote(c["username"], safe="")
    pwd = quote(c["password"], safe="")
    return f"postgresql+asyncpg://{user}:{pwd}@{c['host']}:{c['port']}/{c['database']}"


def _make_sync_pg_url() -> str:
    """Build psycopg2 URL from DATABASE_URL components."""
    c = _parse_db_components()
    import logging
    logging.getLogger(__name__).info(
        "DB sync: user=%r host=%r port=%r db=%r",
        c["username"], c["host"], c["port"], c["database"]
    )
    # Build URL manually — avoids SQLAlchemy URL.create() mangling usernames with dots
    from urllib.parse import quote
    user = quote(c["username"], safe="")
    pwd = quote(c["password"], safe="")
    return f"postgresql+psycopg2://{user}:{pwd}@{c['host']}:{c['port']}/{c['database']}"


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
        c = _parse_db_components()
        import logging
        logging.getLogger(__name__).info(
            "DB async engine: host=%s port=%s user=%s db=%s",
            c["host"], c["port"], c["username"], c["database"]
        )
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
        c = _parse_db_components()
        import logging
        logging.getLogger(__name__).info(
            "DB sync engine: host=%s port=%s user=%s db=%s",
            c["host"], c["port"], c["username"], c["database"]
        )
        return create_engine(url, future=True, pool_pre_ping=True, pool_timeout=30)
    engine = create_engine(_sqlite_url(path, driver=""), future=True)
    event.listen(engine, "connect", _apply_sqlite_pragmas)
    return engine


def init_models_sync(engine: Engine) -> None:
    """Create all tables (idempotent)."""
    Base.metadata.create_all(engine)
