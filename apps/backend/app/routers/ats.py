"""ATS (Applicant Tracking System) analysis endpoints."""

import json
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
        logger.error("ATS analysis failed for resume=%s job=%s: %s", resume_id, job_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"ATS analysis failed: {str(e)[:200]}",
        )

    return ATSAnalysisResponse(request_id=str(uuid4()), data=result)


@router.post("/analyze", response_model=ATSAnalysisResponse)
async def analyze_ats_post(request: ATSAnalysisRequest) -> ATSAnalysisResponse:
    return await _run_analysis(request.resume_id, request.job_id)


@router.get("/analyze/{resume_id}/{job_id}", response_model=ATSAnalysisResponse)
async def analyze_ats_get(resume_id: str, job_id: str) -> ATSAnalysisResponse:
    return await _run_analysis(resume_id, job_id)


# ── Suggest Project ────────────────────────────────────────────────────────────

class SuggestProjectRequest(BaseModel):
    resume_id: str
    job_id: str


class SuggestProjectResponse(BaseModel):
    request_id: str
    project: dict


@router.post("/suggest-project", response_model=SuggestProjectResponse)
async def suggest_project(request: SuggestProjectRequest) -> SuggestProjectResponse:
    """Suggest one relevant project the user could build to strengthen their resume for the role."""
    resume = await db.get_resume(request.resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    job = await db.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    from app.llm import complete_json, get_llm_config
    from app.prompts.ats_analysis import SUGGEST_PROJECT_PROMPT

    config = get_llm_config()
    processed = resume.get("processed_data") or {}
    resume_json = json.dumps(processed, indent=2) if processed else resume.get("content", "")

    prompt = SUGGEST_PROJECT_PROMPT.format(
        resume_json=resume_json,
        job_description=job.get("content", ""),
    )

    try:
        result = await complete_json(prompt=prompt, config=config, max_tokens=500, schema_type="enrichment")
        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate project suggestion")
        return SuggestProjectResponse(request_id=str(uuid4()), project=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("suggest_project failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to suggest project: {str(e)[:200]}")


# ── Analyze Projects Relevance ─────────────────────────────────────────────────

class AnalyzeProjectsRequest(BaseModel):
    resume_id: str
    job_id: str


class ProjectRelevance(BaseModel):
    index: int
    name: str
    relevance_score: int
    verdict: str  # "keep" | "replace"
    reason: str
    jd_skills_matched: list[str] = []
    jd_skills_missing: list[str] = []


class AnalyzeProjectsResponse(BaseModel):
    request_id: str
    projects: list[ProjectRelevance]
    summary: str


@router.post("/analyze-projects", response_model=AnalyzeProjectsResponse)
async def analyze_projects(request: AnalyzeProjectsRequest) -> AnalyzeProjectsResponse:
    """Analyze all existing resume projects for relevance against the JD.
    Returns each project ranked by relevance score with keep/replace verdict.
    """
    resume = await db.get_resume(request.resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    job = await db.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    processed = resume.get("processed_data") or {}
    projects = processed.get("personalProjects", [])
    if not projects:
        return AnalyzeProjectsResponse(
            request_id=str(uuid4()),
            projects=[],
            summary="No projects found in resume.",
        )

    from app.llm import complete_json, get_llm_config
    from app.prompts.ats_analysis import ANALYZE_PROJECTS_PROMPT

    config = get_llm_config()
    skills = processed.get("additional", {}).get("technicalSkills", [])

    prompt = ANALYZE_PROJECTS_PROMPT.format(
        job_description=job.get("content", ""),
        projects_json=json.dumps(projects, indent=2),
        skills_json=json.dumps(skills, indent=2),
    )

    try:
        result = await complete_json(prompt=prompt, config=config, max_tokens=1000, schema_type="enrichment")
        if not result or "projects" not in result:
            raise HTTPException(status_code=500, detail="Failed to analyze projects")

        ranked = sorted(result["projects"], key=lambda p: p.get("relevance_score", 0))
        return AnalyzeProjectsResponse(
            request_id=str(uuid4()),
            projects=[ProjectRelevance(**p) for p in ranked],
            summary=result.get("summary", ""),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("analyze_projects failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to analyze projects: {str(e)[:200]}")


# ── Replace Project ────────────────────────────────────────────────────────────

class ReplaceProjectRequest(BaseModel):
    resume_id: str
    job_id: str
    project_index: int   # 0-based index of the project to replace
    replace_reason: str  # Why it's being replaced (from analyze-projects)


class ReplaceProjectResponse(BaseModel):
    request_id: str
    project: dict


@router.post("/replace-project", response_model=ReplaceProjectResponse)
async def replace_project(request: ReplaceProjectRequest) -> ReplaceProjectResponse:
    """Generate a JD-tailored replacement for a specific project.
    The replacement uses only skills/tech from the candidate's existing resume.
    """
    resume = await db.get_resume(request.resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    job = await db.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    processed = resume.get("processed_data") or {}
    projects = processed.get("personalProjects", [])
    if request.project_index < 0 or request.project_index >= len(projects):
        raise HTTPException(status_code=400, detail=f"Invalid project_index {request.project_index}")

    existing_project = projects[request.project_index]

    from app.llm import complete_json, get_llm_config
    from app.prompts.ats_analysis import REPLACE_PROJECT_PROMPT

    config = get_llm_config()

    # Pass resume without the project list to keep context tight
    resume_context = {
        "personalInfo": processed.get("personalInfo", {}),
        "summary": processed.get("summary", ""),
        "workExperience": processed.get("workExperience", []),
        "additional": processed.get("additional", {}),
    }

    prompt = REPLACE_PROJECT_PROMPT.format(
        existing_project=json.dumps(existing_project, indent=2),
        replace_reason=request.replace_reason,
        job_description=job.get("content", ""),
        resume_json=json.dumps(resume_context, indent=2),
    )

    try:
        result = await complete_json(prompt=prompt, config=config, max_tokens=600, schema_type="enrichment")
        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate replacement project")
        # Preserve the original project ID
        result["id"] = existing_project.get("id", request.project_index + 1)
        return ReplaceProjectResponse(request_id=str(uuid4()), project=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("replace_project failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to replace project: {str(e)[:200]}")
