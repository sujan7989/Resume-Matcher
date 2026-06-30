"""LLM prompts for ATS analysis, skill gap, resume scoring, and interview prep."""

ATS_ANALYSIS_PROMPT = """You are a senior technical recruiter and resume expert with 15+ years of experience screening candidates.

Analyze this resume against the job description and provide a comprehensive, accurate assessment.

JOB DESCRIPTION:
{job_description}

RESUME DATA (JSON):
{resume_json}

Perform a thorough analysis and return ONLY valid JSON in this exact format:

{{
  "ats_score": {{
    "overall": <integer 0-100>,
    "breakdown": {{
      "keyword_match": <integer 0-100>,
      "skills_alignment": <integer 0-100>,
      "experience_relevance": <integer 0-100>,
      "education_fit": <integer 0-100>,
      "resume_completeness": <integer 0-100>
    }},
    "score_explanation": "<1-2 sentence honest explanation of the overall score>"
  }},
  "keyword_analysis": {{
    "matched_keywords": [
      {{"keyword": "<term>", "importance": "critical|important|nice_to_have", "found_in": "skills|experience|education|summary"}}
    ],
    "missing_keywords": [
      {{"keyword": "<term>", "importance": "critical|important|nice_to_have", "suggestion": "<how to naturally add this to resume>"}}
    ],
    "total_jd_keywords": <integer>,
    "matched_count": <integer>,
    "match_percentage": <float 0-100>
  }},
  "skill_gap": {{
    "critical_missing": [
      {{"skill": "<skill name>", "context": "<why this skill matters for this role>", "how_to_address": "<practical advice: learn X, add project Y, get certification Z>"}}
    ],
    "partial_match": [
      {{"skill": "<skill name>", "resume_has": "<what they have>", "jd_needs": "<what role needs>", "gap": "<specific gap>"}}
    ],
    "strong_matches": ["<skill>", "<skill>"]
  }},
  "resume_quality": {{
    "completeness_score": <integer 0-100>,
    "issues": [
      {{"category": "missing_section|weak_bullets|no_metrics|contact_incomplete|no_summary|short_experience", "description": "<specific issue>", "fix": "<exact actionable fix>"}}
    ],
    "strengths": ["<specific strength>", "<specific strength>"],
    "bullet_quality": {{
      "has_action_verbs": <boolean>,
      "has_metrics": <boolean>,
      "average_bullet_strength": "weak|moderate|strong",
      "weak_bullets_count": <integer>
    }}
  }},
  "interview_questions": [
    {{
      "question": "<specific interview question based on JD + resume>",
      "category": "technical|behavioral|situational|culture_fit",
      "why_asked": "<why a recruiter would ask this>",
      "tip": "<how to answer well based on the resume>"
    }}
  ],
  "tailoring_recommendations": [
    {{
      "priority": "high|medium|low",
      "section": "summary|experience|skills|education|projects",
      "recommendation": "<specific, actionable recommendation>",
      "example": "<concrete example of what to write>"
    }}
  ],
  "job_fit_verdict": {{
    "fit_level": "excellent|good|moderate|poor",
    "summary": "<2-3 sentence honest assessment of overall fit>",
    "biggest_strength": "<strongest alignment point>",
    "biggest_gap": "<most critical thing to address>"
  }}
}}

SCORING RULES (be accurate, not generous):
- keyword_match: % of important JD keywords found in resume (exact + semantic match)
- skills_alignment: how well candidate's skills match role requirements (not just keyword presence)
- experience_relevance: how relevant is their work history to this specific role
- education_fit: does education match requirements (be lenient for equivalent experience)
- resume_completeness: has all standard sections, contact info, LinkedIn/GitHub for tech roles

IMPORTANT:
- Overall score = (keyword_match*0.35 + skills_alignment*0.30 + experience_relevance*0.20 + education_fit*0.10 + resume_completeness*0.05)
- Round to nearest integer
- Be honest — a poor fit should score 30-45, a good fit 65-80, excellent 85+
- Never inflate scores — accuracy builds trust
- Generate exactly 5 interview questions, mix of technical and behavioral
- Interview questions must be specific to THIS resume + THIS job, not generic
- Missing keywords should only include terms actually important for the role
- Tailoring recommendations should be specific and immediately actionable
"""


RESUME_COMPLETENESS_PROMPT = """You are a professional resume reviewer. Analyze this resume for completeness and quality.

RESUME DATA (JSON):
{resume_json}

Return ONLY valid JSON:

{{
  "completeness_score": <integer 0-100>,
  "sections_present": {{
    "contact_info": <boolean>,
    "email": <boolean>,
    "phone": <boolean>,
    "linkedin": <boolean>,
    "github": <boolean>,
    "summary": <boolean>,
    "experience": <boolean>,
    "education": <boolean>,
    "skills": <boolean>,
    "projects": <boolean>
  }},
  "issues": [
    {{
      "severity": "critical|warning|suggestion",
      "issue": "<what is missing or weak>",
      "fix": "<exact fix>"
    }}
  ],
  "strengths": ["<strength>"],
  "overall_verdict": "needs_work|decent|strong|excellent"
}}

SCORING:
- Start at 100, deduct points for issues
- Missing email/phone: -20 each
- Missing summary: -10
- No LinkedIn (for professional roles): -5
- No GitHub (for tech roles): -5
- No metrics in any bullet: -15
- Weak bullet points (generic verbs): -10
- Missing skills section: -15
"""
