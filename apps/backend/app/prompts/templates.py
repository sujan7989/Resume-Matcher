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
   - Open with the candidate's most relevant skill/title matching the JD
   - Include 4-6 exact keywords from the JD that the resume already supports
   - Connect the candidate's background directly to the role's needs
   - Make it sound like a professional who is perfect for this role
   - 2-3 sentences maximum

2. TECHNICAL SKILLS: Restructure the skills section:
   - Move JD-critical skills to the FRONT of the list
   - Keep top 12-15 most relevant skills only
   - Remove skills with zero relevance to this specific JD
   - Keep foundation/transferable skills even if not in JD

3. EXPERIENCE: For EVERY work experience entry:
   - Reorder so most JD-relevant role appears first
   - For EACH bullet that relates to a JD requirement: rewrite using the EXACT terminology from the JD
   - Strengthen weak bullets: if the bullet describes something relevant but vaguely, make it more specific
   - Add quantification ONLY if the original already has numbers/metrics to work with
   - Do NOT add new bullet points

4. PROJECTS: For EVERY project:
   - Reorder by JD relevance
   - Rewrite each project description to use JD technology names where the project already uses them
   - Make sure the tech stack in project descriptions matches JD terminology exactly

5. Do NOT add new bullet points, new skills, or fabricate metrics.
6. Keep all dates, company names, institutions exactly as in the original.
7. Do NOT use em dash anywhere.

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
1. SUMMARY: Completely rewrite to target this specific role. Open with the job title or domain. Include 5+ JD keywords the resume supports. Connect the candidate's background directly to the role's requirements.
2. TECHNICAL SKILLS: Reorder so JD-critical skills appear first. Add any JD skill already demonstrated in experience but missing from the skills list.
3. EXPERIENCE: Reorder roles by JD relevance. Rewrite every bullet that relates to a JD keyword using the JD's terminology. Add 1 new bullet per role ONLY to expand on existing work (not to invent new work).
4. PROJECTS: Reorder by JD relevance. Rewrite project descriptions to use JD terminology where the project already demonstrates that skill.
5. CERTIFICATIONS/AWARDS: Keep all. Reorder to put JD-relevant ones first.
6. Keep all dates, company names, institutions exactly as in original.
7. Do NOT fabricate metrics, tools, or experience that doesn't exist.
8. Do NOT use em dash anywhere.

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
5. Each change MUST include the original text (copied exactly) so it can be verified
6. For each change, explain WHY it helps match the job description
7. Generate all new text in {output_language}
8. Do not use em dash characters
9. Keep changes minimal and targeted; do not rewrite content that already aligns well
10. Exception to rule 2: you may add a skill only if it appears in the verified skill targets below
11. By DEFAULT, scan the summary and every work, project, and education description for content that already demonstrates a job-description keyword or skill, and reframe that text using the job description's terminology where it is not already phrased that way (per rule 9, leave content that already aligns well), while preserving the candidate's actual accomplishment. Do NOT add new work, metrics, or responsibilities; only restate existing content in the JD's language, and verify every reframe stays factually accurate.
12. Preserve original capitalization, especially for proper nouns, technical terms (e.g., REST, API, AWS), and acronyms. Do not change the casing of words that were capitalized in the original.

PATHS you can target:
- "summary" — the resume summary text (for replace action, you MAY set "original": null since the summary is always replaced entirely)
- "workExperience[i].description[j]" — a specific bullet (i = entry index, j = bullet index)
- "workExperience[i].description" — append a new bullet (action: "append")
- "personalProjects[i].description[j]" — a specific project bullet
- "personalProjects[i].description" — append a new project bullet (action: "append")
- "education[i].description" — the education entry's description text (replace only; it is a single string, not a list)
- "additional.technicalSkills" — reorder skills by relevance (action: "reorder"). When reordering, TRIM the list to the 15 most JD-relevant skills. Remove skills with zero relevance to this specific role (e.g., remove "SAP NetWeaver" for a Python role, remove "Phishing Detection" for a backend role). Keep core/foundation skills even if not in JD. The value array must contain ONLY the kept skills in relevance order.
- "additional.languages" — reorder the languages list (action: "reorder")
- "additional.certificationsTraining" — reorder the certifications list (action: "reorder")
- "additional.awards" — reorder the awards list (action: "reorder")

Do NOT target: personalInfo, dates/years, company names, education degree/institution/years, customSections.

REWRITING QUALITY RULES — these make the difference between keyword stuffing and true tailoring:
For "summary": COMPLETELY rewrite it. Target this specific role/company. Open with the candidate's most relevant title/skill.
  Include 4-6 exact JD keywords the resume supports. Sound like a professional built for this role.
For experience/project bullets: When a bullet relates to a JD requirement, rewrite it using the JD's EXACT terminology.
  BAD: "Tested web applications" + JD wants "QA testing, test automation"
  GOOD: "Performed QA testing and developed test automation scripts for web applications"
  BAD: "Built backend services" + JD wants "REST APIs, microservices"
  GOOD: "Developed REST API microservices handling authentication and data processing"
Generate at minimum: 1 summary rewrite + technicalSkills reorder + 3-5 experience/project bullet rewrites.
If the resume has relevant experience, ensure the score-impacting sections get substantive rewrites.

Keywords to emphasize (only if already supported by resume content):
{job_keywords}

Verified skill targets:
{skill_targets}

Job Description:
{job_description}

Original Resume:
{original_resume}

Output this exact JSON format, nothing else:
{{
  "changes": [
    {{
      "path": "workExperience[0].description[1]",
      "action": "replace",
      "original": "the exact original text at this path",
      "value": "the improved text",
      "reason": "why this change helps"
    }},
    {{
      "path": "summary",
      "action": "replace",
      "original": "the current summary text",
      "value": "the improved summary",
      "reason": "why this change helps"
    }},
    {{
      "path": "additional.technicalSkills",
      "action": "reorder",
      "original": null,
      "value": ["Python", "FastAPI", "PostgreSQL", "REST APIs", "Docker", "JavaScript", "Git", "SQL", "Linux", "Flask"],
      "reason": "trimmed to top 10 JD-relevant skills, removed irrelevant security/SAP skills"
    }},
    {{
      "path": "additional.technicalSkills",
      "action": "add_skill",
      "original": null,
      "value": "verified skill target missing from the skills list",
      "reason": "added verified JD skill for review"
    }}
  ],
  "strategy_notes": "brief summary of the tailoring approach"
}}"""
