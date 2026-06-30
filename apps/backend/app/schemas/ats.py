"""Pydantic models for ATS analysis, skill gap, and interview prep features."""

from typing import Literal
from pydantic import BaseModel, Field


# ── Keyword Analysis ──────────────────────────────────────────────────────────

class MatchedKeyword(BaseModel):
    keyword: str
    importance: Literal["critical", "important", "nice_to_have"]
    found_in: str  # skills | experience | education | summary


class MissingKeyword(BaseModel):
    keyword: str
    importance: Literal["critical", "important", "nice_to_have"]
    suggestion: str  # How to naturally add this


class KeywordAnalysis(BaseModel):
    matched_keywords: list[MatchedKeyword] = Field(default_factory=list)
    missing_keywords: list[MissingKeyword] = Field(default_factory=list)
    total_jd_keywords: int = 0
    matched_count: int = 0
    match_percentage: float = 0.0


# ── ATS Score ─────────────────────────────────────────────────────────────────

class ATSScoreBreakdown(BaseModel):
    keyword_match: int = Field(ge=0, le=100)
    skills_alignment: int = Field(ge=0, le=100)
    experience_relevance: int = Field(ge=0, le=100)
    education_fit: int = Field(ge=0, le=100)
    resume_completeness: int = Field(ge=0, le=100)


class ATSScore(BaseModel):
    overall: int = Field(ge=0, le=100)
    breakdown: ATSScoreBreakdown
    score_explanation: str


# ── Skill Gap ─────────────────────────────────────────────────────────────────

class CriticalMissingSkill(BaseModel):
    skill: str
    context: str        # Why this skill matters for this role
    how_to_address: str # Practical advice


class PartialMatchSkill(BaseModel):
    skill: str
    resume_has: str
    jd_needs: str
    gap: str


class SkillGap(BaseModel):
    critical_missing: list[CriticalMissingSkill] = Field(default_factory=list)
    partial_match: list[PartialMatchSkill] = Field(default_factory=list)
    strong_matches: list[str] = Field(default_factory=list)


# ── Resume Quality ────────────────────────────────────────────────────────────

class ResumeIssue(BaseModel):
    category: str  # missing_section | weak_bullets | no_metrics | etc.
    description: str
    fix: str


class BulletQuality(BaseModel):
    has_action_verbs: bool
    has_metrics: bool
    average_bullet_strength: Literal["weak", "moderate", "strong"]
    weak_bullets_count: int


class ResumeQuality(BaseModel):
    completeness_score: int = Field(ge=0, le=100)
    issues: list[ResumeIssue] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    bullet_quality: BulletQuality


# ── Interview Questions ───────────────────────────────────────────────────────

class InterviewQuestion(BaseModel):
    question: str
    category: Literal["technical", "behavioral", "situational", "culture_fit"]
    why_asked: str
    tip: str


# ── Tailoring Recommendations ─────────────────────────────────────────────────

class TailoringRecommendation(BaseModel):
    priority: Literal["high", "medium", "low"]
    section: str
    recommendation: str
    example: str


# ── Job Fit Verdict ───────────────────────────────────────────────────────────

class JobFitVerdict(BaseModel):
    fit_level: Literal["excellent", "good", "moderate", "poor"]
    summary: str
    biggest_strength: str
    biggest_gap: str


# ── Main Request/Response ─────────────────────────────────────────────────────

class ATSAnalysisRequest(BaseModel):
    resume_id: str
    job_id: str


class ATSAnalysisResult(BaseModel):
    """Full ATS analysis result — all computed from real resume + JD content."""
    ats_score: ATSScore
    keyword_analysis: KeywordAnalysis
    skill_gap: SkillGap
    resume_quality: ResumeQuality
    interview_questions: list[InterviewQuestion] = Field(default_factory=list)
    tailoring_recommendations: list[TailoringRecommendation] = Field(default_factory=list)
    job_fit_verdict: JobFitVerdict
    # Metadata
    resume_id: str
    job_id: str
    analyzed_at: str


class ATSAnalysisResponse(BaseModel):
    request_id: str
    data: ATSAnalysisResult
