"""LLM prompt templates for resume processing."""

# Language code to full name mapping
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "pt": "Brazilian Portuguese",
}


def get_language_name(code: str) -> str:
    """Get full language name from code."""
    return LANGUAGE_NAMES.get(code, "English")


# Schema with example values - used for prompts to show LLM expected format
RESUME_SCHEMA_EXAMPLE = """{
  "personalInfo": {
    "name": "John Doe",
    "title": "Software Engineer",
    "email": "john@example.com",
    "phone": "+1-555-0100",
    "location": "San Francisco, CA",
    "website": "https://johndoe.dev",
    "linkedin": "linkedin.com/in/johndoe",
    "github": "github.com/johndoe"
  },
  "summary": "Experienced software engineer with 5+ years...",
  "workExperience": [
    {
      "id": 1,
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "years": "Jan 2020 - Present",
      "description": [
        "Led development of microservices architecture",
        "Improved system performance by 40%"
      ]
    }
  ],
  "education": [
    {
      "id": 1,
      "institution": "University of California",
      "degree": "B.S. Computer Science",
      "years": "2014 - 2018",
      "description": "Graduated with honors"
    }
  ],
  "personalProjects": [
    {
      "id": 1,
      "name": "Open Source Tool",
      "role": "Creator & Maintainer",
      "years": "Mar 2021 - Present",
      "description": [
        "Built CLI tool with 1000+ GitHub stars",
        "Used by 50+ companies worldwide"
      ]
    }
  ],
  "additional": {
    "technicalSkills": ["Python", "JavaScript", "AWS", "Docker"],
    "languages": ["English (Native)", "Spanish (Conversational)"],
    "certificationsTraining": ["AWS Solutions Architect"],
    "awards": ["Employee of the Year 2022"]
  },
  "customSections": {
    "publications": {
      "sectionType": "itemList",
      "items": [
        {
          "id": 1,
          "title": "Paper Title",
          "subtitle": "Journal Name",
          "years": "Jun 2023",
          "description": ["Brief description of the publication"]
        }
      ]
    },
    "volunteer_work": {
      "sectionType": "text",
      "text": "Description of volunteer activities..."
    }
  }
}"""

# Schema for improve prompts - excludes personalInfo (preserved from original)
IMPROVE_SCHEMA_EXAMPLE = """{
  "summary": "Experienced software engineer with 5+ years...",
  "workExperience": [
    {
      "id": 1,
      "title": "Senior Software Engineer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "years": "Jan 2020 - Present",
      "description": [
        "Led development of microservices architecture",
        "Improved system performance by 40%"
      ]
    }
  ],
  "education": [
    {
      "id": 1,
      "institution": "University of California",
      "degree": "B.S. Computer Science",
      "years": "2014 - 2018",
      "description": "Graduated with honors"
    }
  ],
  "personalProjects": [
    {
      "id": 1,
      "name": "Open Source Tool",
      "role": "Creator & Maintainer",
      "years": "Mar 2021 - Present",
      "description": [
        "Built CLI tool with 1000+ GitHub stars",
        "Used by 50+ companies worldwide"
      ]
    }
  ],
  "additional": {
    "technicalSkills": ["Python", "JavaScript", "AWS", "Docker"],
    "languages": ["English (Native)", "Spanish (Conversational)"],
    "certificationsTraining": ["AWS Solutions Architect"],
    "awards": ["Employee of the Year 2022"]
  },
  "customSections": {
    "publications": {
      "sectionType": "itemList",
      "items": [
        {
          "id": 1,
          "title": "Paper Title",
          "subtitle": "Journal Name",
          "years": "Jun 2023",
          "description": ["Brief description of the publication"]
        }
      ]
    },
    "volunteer_work": {
      "sectionType": "text",
      "text": "Description of volunteer activities..."
    }
  }
}"""

PARSE_RESUME_PROMPT = """Parse this resume into JSON. Output ONLY the JSON object, no other text.

Map content to standard sections when possible. For non-standard sections (like Publications, Volunteer Work, Research, Hobbies), add them to customSections with an appropriate type.

Example output format:
{schema}

Custom section types:
- "text": Single text block (e.g., objective, statement)
- "itemList": List of items with title, subtitle, years, description (e.g., publications, research)
- "stringList": Simple list of strings (e.g., hobbies, interests)

Rules:
- Use "" for missing text fields, [] for missing arrays, null for optional fields
- Number IDs starting from 1
- Format dates preserving the original precision. Keep months when present: "Jan 2020 - Dec 2023", "May 2021 - Present". Use "YYYY - YYYY" only when the source has no months.
- Use snake_case for custom section keys (e.g., "volunteer_work", "publications")
- Preserve the original section name as a descriptive key
- Normalize date separators: "2020-2021" → "2020 - 2021", "Current"/"Ongoing" → "Present". Do NOT discard months.
- For ambiguous dates like "3 years experience", infer approximate years from context or use "~YYYY"
- Flag overlapping dates (concurrent roles) by preserving both, don't merge

Resume to parse:
{resume_text}"""

EXTRACT_KEYWORDS_PROMPT = """You are an expert ATS (Applicant Tracking System) analyst. Deeply analyze this job description and extract ALL terms that an ATS would score against.

Output ONLY the JSON object, no other text.

Think like an ATS system: extract EVERY term that appears in the JD that would differentiate a matching resume from a non-matching one.

{{
  "company": "<hiring company name or empty string>",
  "role": "<exact job title from posting>",
  "required_skills": ["<every required technical skill, tool, technology, framework, language>"],
  "preferred_skills": ["<every preferred/nice-to-have skill>"],
  "ats_critical_keywords": ["<top 20 terms that MUST appear in a resume to pass ATS for this role>"],
  "action_verbs": ["<action verbs used in JD responsibilities like: developed, designed, implemented, led, managed>"],
  "responsibilities": ["<key responsibilities as short phrases>"],
  "industry_terms": ["<domain-specific terms: e.g., microservices, REST API, CI/CD, Agile, SCRUM>"],
  "soft_skills": ["<soft skills mentioned: communication, teamwork, problem-solving>"],
  "certifications": ["<required or preferred certifications>"],
  "experience_requirements": ["<experience requirements as strings>"],
  "education_requirements": ["<education requirements>"],
  "experience_years": <integer years required, 0 if not specified>,
  "seniority_level": "<entry|junior|mid|senior|lead|principal|staff>",
  "keywords": ["<all other important keywords not captured above>"]
}}

IMPORTANT: Be exhaustive. Miss nothing. An ATS scores every single term that appears in the resume vs the JD.
For ats_critical_keywords: these are the exact strings that MUST appear in the resume to maximize ATS score.

Job description:
{job_description}"""

CRITICAL_TRUTHFULNESS_RULES_TEMPLATE = """CRITICAL TRUTHFULNESS RULES - NEVER VIOLATE:
1. DO NOT add any skill, tool, technology, or certification that is not explicitly mentioned in the original resume
2. DO NOT invent numeric achievements (e.g., "increased by 30%") unless they exist in original
3. DO NOT add company names, product names, or technical terms not in the original
4. DO NOT upgrade experience level (e.g., "Junior" -> "Senior")
5. DO NOT add languages, frameworks, or platforms the candidate hasn't used
6. DO NOT extend employment dates or change timelines. Copy date ranges exactly as they appear, including months.
7. {rule_7}
8. Preserve factual accuracy - only use information provided by the candidate
9. For technicalSkills: reorder so JD-relevant skills appear FIRST. Remove skills that are completely irrelevant to this specific JD (e.g., remove "SAP NetWeaver" for a Python developer role). Keep the top 15-20 most relevant skills. DO NOT remove certifications, languages, or awards — only trim technicalSkills.

Violation of these rules could cause serious problems for the candidate in job interviews.
"""


def _build_truthfulness_rules(rule_7: str) -> str:
    return CRITICAL_TRUTHFULNESS_RULES_TEMPLATE.format(rule_7=rule_7)


CRITICAL_TRUTHFULNESS_RULES = {
    "nudge": _build_truthfulness_rules(
        "DO NOT add new bullet points or content - only rephrase existing content"
    ),
    "keywords": _build_truthfulness_rules(
        "You may rephrase existing bullet points to include keywords, but do NOT add new bullet points"
    ),
    "full": _build_truthfulness_rules(
        "You may expand existing bullet points or add new ones that elaborate on existing work, but DO NOT invent entirely new responsibilities"
    ),
}

IMPROVE_RESUME_PROMPT_NUDGE = """Lightly rephrase this resume toward the job description. Output ONLY the JSON object, no other text.

{critical_truthfulness_rules}

IMPORTANT: Generate ALL text content in {output_language}.
Do NOT include personalInfo in your output.

WHAT "LIGHT NUDGE" MEANS:
- Find existing bullet points and summary phrases that already describe work matching JD keywords
- Rephrase ONLY those phrases using the JD's exact terminology
- Example: resume says "tested web apps" → JD says "QA testing" → rephrase to "performed QA testing on web applications"
- Do NOT add new bullet points, new sections, or new skills
- Do NOT reorder sections or projects
- Do NOT change the job title, summary structure, or overall tone
- Touch the absolute minimum number of words needed to surface the match

Job Description:
{job_description}

JD Keywords (use only where resume already supports them):
{job_keywords}

Original Resume:
{original_resume}

Output in this JSON format:
{schema}"""

IMPROVE_RESUME_PROMPT_KEYWORDS = """Enhance this resume with JD keywords. Output ONLY the JSON object, no other text.

{critical_truthfulness_rules}

IMPORTANT: Generate ALL text content in {output_language}.
Do NOT include personalInfo in your output.

WHAT "KEYWORD ENHANCE" MEANS — execute ALL steps in order:

1. SUMMARY: Completely rewrite the summary to target this specific role.
   - Open with the JD's exact role title (e.g., "Python Developer", "Backend Engineer")
   - Include 5-7 exact keywords from the JD that the resume already supports (even semantically)
   - Map the candidate's experience to the JD: Flask→"REST API development", MySQL/Supabase→"database design", Node.js→"backend services", projects→"application development"
   - End with a statement showing motivation for this specific role
   - 3-4 sentences

2. TECHNICAL SKILLS: Restructure the skills section:
   - Add JD terms that are SEMANTICALLY equivalent to existing skills:
     * If resume has Flask + the JD mentions "REST APIs" → add "RESTful API Development" as explicit skill
     * If resume has MySQL/Firebase/Supabase + JD mentions SQL databases → list "SQL", "Database Design"
     * If resume has Node.js + JD mentions "backend" → add "Backend Development"
     * If resume has Git + JD mentions "version control / CI" → include "Git", "GitHub"
   - Move JD-critical terms to the FRONT
   - Keep top 12-15 most relevant, remove zero-relevance skills

3. EXPERIENCE: For EVERY work experience entry:
   - Rewrite bullets using the JD's EXACT terminology wherever experience supports it
   - "Built solutions using Python, Flask" → "Developed Python-based RESTful APIs and backend services using Flask"
   - "Integrated REST APIs, databases" → "Integrated RESTful APIs, PostgreSQL/SQL databases, and authentication systems"
   - "Performed requirement analysis, testing" → "Conducted requirements analysis, implemented software testing, and maintained CI/CD-ready codebases"
   - Make EVERY bullet highly specific and keyword-rich

4. PROJECTS: For EVERY project:
   - Rewrite to use JD terminology for the same concepts
   - "browser extension" → "full-stack web application with REST API backend"
   - "database integration" → "PostgreSQL/SQL database design and integration"
   - "deployment preparation" → "Docker-ready deployment pipeline"
   - Front-load each bullet with action verbs the JD uses

5. Keep all dates, company names, institutions exactly as in the original.
6. Do NOT use em dash anywhere. Do NOT fabricate metrics.

Job Description:
{job_description}

JD Keywords (in priority order — surface these wherever resume already supports them):
{job_keywords}

Original Resume:
{original_resume}

Output in this JSON format:
{schema}"""

IMPROVE_RESUME_PROMPT_FULL = """Fully tailor this resume for the job description. Output ONLY the JSON object, no other text.

{critical_truthfulness_rules}

IMPORTANT: Generate ALL text content in {output_language}.
Do NOT include personalInfo in your output.

WHAT "FULL TAILOR" MEANS — execute ALL steps:

1. SUMMARY: Completely rewrite for this specific role.
   - Open with the JD's exact role title (e.g. "Python Backend Developer", "Software Engineer")
   - Include 6+ JD keywords the resume already supports (semantic mapping allowed)
   - Translate candidate's background using JD vocabulary: Flask → "REST API development", MySQL/Firebase → "database management", projects → "full-stack application development"
   - 3-4 sentences

2. TECHNICAL SKILLS: Reorder so JD-critical skills appear first.
   - Add JD-relevant terms as explicit skills if the resume already demonstrates them:
     * Flask/Node.js experience → add "RESTful API Development", "Backend Development"
     * MySQL/Firebase/Supabase → add "SQL Databases", "Database Design"
     * Deployed anything → add "Deployment", "Application Deployment"
     * Python + AI work → add "Python Development", "AI Integration"
   - Keep top 15 most relevant, remove zero-relevance skills

3. EXPERIENCE: Rewrite EVERY bullet to use JD terminology:
   - Map existing work to JD's language: 
     * "Built solutions using Python, Flask" → "Developed Python-based microservices and REST APIs using Flask"
     * "Integrated REST APIs, databases" → "Designed and integrated RESTful APIs with SQL databases (MySQL/PostgreSQL)"
     * "deployment support" → "implemented deployment pipelines and application maintenance"
   - Add 1 new bullet per role to expand on existing work (not invent)

4. PROJECTS: Rewrite every project description to use JD terminology:
   - "API handling" → "RESTful API design and integration"
   - "database operations" → "SQL database design and CRUD operations"
   - "deployment preparation" → "Docker-ready deployment configuration"
   - List the JD-relevant technologies first in each project's tech stack

5. Keep all dates, company names, institutions exactly as in original.
6. Do NOT fabricate metrics, tools, or experience that doesn't exist.
7. Do NOT use em dash anywhere.

Job Description:
{job_description}

JD Keywords (incorporate all that the resume already supports):
{job_keywords}

Original Resume:
{original_resume}

Output in this JSON format:
{schema}"""

IMPROVE_PROMPT_OPTIONS = [
    {
        "id": "nudge",
        "label": "Light Nudge",
        "description": "Rephrase existing bullets using JD language. No new content added. Safest option.",
    },
    {
        "id": "keywords",
        "label": "Keyword Enhance",
        "description": "Inject JD keywords into summary & skills, reorder sections by relevance. Moderate changes.",
    },
    {
        "id": "full",
        "label": "Full Tailor",
        "description": "Rewrite summary for the role, align all sections with JD, optimize skills order. Maximum impact.",
    },
]

IMPROVE_RESUME_PROMPTS = {
    "nudge": IMPROVE_RESUME_PROMPT_NUDGE,
    "keywords": IMPROVE_RESUME_PROMPT_KEYWORDS,
    "full": IMPROVE_RESUME_PROMPT_FULL,
}

DEFAULT_IMPROVE_PROMPT_ID = "keywords"

# Backward-compatible alias
IMPROVE_RESUME_PROMPT = IMPROVE_RESUME_PROMPT_FULL

COVER_LETTER_PROMPT = """Write a brief cover letter for this job application.

IMPORTANT: Write in {output_language}.

Job Description:
{job_description}

Candidate Resume (JSON):
{resume_data}

Requirements:
- 100-150 words maximum
- 3-4 short paragraphs
- Opening: Reference ONE specific thing from the job description (product, tech stack, or problem they're solving) - not generic excitement about "the role"
- Middle: Pick 1-2 qualifications from resume that DIRECTLY match stated requirements, and reframe them in the job's language/terminology where the candidate's proven experience supports it (e.g., if the resume shows "built automated data pipelines" and the job says "ETL," describe that real work as ETL) - prioritize relevance over impressiveness
- Closing: Simple availability to discuss, no desperate enthusiasm
- If resume shows career transition, frame the pivot as intentional and relevant
- Extract company name from job description - do not use placeholders
- Do NOT invent information not in the resume
- Tone: Confident peer, not eager applicant
- Do NOT use em dash ("—") anywhere in the writing/output, even if it exists, remove it

Output plain text only. No JSON, no markdown formatting."""

OUTREACH_MESSAGE_PROMPT = """Generate a cold outreach message for LinkedIn or email about this job opportunity.

IMPORTANT: Write in {output_language}.

Job Description:
{job_description}

Candidate Resume (JSON):
{resume_data}

Guidelines:
- 70-100 words maximum (shorter than a cover letter)
- First sentence: Reference specific detail from job description (team, product, technical challenge) - never open with "I'm reaching out" or "I saw your posting"
- One sentence on strongest matching qualification with a concrete metric if available
- End with low-friction ask: "Worth a quick chat?" not "I'd love the opportunity to discuss"
- Tone: How you'd message a former colleague, not a stranger
- Do NOT include placeholder brackets
- Do NOT use phrases like "excited about" or "passionate about"
- Do NOT use em dash ("—") anywhere in the writing/output, even if it exists, remove it

Output plain text only. No JSON, no markdown formatting."""

GENERATE_TITLE_PROMPT = """Extract the job title and company name from this job description.

IMPORTANT: Write in {output_language}.

Job Description:
{job_description}

Rules:
- Format: "Role @ Company" (e.g., "Senior Frontend Engineer @ Stripe")
- If the company name is not found, return just the role (e.g., "Senior Frontend Engineer")
- Maximum 60 characters
- Use the most specific role title mentioned
- Do not add any other text, quotes, or formatting

Output the title only, nothing else."""

# Alias for backward compatibility
RESUME_SCHEMA = RESUME_SCHEMA_EXAMPLE

# Diff-based improvement: outputs targeted changes instead of full resume

DIFF_STRATEGY_INSTRUCTIONS = {
    "nudge": "Rephrase existing content only using JD terminology. Do not add new bullet points, skills, or sections. Touch minimum words.",
    "keywords": "Completely rewrite the summary targeting this role, reorder and trim skills keeping only JD-relevant ones, rewrite ALL experience/project bullets that relate to JD requirements using the JD's exact terminology, reorder sections by relevance.",
    "full": "Completely rewrite the summary for the role, reorder all sections by relevance, rewrite every relevant bullet using JD language, add 1 new bullet per role to expand existing work only, trim irrelevant skills.",
}

SKILL_TARGET_PLAN_PROMPT = """Build a concise skill target plan for tailoring this resume to the job.

Return ONLY a JSON object. Do not rewrite the resume.

Rules:
1. Prefer required and preferred JD skills.
2. Include existing resume skills that are highly relevant to the JD.
3. You may include JD skills that are missing from the resume skills list.
4. Do not include skills unrelated to the JD.
5. Do not include certifications.
6. Generate reasons in {output_language}.

Existing resume skills:
{existing_skills}

JD keywords and skills:
{job_keywords}

Job Description:
{job_description}

Resume JSON:
{original_resume}

Output this exact JSON format:
{{
  "target_skills": [
    {{
      "skill": "skill name",
      "reason": "why this skill should be emphasized"
    }}
  ],
  "strategy_notes": "brief notes for the next editing pass"
}}"""

GENERATE_TAILORED_PROJECT_PROMPT = """Generate a relevant personal project based on the job description and the candidate's existing skills/experience. Output ONLY the JSON object, no other text.

IMPORTANT: Generate ALL text content in {output_language}.

CRITICAL RULES (MUST NOT VIOLATE):
1. ONLY use skills, tools, and technologies explicitly mentioned in the candidate's resume
2. DO NOT invent any metrics or achievements that are not supported by the candidate's existing experience
3. The project should be a plausible side project that demonstrates skills relevant to the JD
4. The project should fit naturally with the candidate's existing background
5. Do NOT invent new skills or technologies the candidate hasn't used
6. Keep the project realistic and achievable, not overly complex
7. Do NOT use em dash characters
8. This project will be added to the resume alongside existing projects — make it distinct and complementary

Candidate's existing resume data:
{resume_data}

Job description:
{job_description}

Extracted JD keywords and skills:
{job_keywords}

Output this exact JSON format:
{{
  "name": "Project name (5-8 words, professional and specific)",
  "role": "Your role in the project (e.g., Creator, Lead Developer)",
  "years": "Date range (e.g., 'Jan 2024 - Present')",
  "description": [
    "Bullet point 1: what was built and why it is relevant to the target role",
    "Bullet point 2: key technologies used (only from candidate's existing skills)",
    "Bullet point 3: outcome or impact (no fabricated metrics)"
  ]
}}"""

DIFF_IMPROVE_PROMPT = """Given this resume and job description, output a JSON object with targeted changes to better align the resume with the job.

RULES:
1. Only modify content; never change names, companies, dates, institutions, or degrees
2. Do not invent metrics or achievements not supported by the original resume text
3. Do not add new work entries, education entries, or project entries
4. {strategy_instruction}
5. Each replace change MUST include "original" copied EXACTLY from the resume — character-for-character. Use null only for "summary" path.
6. For each change, explain WHY it helps match the job description
7. Generate all new text in {output_language}
8. Do not use em dash characters in new text
9. SEMANTIC KEYWORD MAPPING — translate existing experience into JD terminology:
   - "Flask" used for APIs → rewrite as "developed Python-based RESTful APIs using Flask"
   - "MySQL/Firebase/Supabase" → rewrite as "SQL database design and management"
   - "AI services/AI APIs" → rewrite as "integrated AI/ML APIs and LLM-powered features"
   - "testing, debugging" → rewrite as "software testing, debugging, and quality assurance"
   - "deployment support" → rewrite as "deployment pipeline and application maintenance"
10. Preserve original capitalization for technical terms (REST, API, etc.)

PATHS you can target:
- "summary" — the resume summary (set "original": null)
- "workExperience[i].description[j]" — a specific bullet (i=entry index, j=bullet index, both 0-based)
- "workExperience[i].description" — append a new bullet (action: "append")
- "personalProjects[i].description[j]" — a specific project bullet (i=project index, j=bullet index, both 0-based)
- "personalProjects[i].description" — append a project bullet (action: "append")
- "education[i].description" — education description (replace only)
- "additional.technicalSkills" — reorder skills (action: "reorder"). Include JD-equivalent terms at front. Keep 12-15. Remove irrelevant skills.
- "additional.languages", "additional.certificationsTraining", "additional.awards" — reorder

Do NOT target: personalInfo, dates/years, company names, education institution/degree/years, customSections.

REQUIRED CHANGES — you MUST generate ALL of the following:

A) summary rewrite (always):
   Path: "summary", action: "replace", original: null
   Open with role title from JD. Include 5+ JD keywords. 2-3 sentences.

B) skills reorder (always):
   Path: "additional.technicalSkills", action: "reorder"
   Put JD-critical skills first. Add semantic equivalents. Remove irrelevant skills.

C) ALL work experience bullets (rewrite each one using JD terminology):
   Path: "workExperience[0].description[0]", action: "replace", original: "<EXACT text>"
   Path: "workExperience[0].description[1]", action: "replace", original: "<EXACT text>"
   ...continue for all bullets

D) ALL project bullets (rewrite EVERY bullet of EVERY project using JD terminology):
   Path: "personalProjects[0].description[0]", action: "replace", original: "<EXACT text>"
   Path: "personalProjects[0].description[1]", action: "replace", original: "<EXACT text>"
   Path: "personalProjects[1].description[0]", action: "replace", original: "<EXACT text>"
   Path: "personalProjects[1].description[1]", action: "replace", original: "<EXACT text>"
   Path: "personalProjects[2].description[0]", action: "replace", original: "<EXACT text>"
   Path: "personalProjects[2].description[1]", action: "replace", original: "<EXACT text>"
   For EACH project bullet: rewrite using JD vocabulary. Map existing tech to JD terms.

Keywords to emphasize:
{job_keywords}

Verified skill targets:
{skill_targets}

Job Description:
{job_description}

Original Resume (use exact bullet text for "original" fields):
{original_resume}

Output ONLY this JSON format:
{{
  "changes": [
    {{
      "path": "summary",
      "action": "replace",
      "original": null,
      "value": "Python Developer with hands-on experience building REST APIs and web applications using Python, Flask, and SQL databases...",
      "reason": "targets JD role and includes all critical keywords"
    }},
    {{
      "path": "workExperience[0].description[0]",
      "action": "replace",
      "original": "EXACT text copied from resume",
      "value": "Developed Python-based REST APIs and backend services using Flask for web applications...",
      "reason": "uses JD REST API terminology"
    }},
    {{
      "path": "personalProjects[0].description[0]",
      "action": "replace",
      "original": "EXACT text copied from resume",
      "value": "Built Python-based REST API backend with Flask and SQL database integration for real-time data processing",
      "reason": "maps project to JD Python/REST API/SQL requirements"
    }},
    {{
      "path": "additional.technicalSkills",
      "action": "reorder",
      "original": null,
      "value": ["Python", "REST APIs", "Flask", "SQL Databases", "JavaScript", "React.js", "Git", "Node.js", "TypeScript"],
      "reason": "JD-critical skills first, removed irrelevant skills"
    }}
  ],
  "strategy_notes": "tailored for JD role"
}}"""
