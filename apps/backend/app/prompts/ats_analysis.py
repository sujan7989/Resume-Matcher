"""LLM prompts for ATS analysis, skill gap, resume scoring, and interview prep."""

ATS_ANALYSIS_PROMPT = """You are a senior ATS (Applicant Tracking System) expert and technical recruiter with 15+ years experience.

TASK: Score this resume against the job description using a structured 3-step process.

JOB DESCRIPTION:
{job_description}

RESUME DATA (JSON):
{resume_json}

---
STEP 1 — EXTRACT ALL JD KEYWORDS
List every important technical term, skill, tool, framework, methodology, and requirement from the JD.
Include: programming languages, frameworks, databases, tools, methodologies, soft skills, certifications.

STEP 2 — SCAN RESUME FOR EACH KEYWORD
For every keyword from Step 1, check ALL resume sections: summary, skills, experience bullets, project descriptions, education.
Classify each as:
  - EXACT: the exact word/phrase appears in the resume text
  - SEMANTIC: a clear equivalent appears (e.g., "Flask" when JD says "Python web framework", "MySQL" when JD says "PostgreSQL/SQL database")
  - MISSING: neither the exact term nor a clear semantic equivalent is present

IMPORTANT — SEMANTIC MATCHING RULES:
  - "Flask" or "Django" or "FastAPI" appearing in resume = semantic match for "Python backend development"
  - "MySQL" or "Firebase" or "Supabase" = semantic match for "SQL databases" or "PostgreSQL"
  - "REST APIs" in resume = exact match for "REST APIs" or "RESTful APIs" in JD
  - "Node.js" in resume = semantic match for "backend development" or "server-side"
  - "Git" in resume = match for "version control" or "GitHub"
  - Experience bullet mentioning "FastAPI" = EXACT match for FastAPI keyword
  - Summary mentioning "Docker" = EXACT match for Docker keyword
  - DO NOT mark a keyword as MISSING if it appears ANYWHERE in the resume text

STEP 3 — CALCULATE SCORES
  keyword_match = round((exact_count + semantic_count * 0.75) / total_keywords * 100)
  
  skills_alignment: How many JD-required tools are covered (exact or semantic) in skills + experience
    - 0-40%% covered → 30-50
    - 40-60%% covered → 50-65
    - 60-80%% covered → 65-80
    - 80-100%% covered → 80-95

  experience_relevance: Do the experience bullets demonstrate JD responsibilities?
    - Senior role (5+ yrs required) but resume shows <2 yrs → cap at 45
    - Junior/entry role, or JD is flexible: projects count as experience → 55-75

  education_fit: CS/Engineering degree for software role → 80-90

  resume_completeness: All sections present, contact info complete → 75-90

  overall = keyword_match * 0.35 + skills_alignment * 0.30 + experience_relevance * 0.20 + education_fit * 0.10 + resume_completeness * 0.05

CALIBRATION REFERENCE:
  - Original resume: Python, Flask, REST APIs, Git, SQL only → keyword_match=35-45, overall=35-50
  - After tailoring: summary+bullets explicitly say "FastAPI, PostgreSQL, Docker, CI/CD, microservices" → keyword_match=70-85, overall=65-80
  - Perfect match: ALL JD keywords explicitly present throughout, experience level matches → keyword_match=90-95, overall=88-95
  - DO NOT give 90+ overall to a fresh graduate applying to a senior role requiring 5+ years experience

---

Return ONLY valid JSON (no markdown, no extra text):

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
    "score_explanation": "<specific: for each critical JD keyword, state EXACT/SEMANTIC/MISSING and where found. Show your calculation.>"
  }},
  "keyword_analysis": {{
    "matched_keywords": [
      {{"keyword": "<JD term>", "importance": "critical|important|nice_to_have", "found_in": "skills|experience|summary|projects|education", "match_type": "exact|semantic"}}
    ],
    "missing_keywords": [
      {{"keyword": "<JD term genuinely absent — no exact or semantic match anywhere>", "importance": "critical|important|nice_to_have", "suggestion": "<exact sentence to add to resume>"}}
    ],
    "total_jd_keywords": <integer>,
    "matched_count": <integer>,
    "match_percentage": <float 0-100>
  }},
  "skill_gap": {{
    "critical_missing": [
      {{"skill": "<skill genuinely not in resume>", "context": "<why critical>", "how_to_address": "<how to add naturally>"}}
    ],
    "partial_match": [
      {{"skill": "<skill>", "resume_has": "<what resume shows as equivalent>", "jd_needs": "<what JD requires>", "gap": "<gap description>"}}
    ],
    "strong_matches": ["<skill present in both resume and JD>"]
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
      "question": "<specific question>",
      "category": "technical|behavioral|situational|culture_fit",
      "why_asked": "<why recruiter asks this>",
      "tip": "<how to answer>"
    }}
  ],
  "tailoring_recommendations": [
    {{
      "priority": "high|medium|low",
      "section": "summary|experience|skills|education|projects",
      "recommendation": "<specific actionable recommendation>",
      "example": "<exact text to write>"
    }}
  ],
  "job_fit_verdict": {{
    "fit_level": "excellent|good|moderate|poor",
    "summary": "<honest 2-3 sentence assessment>",
    "biggest_strength": "<strongest alignment>",
    "biggest_gap": "<most critical missing requirement>"
  }}
}}

Generate exactly 2 interview questions and 2 tailoring recommendations (most impactful only). Keep all string values concise (1 sentence max).
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
