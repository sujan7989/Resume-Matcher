"""FastAPI application entry point."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Fix for Windows: Use ProactorEventLoop for subprocess support (Playwright)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import settings
from app.database import db
from app.pdf import close_pdf_renderer, init_pdf_renderer
from app.routers import (
    applications_router,
    ats_router,
    config_router,
    enrichment_router,
    health_router,
    jobs_router,
    resume_wizard_router,
    resumes_router,
)


def _configure_application_logging() -> None:
    """Set application log level from configuration."""
    numeric_level = getattr(logging, settings.log_level, logging.INFO)
    logging.getLogger("app").setLevel(numeric_level)


_configure_application_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    # Force DB init on startup - creates all tables in Supabase/SQLite immediately
    try:
        db._ensure_initialized()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Reset so next request retries initialization
        db._initialized = False

    from app.scripts.migrate_tinydb_to_sqlite import migrate as migrate_tinydb
    result = await migrate_tinydb()
    if result.get("status") == "migrated":
        logger.info("Startup data migration: %s", result)

    from app.config import migrate_legacy_keys
    migrate_legacy_keys()

    # Clean up stale encrypted API keys that can't be decrypted
    # (happens when the encryption secret is regenerated on redeploy).
    # The LLM_API_KEY env var is the source of truth — stale DB copies just produce warnings.
    try:
        from app.crypto import decrypt
        stored = db.get_api_key_ciphertexts()
        stale_providers = [p for p, ct in stored.items() if ct and not decrypt(ct)]
        if stale_providers:
            for provider in stale_providers:
                db.delete_api_key(provider)
            logger.info("Cleared %d stale encrypted API key(s): %s", len(stale_providers), stale_providers)
    except Exception as e:
        logger.warning("Could not clean stale API keys: %s", e)

    yield

    # Shutdown
    try:
        await close_pdf_renderer()
    except Exception as e:
        logger.error(f"Error closing PDF renderer: {e}")
    try:
        await db.close()
    except Exception as e:
        logger.error(f"Error closing database: {e}")


app = FastAPI(
    title="Resume Matcher API",
    description="AI-powered resume tailoring for job descriptions",
    version=__version__,
    lifespan=lifespan,
)

# CORS middleware - origins configurable via CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.effective_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(config_router, prefix="/api/v1")
app.include_router(resumes_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(enrichment_router, prefix="/api/v1")
app.include_router(applications_router, prefix="/api/v1")
app.include_router(resume_wizard_router, prefix="/api/v1")
app.include_router(ats_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Resume Matcher API",
        "version": __version__,
        "docs": "/docs",
    }


def main():
    """Entry point for the project.scripts console script."""
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )


if __name__ == "__main__":
    main()
