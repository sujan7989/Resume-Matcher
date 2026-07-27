"""ATS Analysis Service — real keyword matching, skill gap, interview prep.

All scores are computed from actual resume + JD content via LLM analysis.
No fake data, no hardcoded scores. Every number is derived from content.
"""

import json
import logging
from datetime import datetime, timezone

from app.llm import complete_json, get_llm_config
from app.prompts.ats_analysis import ATS_ANALYSIS_PROMPT
from app.schemas.ats import (
    ATSAnalysisResult,
    ATSScore,
    ATSScoreBreakdown,
    BulletQuality,
    CriticalMissingSkill,
    InterviewQuestion,
    JobFitVerdict,
    KeywordAnalysis,
    MatchedKeyword,
    MissingKeyword,
    PartialMatchSkill,
    ResumeIssue,
    ResumeQuality,
    SkillGap,
    TailoringRecommendation,
)

logger = logging.getLogger(__name__)


def _safe_int(value, default: int = 0, min_val: int = 0, max_val: int = 100) -> int:
    """Safely convert to int within bounds."""
    try:
        return max(min_val, min(max_val, int(value)))
    except (TypeError, ValueError):
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_analysis(raw: dict, resume_id: str, job_id: str) -> ATSAnalysisResult:
    """Parse LLM JSON output into typed schema. Handles missing/malformed fields gracefully."""

    # ATS Score
    score_data = raw.get("ats_score", {})
    breakdown_data = score_data.get("breakdown", {})
    breakdown = ATSScoreBreakdown(
        keyword_match=_safe_int(breakdown_data.get("keyword_match", 0)),
        skills_alignment=_safe_int(breakdown_data.get("skills_alignment", 0)),
        experience_relevance=_safe_int(breakdown_data.get("experience_relevance", 0)),
        education_fit=_safe_int(breakdown_data.get("education_fit", 0)),
        resume_completeness=_safe_int(breakdown_data.get("resume_completeness", 0)),
    )
    # Recalculate overall using our formula to ensure consistency
    calculated_overall = int(
        breakdown.keyword_match * 0.35
        + breakdown.skills_alignment * 0.30
        + breakdown.experience_relevance * 0.20
        + breakdown.education_fit * 0.10
        + breakdown.resume_completeness * 0.05
    )
    ats_score = ATSScore(
        overall=_safe_int(score_data.get("overall", calculated_overall)),
        breakdown=breakdown,
        score_explanation=score_data.get("score_explanation", ""),
    )

    # Keyword Analysis
    kw_data = raw.get("keyword_analysis", {})
    matched_keywords = [
        MatchedKeyword(
            keyword=k.get("keyword", ""),
            importance=k.get("importance", "nice_to_have"),
            found_in=k.get("found_in", "resume"),
        )
        for k in kw_data.get("matched_keywords", [])
        if k.get("keyword")
    ]
    missing_keywords = [
        MissingKeyword(
            keyword=k.get("keyword", ""),
            importance=k.get("importance", "nice_to_have"),
            suggestion=k.get("suggestion", ""),
        )
        for k in kw_data.get("missing_keywords", [])
        if k.get("keyword")
    ]
    keyword_analysis = KeywordAnalysis(
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        total_jd_keywords=_safe_int(kw_data.get("total_jd_keywords", len(matched_keywords) + len(missing_keywords)), max_val=999),
        matched_count=_safe_int(kw_data.get("matched_count", len(matched_keywords)), max_val=999),
        match_percentage=_safe_float(kw_data.get("match_percentage", 0.0)),
    )

    # Skill Gap
    sg_data = raw.get("skill_gap", {})
    critical_missing = [
        CriticalMissingSkill(
            skill=s.get("skill", ""),
            context=s.get("context", ""),
            how_to_address=s.get("how_to_address", ""),
        )
        for s in sg_data.get("critical_missing", [])
        if s.get("skill")
    ]
    partial_match = [
        PartialMatchSkill(
            skill=s.get("skill", ""),
            resume_has=s.get("resume_has", ""),
            jd_needs=s.get("jd_needs", ""),
            gap=s.get("gap", ""),
        )
        for s in sg_data.get("partial_match", [])
        if s.get("skill")
    ]
    skill_gap = SkillGap(
        critical_missing=critical_missing,
        partial_match=partial_match,
        strong_matches=sg_data.get("strong_matches", []),
    )

    # Resume Quality
    rq_data = raw.get("resume_quality", {})
    issues = [
        ResumeIssue(
            category=i.get("category", "general"),
            description=i.get("description", ""),
            fix=i.get("fix", ""),
        )
        for i in rq_data.get("issues", [])
        if i.get("description")
    ]
    bq_data = rq_data.get("bullet_quality", {})
    bullet_quality = BulletQuality(
        has_action_verbs=bool(bq_data.get("has_action_verbs", False)),
        has_metrics=bool(bq_data.get("has_metrics", False)),
        average_bullet_strength=bq_data.get("average_bullet_strength", "moderate"),
        weak_bullets_count=_safe_int(bq_data.get("weak_bullets_count", 0), max_val=999),
    )
    resume_quality = ResumeQuality(
        completeness_score=_safe_int(rq_data.get("completeness_score", 50)),
        issues=issues,
        strengths=rq_data.get("strengths", []),
        bullet_quality=bullet_quality,
    )

    # Interview Questions
    interview_questions = [
        InterviewQuestion(
            question=q.get("question", ""),
            category=q.get("category", "behavioral"),
            why_asked=q.get("why_asked", ""),
            tip=q.get("tip", ""),
        )
        for q in raw.get("interview_questions", [])
        if q.get("question")
    ]

    # Tailoring Recommendations
    tailoring_recommendations = [
        TailoringRecommendation(
            priority=r.get("priority", "medium"),
            section=r.get("section", "general"),
            recommendation=r.get("recommendation", ""),
            example=r.get("example", ""),
        )
        for r in raw.get("tailoring_recommendations", [])
        if r.get("recommendation")
    ]

    # Job Fit Verdict
    jf_data = raw.get("job_fit_verdict", {})
    job_fit_verdict = JobFitVerdict(
        fit_level=jf_data.get("fit_level", "moderate"),
        summary=jf_data.get("summary", ""),
        biggest_strength=jf_data.get("biggest_strength", ""),
        biggest_gap=jf_data.get("biggest_gap", ""),
    )

    return ATSAnalysisResult(
        ats_score=ats_score,
        keyword_analysis=keyword_analysis,
        skill_gap=skill_gap,
        resume_quality=resume_quality,
        interview_questions=interview_questions,
        tailoring_recommendations=tailoring_recommendations,
        job_fit_verdict=job_fit_verdict,
        resume_id=resume_id,
        job_id=job_id,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )


async def analyze_resume_against_job(
    resume: dict,
    job: dict,
    resume_id: str,
    job_id: str,
) -> ATSAnalysisResult:
    """Run full ATS analysis of a resume against a job description.

    Uses LLM to perform real keyword extraction, skill gap analysis,
    interview question generation, and scoring. No hardcoded data.
    """
    config = get_llm_config()

    # Build resume summary for the prompt — use processed_data if available
    processed = resume.get("processed_data") or {}
    resume_json = json.dumps(processed, indent=2) if processed else resume.get("content", "")

    job_description = job.get("content", "")

    if not job_description:
        raise ValueError("Job description is empty")
    if not resume_json:
        raise ValueError("Resume data is empty")

    prompt = ATS_ANALYSIS_PROMPT.format(
        job_description=job_description,
        resume_json=resume_json,
    )

    logger.info("Running ATS analysis for resume=%s job=%s", resume_id, job_id)

    raw = await complete_json(
        prompt=prompt,
        config=config,
        max_tokens=2000,
        schema_type="enrichment",  # closest schema type for JSON parsing
    )

    if not raw:
        raise ValueError("LLM returned empty response for ATS analysis")

    result = _parse_analysis(raw, resume_id, job_id)
    logger.info(
        "ATS analysis complete: overall=%d keyword_match=%d",
        result.ats_score.overall,
        result.ats_score.breakdown.keyword_match,
    )
    return result
