"""Job description management endpoints."""

import asyncio
import logging
import re

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
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


async def _extract_and_cache_keywords(job_id: str, content: str) -> None:
    """Background task: extract JD keywords and cache them so the first improve call is fast."""
    try:
        from app.services.improver import extract_job_keywords
        import hashlib
        keywords = await extract_job_keywords(content)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        cache_updates = {
            "job_keywords": keywords,
            "job_keywords_hash": content_hash,
        }
        raw_company = keywords.get("company")
        raw_role = keywords.get("role")
        if isinstance(raw_company, str) and raw_company.strip():
            cache_updates["company"] = raw_company.strip()
        if isinstance(raw_role, str) and raw_role.strip():
            cache_updates["role"] = raw_role.strip()
        await db.update_job(job_id, cache_updates)
        logger.info("Pre-cached keywords for job %s", job_id)
    except Exception as e:
        logger.warning("Background keyword extraction failed for job %s: %s", job_id, e)


@router.post("/upload", response_model=JobUploadResponse)
async def upload_job_descriptions(
    request: JobUploadRequest,
    background_tasks: BackgroundTasks,
) -> JobUploadResponse:
    """Upload one or more job descriptions.

    Stores the raw text and immediately starts keyword extraction in the
    background so the first improve/tailor call doesn't have to wait for it.
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
        # Pre-cache keywords in background so first improve call is fast
        background_tasks.add_task(_extract_and_cache_keywords, job["job_id"], jd.strip())

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


def _extract_meta_tags(html: str) -> str:
    """Extract job-relevant content from meta tags (Open Graph, Twitter, standard)."""
    import re as _re
    parts: list[str] = []

    # og:title, og:description, twitter:title, twitter:description
    og_patterns = [
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
        r'<title[^>]*>([^<]+)</title>',
    ]
    for pattern in og_patterns:
        m = _re.search(pattern, html, _re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if val and len(val) > 10 and val not in parts:
                parts.append(val)

    return "\n\n".join(parts) if parts else ""


def _extract_json_ld(html: str) -> str:
    """Extract job description from any JSON-LD schema on the page (JobPosting type)."""
    import json as _json
    import re as _re

    json_ld_matches = _re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, _re.DOTALL | _re.IGNORECASE
    )
    for match in json_ld_matches:
        try:
            data = _json.loads(match.strip())
            # Handle arrays of schemas
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                # JobPosting schema or any schema with a description
                desc_raw = item.get("description", "")
                if not desc_raw:
                    continue
                desc = _re.sub(r'<[^>]+>', ' ', str(desc_raw))
                desc = _re.sub(r'\s+', ' ', desc).strip()
                if len(desc) < 50:
                    continue
                title = str(item.get("title", "") or item.get("name", "")).strip()
                company = ""
                org = item.get("hiringOrganization") or item.get("publisher") or {}
                if isinstance(org, dict):
                    company = str(org.get("name", "")).strip()
                parts = [p for p in [title, company, desc] if p]
                return "\n\n".join(parts)
        except Exception:
            continue
    return ""


def _extract_platform_specific(html: str, url_lower: str) -> str:
    """Platform-specific HTML extraction for known job portals."""
    import re as _re

    # LinkedIn — JSON-LD is handled by _extract_json_ld; also try the react-rendered div
    if "linkedin.com" in url_lower:
        for selector in [
            r'class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
            r'id="job-details"[^>]*>(.*?)</section>',
        ]:
            m = _re.search(selector, html, _re.DOTALL | _re.IGNORECASE)
            if m:
                text = _TAG_STRIP_RE.sub(" ", m.group(1))
                text = _WHITESPACE_RE.sub(" ", text).strip()
                if len(text) > 100:
                    return text

    # Indeed
    if "indeed.com" in url_lower:
        for selector in [
            r'id="jobDescriptionText"[^>]*>(.*?)</div>',
            r'class="[^"]*jobsearch-jobDescriptionText[^"]*"[^>]*>(.*?)</div>',
        ]:
            m = _re.search(selector, html, _re.DOTALL | _re.IGNORECASE)
            if m:
                text = _TAG_STRIP_RE.sub(" ", m.group(1))
                text = _WHITESPACE_RE.sub(" ", text).strip()
                if len(text) > 100:
                    return text

    # Glassdoor
    if "glassdoor.com" in url_lower:
        for selector in [
            r'class="[^"]*JobDetails_jobDescription[^"]*"[^>]*>(.*?)</div>',
            r'class="[^"]*desc[^"]*"[^>]*data-test="job-description"[^>]*>(.*?)</div>',
            r'data-test="job-description"[^>]*>(.*?)</div>',
        ]:
            m = _re.search(selector, html, _re.DOTALL | _re.IGNORECASE)
            if m:
                text = _TAG_STRIP_RE.sub(" ", m.group(1))
                text = _WHITESPACE_RE.sub(" ", text).strip()
                if len(text) > 100:
                    return text

    # Naukri
    if "naukri.com" in url_lower:
        for selector in [
            r'class="[^"]*job-desc[^"]*"[^>]*>(.*?)</div>',
            r'class="[^"]*jd-desc[^"]*"[^>]*>(.*?)</section>',
        ]:
            m = _re.search(selector, html, _re.DOTALL | _re.IGNORECASE)
            if m:
                text = _TAG_STRIP_RE.sub(" ", m.group(1))
                text = _WHITESPACE_RE.sub(" ", text).strip()
                if len(text) > 100:
                    return text

    # Internshala
    if "internshala.com" in url_lower:
        m = _re.search(r'class="[^"]*internship_other_details_container[^"]*"[^>]*>(.*?)</div>', html, _re.DOTALL)
        if m:
            text = _TAG_STRIP_RE.sub(" ", m.group(1))
            text = _WHITESPACE_RE.sub(" ", text).strip()
            if len(text) > 100:
                return text

    # Lever.co / Greenhouse.io / Workday / Workable — semantic job description containers
    for selector in [
        r'class="[^"]*job-description[^"]*"[^>]*>(.*?)</div>',
        r'class="[^"]*posting-description[^"]*"[^>]*>(.*?)</div>',
        r'id="job_description"[^>]*>(.*?)</div>',
        r'id="posting-description[^"]*"[^>]*>(.*?)</div>',
        r'data-qa="job-description"[^>]*>(.*?)</div>',
        r'itemprop="description"[^>]*>(.*?)</div>',
    ]:
        m = _re.search(selector, html, _re.DOTALL | _re.IGNORECASE)
        if m:
            text = _TAG_STRIP_RE.sub(" ", m.group(1))
            text = _WHITESPACE_RE.sub(" ", text).strip()
            if len(text) > 100:
                return text

    return ""


@router.post("/extract-from-url", response_model=ExtractFromUrlResponse)
async def extract_job_from_url(request: ExtractFromUrlRequest) -> ExtractFromUrlResponse:
    """Fetch a job posting URL and extract the job description text.

    Supports LinkedIn, Indeed, Glassdoor, Naukri, Internshala, Lever, Greenhouse,
    and any public URL. Uses multiple extraction strategies in priority order.
    """
    url = request.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    url_lower = url.lower()

    # Platform-specific User-Agent strategies
    user_agents = [
        # Real browser UA — best default for most job portals
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        # Googlebot — some sites serve cleaner HTML to bots
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        # Mobile UA — some sites return simpler HTML for mobile
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    ]

    html = ""
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
                    "Referer": "https://www.google.com/",
                },
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    html = response.text
                    break
                last_error = f"HTTP {response.status_code}"
        except httpx.TimeoutException:
            last_error = "Request timed out"
            continue
        except httpx.RequestError as e:
            last_error = str(e)
            continue

    if not html:
        # If Playwright is available, try JS rendering as last resort
        try:
            from app.pdf import _is_playwright_available, init_pdf_renderer, _browser_instance
            if await _is_playwright_available():
                await init_pdf_renderer()
                if _browser_instance:
                    page = await _browser_instance.new_page()
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                        await page.wait_for_timeout(2000)
                        html = await page.content()
                    finally:
                        await page.close()
        except Exception as pw_err:
            logger.warning("Playwright JS rendering also failed: %s", pw_err)

    if not html:
        raise HTTPException(
            status_code=422,
            detail=(
                "This website blocks automatic extraction. "
                "Please copy and paste the Job Description manually."
            ),
        )

    # ── Extraction pipeline (priority order) ─────────────────────────────────

    # Strategy 1: JSON-LD structured data (most reliable, works on LinkedIn, Glassdoor, etc.)
    result = _extract_json_ld(html)
    if result and len(result) >= 100:
        truncated = result[:_MAX_JOB_TEXT_CHARS]
        return ExtractFromUrlResponse(url=url, text=truncated, char_count=len(truncated))

    # Strategy 2: Platform-specific HTML selectors
    result = _extract_platform_specific(html, url_lower)
    if result and len(result) >= 100:
        truncated = result[:_MAX_JOB_TEXT_CHARS]
        return ExtractFromUrlResponse(url=url, text=truncated, char_count=len(truncated))

    # Strategy 3: Generic HTML extraction (strip all tags)
    result = _extract_text_from_html(html)
    if result and len(result) >= 150:
        truncated = result[:_MAX_JOB_TEXT_CHARS]
        return ExtractFromUrlResponse(url=url, text=truncated, char_count=len(truncated))

    # Strategy 4: Meta tags (last resort — often just the job title + teaser)
    result = _extract_meta_tags(html)
    if result and len(result) >= 50:
        truncated = result[:_MAX_JOB_TEXT_CHARS]
        return ExtractFromUrlResponse(url=url, text=truncated, char_count=len(truncated))

    # All strategies failed
    raise HTTPException(
        status_code=422,
        detail=(
            "This website blocks automatic extraction. "
            "Please copy and paste the Job Description manually."
        ),
    )
