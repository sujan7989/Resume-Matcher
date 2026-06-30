"""ATS (Applicant Tracking System) analysis endpoints."""

import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.database import db
from app.schemas.ats import ATSAnalysisRequest, ATSAnalysisResponse
from app.services.ats_analyzer import analyze_resume_against_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ats", tags=["ATS"])


async def _run_analysis(resume_id: str, job_id: str) -> ATSAnalysisResponse:
    """Shared logic for POST and GET ATS analysis endpoints."""
    resume = await db.get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    job = await db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        result = await analyze_resume_against_job(
            resume=resume,
            job=job,
            resume_id=resume_id,
            job_id=job_id,
        )
    except ValueError as e:
        logger.error("ATS analysis value error for resume=%s job=%s: %s", resume_id, job_id, e)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("ATS analysis failed for resume=%s job=%s: %s", resume_id, job_id, e)
        raise HTTPException(
            status_code=500,
            detail="ATS analysis failed. Please try again.",
        )

    return ATSAnalysisResponse(request_id=str(uuid4()), data=result)


@router.post("/analyze", response_model=ATSAnalysisResponse)
async def analyze_ats_post(request: ATSAnalysisRequest) -> ATSAnalysisResponse:
    """Run ATS analysis for a resume against a job description.

    Accepts resume_id and job_id as a JSON body. Fetches both records,
    runs the LLM-powered analysis, and returns a full ATSAnalysisResponse.
    """
    return await _run_analysis(request.resume_id, request.job_id)


@router.get("/analyze/{resume_id}/{job_id}", response_model=ATSAnalysisResponse)
async def analyze_ats_get(resume_id: str, job_id: str) -> ATSAnalysisResponse:
    """Run ATS analysis for a resume against a job description (GET variant).

    Accepts resume_id and job_id as path parameters. Useful for caching
    and direct URL access.
    """
    return await _run_analysis(resume_id, job_id)
