"""Health check and status endpoints."""

import logging
import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.database import db
from app.llm import check_llm_health, get_llm_config
from app.schemas import HealthResponse, StatusResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])

# Returned for database_stats when the stats query itself fails, so /status can
# still respond (degraded) instead of 500-ing.
_EMPTY_DB_STATS = {
    "total_resumes": 0,
    "total_jobs": 0,
    "total_improvements": 0,
    "has_master_resume": False,
}


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Lightweight liveness check for Docker HEALTHCHECK."""
    return HealthResponse(status="healthy")


@router.get("/db-test")
async def db_test() -> JSONResponse:
    """Debug: test database connection and return actual error if any."""
    try:
        resumes = await db.list_resumes()
        from app.db_engine import _DATABASE_URL, _is_postgres
        return JSONResponse({
            "status": "ok",
            "resume_count": len(resumes),
            "using_postgres": _is_postgres(),
            "db_url_prefix": _DATABASE_URL[:50] if _DATABASE_URL else "SQLite",
        })
    except Exception as e:
        from app.db_engine import _DATABASE_URL, _is_postgres
        return JSONResponse(status_code=500, content={
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()[-1000:],
            "using_postgres": _is_postgres(),
            "db_url_prefix": _DATABASE_URL[:50] if _DATABASE_URL else "SQLite",
        })
    return HealthResponse(status="healthy")
async def get_status() -> StatusResponse:
    """Get comprehensive application status.

    Each subsystem check is isolated: a failure in the LLM health probe or the
    database stats query degrades only its own field instead of 500-ing the
    whole endpoint, so the status page can still report partial/degraded state.
    """
    llm_configured = False
    llm_healthy = False
    try:
        config = get_llm_config()
        # ollama / openai_compatible run without a key, matching check_llm_health.
        llm_configured = bool(config.api_key) or config.provider in ("ollama", "openai_compatible")
        llm_status = await check_llm_health(config)
        llm_healthy = bool(llm_status.get("healthy"))
    except Exception:
        logger.exception("Status: LLM health check failed")

    db_stats: dict = dict(_EMPTY_DB_STATS)
    try:
        db_stats = await db.get_stats()
    except Exception:
        logger.exception("Status: database stats failed")

    has_master_resume = bool(db_stats.get("has_master_resume"))

    return StatusResponse(
        status="ready" if llm_healthy and has_master_resume else "setup_required",
        llm_configured=llm_configured,
        llm_healthy=llm_healthy,
        has_master_resume=has_master_resume,
        database_stats=db_stats,
    )
