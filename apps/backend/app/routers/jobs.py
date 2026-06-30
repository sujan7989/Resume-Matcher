"""Job description management endpoints."""

import logging
import re

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import db
from app.schemas import JobUploadRequest, JobUploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# Tags that typically contain job-relevant content
_JOB_RELEVANT_TAGS_RE = re.compile(
    r"<(h[1-6]|p|li|span|div|section|article|title)[^>]*>(.*?)</\1>",
    re.IGNORECASE | re.DOTALL,
)
_TAG_STRIP_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s{2,}")
_MAX_JOB_TEXT_CHARS = 5000


def _extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML, keeping job-relevant content."""
    # Remove script and style blocks entirely
    html = re.sub(r"<(script|style|noscript|head)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
    # Strip all remaining HTML tags
    text = _TAG_STRIP_RE.sub(" ", html)
    # Decode common HTML entities
    text = (
        text.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&nbsp;", " ")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )
    # Collapse whitespace
    text = _WHITESPACE_RE.sub(" ", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


@router.post("/upload", response_model=JobUploadResponse)
async def upload_job_descriptions(request: JobUploadRequest) -> JobUploadResponse:
    """Upload one or more job descriptions.

    Stores the raw text for later use in resume tailoring.
    Returns an array of job_ids corresponding to the input array.
    """
    if not request.job_descriptions:
        raise HTTPException(status_code=400, detail="No job descriptions provided")

    job_ids = []
    for jd in request.job_descriptions:
        if not jd.strip():
            raise HTTPException(status_code=400, detail="Empty job description")

        job = await db.create_job(
            content=jd.strip(),
            resume_id=request.resume_id,
        )
        job_ids.append(job["job_id"])

    return JobUploadResponse(
        message="data successfully processed",
        job_id=job_ids,
        request={
            "job_descriptions": request.job_descriptions,
            "resume_id": request.resume_id,
        },
    )


@router.get("/{job_id}")
async def get_job(job_id: str) -> dict:
    """Get job description by ID."""
    job = await db.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


class ExtractFromUrlRequest(BaseModel):
    url: str


class ExtractFromUrlResponse(BaseModel):
    url: str
    text: str
    char_count: int


@router.post("/extract-from-url", response_model=ExtractFromUrlResponse)
async def extract_job_from_url(request: ExtractFromUrlRequest) -> ExtractFromUrlResponse:
    """Fetch a job posting URL and extract the job description text.

    Fetches the page content, strips HTML, and returns up to 5000 characters
    of job-relevant text. Useful for auto-populating the JD input field.
    """
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; ResumeMatcher/1.0; +https://github.com/resume-matcher)"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to the provided URL timed out.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"The job URL returned an error: HTTP {e.response.status_code}",
        )
    except httpx.RequestError as e:
        logger.warning("Failed to fetch job URL %s: %s", url, e)
        raise HTTPException(status_code=502, detail="Could not reach the provided URL.")

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        raise HTTPException(
            status_code=415,
            detail="The URL does not point to an HTML page.",
        )

    text = _extract_text_from_html(response.text)
    truncated = text[:_MAX_JOB_TEXT_CHARS]

    return ExtractFromUrlResponse(url=url, text=truncated, char_count=len(truncated))
