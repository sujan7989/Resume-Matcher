"""LLM prompts for ATS analysis, skill gap, resume scoring, and interview prep."""

ATS_ANALYSIS_PROMPT = """You are a senior ATS (Applicant Tracking System) expert and technical recruiter with 15+ years experience.

Your job: Give an ACCURATE ATS score that reflects what automated systems would give this resume for this specific job.

JOB DESCRIPTION:
{job_description}

RESUME DATA (JSON):
{resume_json}

CRITICAL MATCHING RULES — ATS systems use semantic matching, not just exact strings:
- "Flask" or "Django" or "Node.js" counts as experience with "REST APIs" and "backend development"
- "MySQL" or "Firebase" or "Supabase" counts as partial match for "PostgreSQL" (SQL databases)
- "JavaScript/TypeScript" counts as "frontend development" experience
- "Git" matches "version control" and "GitHub workflows"
- "AI APIs" / "LLM applications" matches "AI/ML integration"
- "Freelance Software Developer" with full-stack work matches "software developer" roles
- Academic projects count as real experience for entry-level/junior roles
- Count EVERY relevant skill, not just exact matches

SCORING RULES (be calibrated — not too harsh, not too lenient):
- keyword_match: % of CRITICAL JD keywords found verbatim OR semantically in resume
  * 90-100: Almost all critical keywords present (exact or semantic)
  * 70-89: Most critical keywords present, few missing
  * 50-69: About half of critical keywords present
  * Below 50: Many critical keywords genuinely missing
- skills_alignment: How well the resume's technical stack matches JD requirements
  * Score based on semantic equivalents, not just exact tool names
  * Python+Flask+REST APIs is STRONG alignment for a Python backend role
  * If JD requires senior 5+ years and resume has <2 years: reduce by 20-30 points
- experience_relevance: Does experience demonstrate the required responsibilities?
  * Projects count as experience for entry/junior roles
  * API development, database work, deployment ARE relevant
- education_fit: CS/Engineering degree = high fit for software roles (80+)
- resume_completeness: Has all required sections, summary, contact info (score high if present)

IMPORTANT: After a resume is tailored, re-score accurately. If the tailored resume contains the JD keywords, it should score 80-95+.

CRITICAL: For missing_keywords, list EVERY important JD term genuinely NOT found in the resume (including semantic equivalents).
For suggestion, give the EXACT text to add to the resume.

Return ONLY valid JSON:

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
    "score_explanation": "<specific explanation: list each JD keyword and whether it was found (exact or semantic), explain the score precisely>"
  }},
  "keyword_analysis": {{
    "matched_keywords": [
      {{"keyword": "<JD term found in resume — exact or semantic match>", "importance": "critical|important|nice_to_have", "found_in": "skills|experience|education|summary|projects"}}
    ],
    "missing_keywords": [
      {{"keyword": "<JD term genuinely NOT in resume — no semantic equivalent either>", "importance": "critical|important|nice_to_have", "suggestion": "<exact text to add to resume to include this keyword naturally>"}}
    ],
    "total_jd_keywords": <integer — count ALL important terms in JD>,
    "matched_count": <integer>,
    "match_percentage": <float 0-100>
  }},
  "skill_gap": {{
    "critical_missing": [
      {{"skill": "<skill from JD genuinely not in resume>", "context": "<why this skill is critical>", "how_to_address": "<exactly how to add this to resume if candidate has related experience>"}}
    ],
    "partial_match": [
      {{"skill": "<skill name>", "resume_has": "<what resume shows as semantic equivalent>", "jd_needs": "<what JD requires>", "gap": "<specific gap if any>"}}
    ],
    "strong_matches": ["<skill present in both resume and JD — exact or semantic>"]
  }},
  "resume_quality": {{
    "completeness_score": <integer 0-100>,
    "issues": [
      {{"category": "missing_section|weak_bullets|no_metrics|contact_incomplete|no_summary|short_experience|missing_keywords", "description": "<specific issue>", "fix": "<exact fix>"}}
    ],
    "strengths": ["<specific strength>"],
    "bullet_quality": {{
      "has_action_verbs": <boolean>,
      "has_metrics": <boolean>,
      "average_bullet_strength": "weak|moderate|strong",
      "weak_bullets_count": <integer>
    }}
  }},
  "interview_questions": [
    {{
      "question": "<specific question based on JD + resume gap>",
      "category": "technical|behavioral|situational|culture_fit",
      "why_asked": "<why recruiter asks this>",
      "tip": "<how to answer based on resume>"
    }}
  ],
  "tailoring_recommendations": [
    {{
      "priority": "high|medium|low",
      "section": "summary|experience|skills|education|projects",
      "recommendation": "<SPECIFIC actionable recommendation>",
      "example": "<exact text to write>"
    }}
  ],
  "job_fit_verdict": {{
    "fit_level": "excellent|good|moderate|poor",
    "summary": "<honest 2-3 sentence assessment>",
    "biggest_strength": "<strongest alignment point>",
    "biggest_gap": "<most critical missing requirement>"
  }}
}}

CALIBRATION EXAMPLES:
- Resume with Python, Flask, REST APIs, SQL, Git applying to Python Backend Developer role: keyword_match should be 65-75 (has most basics), skills_alignment 65-75
- Same resume AFTER tailoring with FastAPI, PostgreSQL, Docker language in resume: keyword_match 80-90, skills_alignment 80-90
- A perfectly tailored resume with ALL JD keywords explicitly present: 90-95 overall

Generate exactly 3 tailoring recommendations (most impactful only). Keep string values concise (1-2 sentences max).
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


SUGGEST_PROJECT_PROMPT = """You are a career coach and software engineer. Suggest ONE relevant personal project a candidate could build to strengthen their resume for the job below.

The project must:
1. Use skills the candidate ALREADY HAS (from their resume)
2. Be directly relevant to the JD requirements
3. Be completable in 1-4 weeks
4. Sound impressive but realistic for the candidate's level
5. NOT fabricate skills they don't have

RESUME (JSON):
{resume_json}

JOB DESCRIPTION:
{job_description}

Return ONLY valid JSON:
{{
  "name": "Project name (5-8 words, professional)",
  "role": "Creator / Developer",
  "description": [
    "Built X using Y to achieve Z (specific, uses candidate's existing skills)",
    "Implemented A feature demonstrating B capability relevant to the role",
    "Demonstrated C skill from JD by building D component"
  ],
  "rationale": "One sentence explaining why this project specifically helps for this role"
}}

RULES:
- Use only technologies/skills from the resume
- Make it directly relevant to 2-3 JD requirements
- 2-3 bullet points maximum
- Each bullet must start with an action verb
- No fake metrics unless the candidate provided them
"""


ANALYZE_PROJECTS_PROMPT = """You are a senior technical recruiter. Analyze each project in this resume against the job description and score its relevance.

JOB DESCRIPTION:
{job_description}

RESUME PROJECTS:
{projects_json}

CANDIDATE SKILLS:
{skills_json}

For each project, score relevance 0-100 (100 = perfectly aligned with JD, 0 = completely irrelevant).
Also determine whether it should be kept or replaced.

Return ONLY valid JSON:
{{
  "projects": [
    {{
      "index": 0,
      "name": "<project name>",
      "relevance_score": <integer 0-100>,
      "verdict": "keep|replace",
      "reason": "<one sentence explaining the score and verdict>",
      "jd_skills_matched": ["<skill1>", "<skill2>"],
      "jd_skills_missing": ["<skill1>", "<skill2>"]
    }}
  ],
  "summary": "<1-2 sentence overall assessment of the projects section vs the JD>"
}}

SCORING RULES:
- 80-100: Highly relevant — uses JD-critical skills, demonstrates JD requirements directly
- 60-79: Moderately relevant — some JD skills used, partial alignment
- 40-59: Weakly relevant — tangential connection to JD
- 0-39: Not relevant — no meaningful alignment with JD requirements

VERDICT RULES:
- "keep" if relevance_score >= 60
- "replace" if relevance_score < 60

Be honest. A project about gaming when the JD is cloud infrastructure should score < 20.
"""


REPLACE_PROJECT_PROMPT = """You are a career coach. Generate a replacement project for the candidate's least relevant project.

The candidate wants to replace their existing project with something more relevant to the job.

EXISTING PROJECT TO REPLACE:
{existing_project}

WHY IT'S BEING REPLACED:
{replace_reason}

JOB DESCRIPTION:
{job_description}

CANDIDATE'S SKILLS AND EXPERIENCE (use ONLY these):
{resume_json}

ALREADY GENERATED REPLACEMENTS (your project MUST be completely different from these — different domain, different tech focus, different problem solved):
{already_generated}

Generate ONE replacement project that:
1. Uses ONLY skills the candidate already has from their resume
2. Directly addresses what the JD requires
3. Would score 80+ for relevance against this JD
4. Is realistic for the candidate's level
5. Does NOT invent skills or technologies not in their resume
6. Is COMPLETELY DIFFERENT from any project in ALREADY GENERATED REPLACEMENTS above — different name, different domain, different approach

Return ONLY valid JSON:
{{
  "name": "Project name (5-8 words, professional, specific)",
  "role": "Creator / Lead Developer",
  "years": "2024",
  "description": [
    "Built X using [candidate's existing skill] to solve [JD requirement]",
    "Implemented [feature] demonstrating [JD-critical capability] using [candidate's tools]",
    "Deployed/tested/optimized [component] achieving [realistic outcome]"
  ],
  "rationale": "Why this replaces the old project and directly addresses the JD requirements"
}}

CRITICAL: Only use technologies explicitly listed in the candidate's resume skills or experience.
"""
