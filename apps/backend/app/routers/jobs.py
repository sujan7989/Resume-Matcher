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

    Supports LinkedIn, Indeed, Glassdoor, Naukri, Internshala, and any public URL.
    Uses multiple User-Agent headers and fallback strategies to handle paywalls.
    """
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    # Platform-specific User-Agent strategies
    user_agents = [
        # Googlebot — most sites allow this
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        # Real browser UA — fallback
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Mobile UA — some sites return simpler HTML
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    ]

    last_error = None
    for ua in user_agents:
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=20.0,
                headers={
                    "User-Agent": ua,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate",
                    "Cache-Control": "no-cache",
                },
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    break
                last_error = f"HTTP {response.status_code}"
        except httpx.TimeoutException:
            last_error = "timeout"
            continue
        except httpx.RequestError as e:
            last_error = str(e)
            continue
    else:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch the job URL after multiple attempts. Last error: {last_error}. "
                   "Try copying and pasting the job description directly instead."
        )

    content_type = response.headers.get("content-type", "")
    html = response.text

    # LinkedIn returns JSON-LD with job data — extract it
    if "linkedin.com" in url.lower():
        import json as _json
        import re as _re
        # Try to find job description in JSON-LD
        json_ld_matches = _re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, _re.DOTALL)
        for match in json_ld_matches:
            try:
                data = _json.loads(match)
                if isinstance(data, dict) and data.get("description"):
                    desc = _re.sub(r'<[^>]+>', ' ', data["description"])
                    desc = re.sub(r'\s+', ' ', desc).strip()
                    title = data.get("title", "")
                    company = ""
                    if isinstance(data.get("hiringOrganization"), dict):
                        company = data["hiringOrganization"].get("name", "")
                    combined = f"{title}\n{company}\n\n{desc}" if title else desc
                    return ExtractFromUrlResponse(url=url, text=combined[:_MAX_JOB_TEXT_CHARS], char_count=min(len(combined), _MAX_JOB_TEXT_CHARS))
            except Exception:
                continue

    # Indeed — try to find job description div
    if "indeed.com" in url.lower():
        import re as _re
        match = _re.search(r'id="jobDescriptionText"[^>]*>(.*?)</div', html, _re.DOTALL)
        if match:
            text = _TAG_STRIP_RE.sub(" ", match.group(1))
            text = _WHITESPACE_RE.sub(" ", text).strip()
            if len(text) > 100:
                return ExtractFromUrlResponse(url=url, text=text[:_MAX_JOB_TEXT_CHARS], char_count=min(len(text), _MAX_JOB_TEXT_CHARS))

    # Generic HTML extraction
    text = _extract_text_from_html(html)
    if len(text) < 100:
        raise HTTPException(
            status_code=422,
            detail="Could not extract job description from this URL. "
                   "The page may require login or use JavaScript rendering. "
                   "Please copy and paste the job description directly."
        )

    truncated = text[:_MAX_JOB_TEXT_CHARS]
    return ExtractFromUrlResponse(url=url, text=truncated, char_count=len(truncated))
