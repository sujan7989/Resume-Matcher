# Resume Matcher — Complete Project Handover Document

> Generated: 2026-07-15  
> Based on: Full codebase analysis (not memory)  
> Version: 1.2.0 (backend + frontend both at 1.2.0)

---

## 1. Project Purpose and End Goal

Resume Matcher is a **self-hosted, AI-powered career tools platform**. Its end goal is to give job seekers everything they need to go from raw resume to hired — in one tool:

1. Upload a master resume (PDF/DOCX) → AI parses it to structured JSON
2. Paste or fetch a job description → AI extracts keywords and requirements
3. Tailor the resume to the JD with three strategies (light nudge / keyword enhance / full tailor)
4. Score the tailored resume against the JD via ATS analysis (0–100 with five sub-scores)
5. Enrich thin experience bullets with AI-guided questions
6. Generate cover letter, LinkedIn outreach message, and resume title
7. Build a resume from scratch via Resume Wizard (Q&A flow)
8. Export to PDF (Playwright + HTML or fpdf2 fallback)
9. Track applications on a Kanban board (7 columns: saved → rejected)
10. Manage LLM provider/API keys from the Settings UI (no restart needed)

The product is provider-agnostic: OpenAI, Anthropic, Gemini, OpenRouter, DeepSeek, Groq, Ollama, and any OpenAI-compatible local server all work.

---

## 2. Current Completion Percentage

**~88% complete.** The core feature set is fully implemented and deployed. What remains is polish, edge cases, and some unfinished frontend flows.

| Area | Status |
|------|--------|
| Backend API (all routers) | ✅ Complete |
| Database (SQLite + Postgres) | ✅ Complete |
| Auth / API key management | ✅ Complete |
| Resume upload + parsing | ✅ Complete |
| Resume tailoring (3 strategies) | ✅ Complete |
| ATS scoring + analysis | ✅ Complete |
| Cover letter / outreach generation | ✅ Complete |
| PDF export (Playwright + fpdf2) | ✅ Complete |
| Resume Builder (manual edit) | ✅ Complete |
| Enrichment wizard | ✅ Complete |
| Application Tracker (Kanban) | ✅ Complete |
| Resume Wizard (scratch build) | ✅ Complete |
| i18n (en/es/zh/ja/pt-BR) | ✅ Complete |
| Dark/light theme | ✅ Complete |
| Deployment (Docker, Render, Vercel) | ✅ Complete |
| Test coverage | ⚠️ Frontend has tests, backend test suite exists but limited |
| Error boundaries / edge cases | ⚠️ Some gaps (see Known Bugs) |
| Performance optimization | ⚠️ Some LLM timeout issues on slow providers |

---

## 3. Complete Folder Structure

```
resume-matcher-deploy/
├── apps/
│   ├── backend/                    # Python FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py             # FastAPI app entry point, lifespan, CORS, router registration
│   │   │   ├── config.py           # Pydantic Settings (env vars), API key helpers, legacy migration
│   │   │   ├── config_cache.py     # TTL cache for config.json reads (avoid disk I/O on hot paths)
│   │   │   ├── crypto.py           # Fernet encryption for API keys at rest (data/.secret_key)
│   │   │   ├── database.py         # SQLAlchemy async facade — ALL DB operations go through here
│   │   │   ├── db_engine.py        # SQLAlchemy engine factory (SQLite vs PostgreSQL detection)
│   │   │   ├── models.py           # SQLAlchemy ORM models: Resume, Job, Improvement, Application, ApiKey
│   │   │   ├── llm.py              # LiteLLM wrapper, Router, health check, complete(), complete_json()
│   │   │   ├── pdf.py              # PDF rendering: Playwright (primary) + fpdf2 (fallback)
│   │   │   ├── __init__.py         # Version string (__version__ = "1.2.0")
│   │   │   ├── .deploy-ts          # Deployment timestamp marker
│   │   │   ├── prompts/
│   │   │   │   ├── __init__.py     # Re-exports IMPROVE_PROMPT_OPTIONS, DEFAULT_IMPROVE_PROMPT_ID
│   │   │   │   ├── ats_analysis.py # All ATS-related prompts (scoring, suggest/replace/analyze projects)
│   │   │   │   ├── enrichment.py   # Enrichment + regenerate prompts (analyze, enhance, regenerate)
│   │   │   │   ├── refinement.py   # AI phrase blacklist, keyword injection, validation polish prompts
│   │   │   │   ├── resume_wizard.py# Resume wizard prompt (scratch build from Q&A)
│   │   │   │   └── templates.py    # Core prompts: PARSE_RESUME, EXTRACT_KEYWORDS, IMPROVE_RESUME (3 variants)
│   │   │   │                       # COVER_LETTER, OUTREACH, GENERATE_TITLE, DIFF_IMPROVE, SKILL_TARGET_PLAN
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py     # Exports all router objects
│   │   │   │   ├── ats.py          # /ats/* — ATS analysis + project optimizer endpoints
│   │   │   │   ├── applications.py # /applications/* — Kanban tracker CRUD
│   │   │   │   ├── config.py       # /config/* — LLM config, features, language, prompts, API keys, reset
│   │   │   │   ├── enrichment.py   # /enrichment/* — analyze, enhance, apply, regenerate, apply-regenerated
│   │   │   │   ├── health.py       # /health, /status, /db-test
│   │   │   │   ├── jobs.py         # /jobs/* — upload JD, get JD, extract-from-url
│   │   │   │   ├── resumes.py      # /resumes/* — upload, get, list, improve/preview, improve/confirm, PDF, etc.
│   │   │   │   └── resume_wizard.py# /resume-wizard/* — scratch build via Q&A
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py     # Re-exports all public schemas
│   │   │   │   ├── applications.py # Application, ApplicationUpdate, BulkStatusUpdate, etc.
│   │   │   │   ├── ats.py          # ATSAnalysisResult, ATSScore, SkillGap, InterviewQuestion, etc.
│   │   │   │   ├── enrichment.py   # EnrichmentItem, EnhancementPreview, RegenerateRequest, etc.
│   │   │   │   ├── models.py       # ResumeData, ResumeSchema, JobUploadRequest, all Pydantic models
│   │   │   │   ├── refinement.py   # RefinementConfig schema
│   │   │   │   └── resume_wizard.py# ResumeWizardRequest/Response schemas
│   │   │   ├── services/
│   │   │   │   ├── ats_analyzer.py # ATS analysis service: calls LLM, parses result into typed schema
│   │   │   │   ├── cover_letter.py # generate_cover_letter(), generate_outreach_message(), generate_resume_title()
│   │   │   │   ├── improver.py     # Core tailoring logic: diff strategy, skill target plan, apply_diffs(), etc.
│   │   │   │   ├── parser.py       # parse_document() → markdown, parse_resume_to_json() → structured JSON
│   │   │   │   ├── refiner.py      # Multi-pass refiner: keyword injection, AI phrase stripping, polish
│   │   │   │   └── resume_wizard.py# Q&A-based resume builder service
│   │   │   └── scripts/
│   │   │       └── migrate_tinydb_to_sqlite.py  # One-time migration from legacy TinyDB to SQLite
│   │   ├── data/                   # Runtime data directory (gitignored)
│   │   │   ├── resume_matcher.db   # SQLite database (primary store when DATABASE_URL is unset)
│   │   │   ├── config.json         # Non-secret LLM config (provider, model, features, language)
│   │   │   └── .secret_key         # Fernet encryption key (auto-generated, chmod 600, gitignored)
│   │   ├── tests/                  # pytest test suite
│   │   ├── pyproject.toml          # Project metadata + pinned dependencies
│   │   ├── .env                    # Local secrets (gitignored)
│   │   ├── .env.example            # Template for environment variables
│   │   └── start.sh                # Production start script: uvicorn on $PORT (default 10000)
│   └── frontend/                   # Next.js 16 + React 19 + Tailwind 4 frontend
│       ├── app/
│       │   ├── layout.tsx          # Root layout (ThemeProvider, LanguageContext, StatusCache)
│       │   ├── (default)/          # Main app routes with shared sidebar layout
│       │   │   ├── layout.tsx      # App shell with navigation sidebar
│       │   │   ├── page.tsx        # Home/landing page
│       │   │   ├── dashboard/      # Resume upload + master resume management
│       │   │   ├── builder/        # Resume builder (manual JSON editor + live preview)
│       │   │   ├── tailor/         # Resume tailoring flow (JD input → preview → confirm)
│       │   │   ├── resumes/        # Resume list and individual resume views
│       │   │   ├── tracker/        # Kanban application tracker
│       │   │   ├── resume-wizard/  # Q&A based resume creation from scratch
│       │   │   └── settings/       # LLM config, API keys, features, language, prompts
│       │   ├── print/              # Print/PDF rendering routes (no nav, clean layout)
│       │   │   ├── resumes/        # Resume print page (Playwright navigates here for PDF)
│       │   │   └── cover-letter/   # Cover letter print page
│       │   └── api/
│       │       └── keep-alive/     # Ping endpoint to prevent Render free-tier sleep
│       ├── components/
│       │   ├── ats/                # ATS score panel, job URL input, project optimizer
│       │   ├── builder/            # Resume builder: form, cover letter editor, diff view, regenerate wizard
│       │   ├── common/             # ErrorBoundary, ThemeProvider, ResumePreviewerContext
│       │   ├── dashboard/          # Master resume choice dialog, upload dialog, resume card
│       │   ├── enrichment/         # Enrichment wizard modal (analyze → questions → preview → apply)
│       │   ├── preview/            # Paginated resume preview with page container
│       │   ├── resume/             # 7 resume templates: single, two-column, modern, latex, clean, vivid, modern-two-column
│       │   ├── resume-wizard/      # Q&A wizard: question card, live preview, wizard page
│       │   ├── settings/           # API key menu
│       │   ├── tailor/             # Diff preview modal for tailoring review
│       │   ├── tracker/            # Kanban board, columns, cards, bulk actions, card detail modal
│       │   └── ui/                 # Primitive UI components (Button, Card, Dialog, Input, etc.)
│       ├── lib/
│       │   ├── api/                # All API client functions (resume.ts, jobs.ts, ats.ts, etc.)
│       │   ├── context/            # LanguageContext, StatusCache (global state)
│       │   ├── i18n/               # i18n utils, locale detection, translation loader
│       │   ├── types/              # TypeScript type definitions
│       │   └── utils/              # download.ts, html-sanitizer.ts, keyword-matcher.ts, section-helpers.ts
│       ├── messages/               # i18n JSON files: en.json, es.json, zh.json, ja.json, pt-BR.json
│       ├── hooks/                  # Custom React hooks (use-enrichment-wizard, use-regenerate-wizard, use-file-upload)
│       ├── next.config.ts          # Next.js config: API proxy to backend, proxyTimeout, tree-shaking
│       ├── package.json            # Frontend dependencies (pinned)
│       └── tsconfig.json           # TypeScript config (@/* path alias)
├── .github/
│   └── workflows/
│       ├── docker-publish.yml      # Docker build + push to GitHub Container Registry
│       └── render-deploy.yml       # Render.com deployment trigger
└── HANDOVER.md                     # This document
```

---

## 4. Frontend Architecture and Complete User Flow

### Tech Stack
- **Next.js 16.2.6** (App Router, standalone output)
- **React 19.2.4**
- **Tailwind CSS 4** (no config file — uses CSS variables)
- **@dnd-kit** for Kanban drag-and-drop
- **@tiptap/react** for rich text editing (cover letter, outreach)
- **lucide-react** for icons
- **clsx + tailwind-merge** for conditional classes
- **isomorphic-dompurify** for HTML sanitization in preview

### API Proxy
All `/api/*` calls from the frontend are proxied by `next.config.ts` rewrites to `BACKEND_ORIGIN`. In production (Vercel) `BACKEND_ORIGIN` must be set to the Render backend URL. Locally it defaults to `https://resume-matcher-6kv2.onrender.com` which means **you must override it for local dev**.

### Complete User Flow

```
1. DASHBOARD (/dashboard)
   └── Upload resume (PDF/DOCX, max 4MB)
       ├── Backend parses to markdown + structured JSON
       ├── First upload becomes "master" resume (atomic lock)
       └── Resume card shown with processing_status indicator

2. BUILDER (/builder?resumeId=<id>)
   ├── Left panel: form editor (personal info, experience, education, projects, skills, etc.)
   │   ├── Drag-and-drop section reordering (@dnd-kit)
   │   ├── Rich text editor for cover letter/outreach (Tiptap)
   │   ├── Template selector (7 templates)
   │   └── AI Regenerate: select items → give instruction → LLM rewrites → preview diff → apply
   └── Right panel: live resume preview (paginated, matches print output)
       └── Download PDF button → calls /api/v1/resumes/pdf

3. TAILOR (/tailor)
   ├── Step 1: Select resume + paste/fetch JD
   │   └── "Fetch from URL" calls /api/v1/jobs/extract-from-url
   ├── Step 2: Choose tailoring strategy (Light Nudge / Keyword Enhance / Full Tailor)
   │   └── Calls /api/v1/resumes/improve/preview (LLM tailoring, no DB write yet)
   ├── Step 3: Review diff preview modal (shows added/changed/removed per field)
   └── Step 4: Confirm → /api/v1/resumes/improve/confirm (saves tailored resume + auto-creates tracker card)

4. ATS ANALYSIS (inside /builder or /tailor)
   ├── POST /api/v1/ats/analyze (or GET /api/v1/ats/analyze/{resume_id}/{job_id})
   │   Returns: overall score, 5-dimension breakdown, keyword analysis, skill gap, interview Qs, recommendations
   ├── POST /api/v1/ats/analyze-projects → ranks all projects by JD relevance
   ├── POST /api/v1/ats/suggest-project → suggest one new project to build
   └── POST /api/v1/ats/replace-project → generate replacement for a weak project

5. ENRICHMENT (inside /builder)
   ├── POST /api/v1/enrichment/analyze/{resume_id} → identify weak bullets, generate max 6 questions
   ├── User answers questions in wizard modal
   ├── POST /api/v1/enrichment/enhance → generate new bullet points from answers
   └── POST /api/v1/enrichment/apply/{resume_id} → append new bullets to existing description

6. RESUME WIZARD (/resume-wizard)
   └── Q&A flow (LLM generates questions → user answers → LLM builds resume JSON)

7. TRACKER (/tracker)
   ├── Kanban board with 7 columns: saved, applied, no_response, response, interview, accepted, rejected
   ├── Cards auto-created after tailoring confirm
   ├── Manual add: paste JD → LLM extracts company/role → create card
   ├── Drag-and-drop reorder within + between columns
   └── Card detail modal: shows JD, applied resume preview, notes

8. SETTINGS (/settings)
   ├── LLM config: provider, model, API key, API base URL, reasoning effort
   ├── Per-provider API keys (openai, anthropic, google, openrouter, deepseek, groq, openai_compatible, ollama)
   ├── Feature flags: cover letter, outreach message
   ├── Language: UI language + content language (en/es/zh/ja/pt)
   ├── Custom prompts: cover letter, outreach message
   └── System status: LLM health + DB stats
```

### Resume Templates
7 templates rendered as React components in `components/resume/`:
- `swiss-single` (default, ATS-friendly, single column)
- `swiss-two-column`
- `modern` (blue header, single column)
- `modern-two-column`
- `latex` (serif font, academic style)
- `clean` (minimalist gray)
- `vivid` (purple accent)

### Print Route
`/print/resumes/[resumeId]` renders the resume without navigation for Playwright to screenshot into PDF. The backend navigates to `FRONTEND_BASE_URL/print/resumes/{id}` via Playwright, waits for `networkidle`, then calls `page.pdf()`.

---

## 5. Backend Architecture and Request Flow

### Stack
- **FastAPI 0.128.4** — async, ASGI
- **uvicorn 0.40.0** — ASGI server
- **SQLAlchemy 2.0.36** (async) — data layer
- **aiosqlite 0.20.0** — async SQLite driver
- **LiteLLM 1.86.2** — multi-provider LLM abstraction
- **Pydantic 2.12.5 + pydantic-settings** — validation + config
- **Playwright 1.58.0** — headless Chromium for PDF
- **markitdown + pdfminer.six** — document parsing
- **cryptography (Fernet)** — API key encryption

### Request Flow (Example: Resume Tailoring)

```
Browser
  │
  ▼ POST /api/v1/resumes/improve/preview
Next.js proxy (next.config.ts rewrite)
  │
  ▼ FastAPI router (routers/resumes.py)
  │  _improve_preview_flow()
  ├── db.get_resume(resume_id)          # SQLite async read
  ├── db.get_job(job_id)                # SQLite async read
  ├── extract_job_keywords(job_content) # LLM call → {company, role, skills, keywords, ...}
  │   └── db.update_job(job_id, ...)    # cache keywords + hash
  ├── generate_skill_target_plan(...)   # LLM call → {target_skills, strategy_notes}
  ├── generate_resume_diffs(...)        # LLM call → {changes: [{path, action, original, value}]}
  ├── apply_diffs(original_data, diffs) # pure function, applies changes to resume JSON
  ├── _preserve_personal_info(...)      # safety: always copy original personalInfo
  ├── _preserve_original_skills(...)    # safety: never drop skills/certs/languages/awards
  ├── _restore_original_dates(...)      # safety: restore month-precision dates LLM stripped
  ├── _protect_custom_sections(...)     # safety: prevent LLM hallucination in customSections
  ├── _hash_improved_data(...)          # SHA-256 hash of canonical JSON (for confirm validation)
  ├── db.update_job("preview_hash", hash) # store hash so confirm can verify
  └── asyncio.gather(                   # parallel: cover letter + outreach + title
        generate_cover_letter(),
        generate_outreach_message(),
        generate_resume_title()
      )
  │
  ▼ ImproveResumeResponse (resume_preview + hash, no DB write yet)
  
Browser submits POST /api/v1/resumes/improve/confirm
  │
  ├── Verify preview_hash matches stored hash (anti-tampering)
  ├── _validate_confirm_payload()       # personal info must not have changed
  ├── db.create_resume(tailored, is_master=False, parent_id=master_id)
  ├── db.create_improvement(...)        # audit record
  └── _auto_create_tracker_application(...)  # best-effort Kanban card
```

### LLM Call Flow

```
app/llm.py
  complete_json(prompt, config, max_tokens, schema_type)
    │
    ├── get_router(config)              # cached LiteLLM Router (rebuilt on config change)
    ├── get_model_name(config)          # provider prefix: "gemini/...", "ollama_chat/...", etc.
    ├── _supports_json_mode(model_name) # query LiteLLM registry
    ├── router.acompletion(...)         # with retry policy (3 retries, rate-limit/timeout only)
    └── _extract_choice_text(response) # handles content + reasoning_content + thinking
```

### Database Engine

Two engines back one file:
- **Async engine** (`aiosqlite`) for all document tables + applications
- **Sync engine** for `api_keys` table (read on LLM hot path without `await`)

The `Database` class is a singleton (`db` in `app/database.py`). All methods return plain dicts (never ORM objects) to preserve TinyDB migration semantics.

### Startup Sequence (lifespan)

1. Create `data/` directory
2. `db._ensure_initialized()` — create all SQLAlchemy tables
3. `migrate_tinydb_to_sqlite()` — one-time migration if `data/database.json` exists
4. `migrate_legacy_keys()` — fold old plaintext API keys from config.json into encrypted store
5. Clean stale encrypted API keys (keys encrypted with a different secret after redeploy)
6. Yield (app serving)
7. On shutdown: close Playwright browser, close DB engines

---

## 6. Database Schema and Relationships

Primary store: **SQLite** (`data/resume_matcher.db`) or **PostgreSQL** (when `DATABASE_URL` is set).

### Tables

#### `resumes`
| Column | Type | Notes |
|--------|------|-------|
| `resume_id` | String PK | UUID |
| `content` | Text | Markdown (upload) or JSON string (after builder save) |
| `content_type` | String | `"md"` or `"json"` |
| `filename` | String? | Original uploaded filename |
| `is_master` | Boolean | Only one master allowed (enforced by asyncio.Lock) |
| `parent_id` | String? | Points to master resume this was tailored from |
| `processed_data` | JSON | Parsed structured resume (see ResumeData schema) |
| `processing_status` | String | `pending` / `processing` / `ready` / `failed` |
| `cover_letter` | Text? | AI-generated cover letter |
| `outreach_message` | Text? | AI-generated LinkedIn/email message |
| `title` | String? | AI-generated title like "Senior Engineer @ Stripe" |
| `original_markdown` | Text? | Preserved original markdown (for date reference) |
| `created_at` | String | ISO-8601 UTC |
| `updated_at` | String | ISO-8601 UTC |

Index: `ux_resumes_single_master` on `is_master` (fast master lookup).

#### `jobs`
| Column | Type | Notes |
|--------|------|-------|
| `job_id` | String PK | UUID |
| `content` | Text | Raw JD text |
| `resume_id` | String? | Resume it was uploaded with |
| `created_at` | String | ISO-8601 UTC |
| `metadata_json` | JSON | Dynamic fields: `job_keywords`, `job_keywords_hash`, `preview_hash`, `preview_hashes`, `company`, `role` |

The facade flattens `metadata_json` to top-level keys on read, making dynamic pipeline fields transparent to call sites.

#### `improvements`
| Column | Type | Notes |
|--------|------|-------|
| `request_id` | String PK | UUID |
| `original_resume_id` | String | Source resume |
| `tailored_resume_id` | String | Result resume (indexed) |
| `job_id` | String | Associated job |
| `improvements` | JSON | List of diffs that were applied |
| `created_at` | String | ISO-8601 UTC |

#### `applications`
| Column | Type | Notes |
|--------|------|-------|
| `application_id` | String PK | UUID |
| `job_id` | String | Indexed |
| `resume_id` | String | Applied/tailored resume, indexed |
| `master_resume_id` | String? | Base resume for "stack" grouping |
| `status` | String | One of 7 statuses, indexed |
| `company` | String? | Extracted from JD |
| `role` | String? | Extracted from JD |
| `applied_at` | String? | ISO-8601 UTC |
| `notes` | Text? | User notes |
| `position` | Integer | Ordering within a column (0-based) |
| `created_at` | String | ISO-8601 UTC |
| `updated_at` | String | ISO-8601 UTC |

Unique constraint: `(job_id, resume_id)` — deduplicates concurrent auto-creates.

#### `api_keys`
| Column | Type | Notes |
|--------|------|-------|
| `provider` | String PK | Key-store name: `openai`, `anthropic`, `google`, `openrouter`, `deepseek`, `groq`, `openai_compatible`, `ollama` |
| `ciphertext` | Text | Fernet-encrypted plaintext key |
| `updated_at` | String | ISO-8601 UTC |

Note: `google` is the key-store name for the `gemini` LLM provider.

### Relationships (logical, no FK constraints in SQLite)
```
resumes.parent_id → resumes.resume_id   (master → tailored)
applications.job_id → jobs.job_id
applications.resume_id → resumes.resume_id
applications.master_resume_id → resumes.resume_id
improvements.original_resume_id → resumes.resume_id
improvements.tailored_resume_id → resumes.resume_id
improvements.job_id → jobs.job_id
```

### ResumeData JSON Structure (processed_data field)
```json
{
  "personalInfo": { "name", "title", "email", "phone", "location", "website", "linkedin", "github" },
  "summary": "string",
  "workExperience": [{ "id", "title", "company", "location", "years", "description": [] }],
  "education": [{ "id", "institution", "degree", "years", "description" }],
  "personalProjects": [{ "id", "name", "role", "years", "github", "website", "description": [] }],
  "additional": {
    "technicalSkills": [],
    "languages": [],
    "certificationsTraining": [],
    "awards": []
  },
  "customSections": {
    "<key>": {
      "sectionType": "text" | "itemList" | "stringList",
      "text": "...",          // for sectionType: text
      "items": [...]          // for sectionType: itemList
    }
  }
}
```

---

## 7. Authentication Flow

**There is no user authentication.** This is an intentional design decision: the tool is single-user, self-hosted.

The only "auth" is for the LLM API keys, which are:
1. Stored encrypted with Fernet symmetric encryption (`data/.secret_key`)
2. Never written to `config.json` (only non-secret config is there)
3. Read from the encrypted SQLite `api_keys` table at call time
4. Decrypted in memory only when making an LLM call

**Security note:** The `/config/reset` endpoint requires `confirm=RESET_ALL_DATA` in the body, and `/config/api-keys` (DELETE all) requires `confirm=CLEAR_ALL_KEYS` query param. These are the only "auth" measures on destructive endpoints.

**CORS** is configured via `CORS_ORIGINS` env var (default: `localhost:3000`). `FRONTEND_BASE_URL` is also added to the allowed origins automatically.

If you deploy this for multiple users, you must add authentication (e.g., OAuth, session middleware) before all API routes. The current design assumes one trusted user per instance.

---

## 8. Resume Parsing Pipeline

```
File upload (PDF/DOCX/DOC)
  │
  ├── Validate: content_type must be in ALLOWED_TYPES
  ├── Validate: size ≤ 4MB
  ├── Validate: not empty
  │
  ▼ parse_document(content: bytes, filename: str) → markdown: str
  │   app/services/parser.py
  │   ├── If .pdf: use pdfminer.six to extract text → plain string
  │   ├── If .docx/.doc: use markitdown[docx] → markdown string
  │   └── Strips excessive whitespace
  │
  ├── Validate: extracted text not empty (catches scanned/image PDFs)
  │
  ▼ db.create_resume_atomic_master(...)
  │   status = "processing", original_markdown stored permanently
  │
  ▼ parse_resume_to_json(markdown: str) → dict (processed_data)
  │   app/services/parser.py
  │   ├── Builds PARSE_RESUME_PROMPT with RESUME_SCHEMA_EXAMPLE
  │   ├── Calls complete_json() → LLM returns structured JSON
  │   ├── Validates with ResumeData.model_validate()
  │   ├── restore_dates_from_markdown() — corrects month loss
  │   └── normalize_resume_data() — adds sectionMetadata defaults
  │
  ▼ db.update_resume(resume_id, {processed_data, processing_status: "ready"})
  │
  └── Returns ResumeUploadResponse with processing_status
```

### Key Notes on Parsing
- `original_markdown` is stored permanently and never overwritten, even when the builder later saves the resume as JSON. This preserves original dates for the `_restore_original_dates()` pass in tailoring.
- If LLM parsing fails, `processing_status = "failed"` and the raw markdown is still accessible. The user can retry or use the builder directly.
- The schema example in `PARSE_RESUME_PROMPT` shows LLM the exact output format expected.

---

## 9. Job Description Parsing Pipeline

```
POST /api/v1/jobs/upload
  ├── Accept array of JD text strings
  ├── db.create_job(content, resume_id)  # just stores raw text
  └── Returns job_ids[]

POST /api/v1/jobs/extract-from-url
  ├── Try 3 User-Agent strategies (Googlebot, real browser, mobile)
  ├── LinkedIn: extract from JSON-LD (application/ld+json)
  ├── Indeed: extract from #jobDescriptionText div
  ├── Generic: strip HTML tags, decode entities, collapse whitespace
  └── Truncate to 5000 chars, return text

Keywords are extracted lazily (cached on job):
  extract_job_keywords(job_content) in services/improver.py
    ├── Uses EXTRACT_KEYWORDS_PROMPT
    ├── Returns: company, role, required_skills, preferred_skills,
    │           experience_requirements, education_requirements,
    │           key_responsibilities, keywords[], experience_years, seniority_level
    └── Cached in jobs.metadata_json with SHA-256 hash of content for invalidation
```

---

## 10. ATS Scoring Logic

### Formula (from ATS_ANALYSIS_PROMPT + ats_analyzer.py)

```
overall_score = (
    keyword_match      * 0.35 +   # % of important JD keywords found in resume
    skills_alignment   * 0.30 +   # How well candidate skills match role requirements
    experience_relevance * 0.20 + # How relevant work history is to this specific role
    education_fit      * 0.10 +   # Does education match requirements
    resume_completeness * 0.05    # Has all standard sections + contact info
)
```

The backend **recalculates** `overall` from the breakdown using the formula after parsing the LLM response to ensure mathematical consistency (`ats_analyzer.py:_parse_analysis`). The LLM-provided overall is used as a fallback but the formula wins.

### Score Calibration (from prompt)
- Poor fit: 30–45
- Moderate: 46–64  
- Good fit: 65–80
- Excellent: 85+

### ATS Analysis Output Structure
```
ATSAnalysisResult
├── ats_score: { overall: int, breakdown: {5 scores}, score_explanation }
├── keyword_analysis: { matched_keywords[], missing_keywords[], total_jd_keywords, match_percentage }
├── skill_gap: { critical_missing[], partial_match[], strong_matches[] }
├── resume_quality: { completeness_score, issues[], strengths[], bullet_quality }
├── interview_questions: [{question, category, why_asked, tip}]  # always 5
├── tailoring_recommendations: [{priority, section, recommendation, example}]
├── job_fit_verdict: { fit_level, summary, biggest_strength, biggest_gap }
├── resume_id, job_id, analyzed_at
```

### Project Optimizer (ATS Router)
- `POST /ats/analyze-projects` — ranks all resume projects by JD relevance (0–100), verdict = "keep" (≥60) or "replace" (<60)
- `POST /ats/suggest-project` — suggests ONE new project using only the candidate's existing skills
- `POST /ats/replace-project` — generates a JD-tailored replacement; supports `already_generated` list to ensure uniqueness

### AI Models / Weights / Prompts Used
- All ATS endpoints use `complete_json()` with `schema_type="enrichment"`
- Temperature and other params come from `LLMConfig` (stored in `config.json`)
- No embeddings are used — all scoring is LLM-driven via prompt engineering
- `reasoning_effort` parameter supported for OpenAI gpt-5 / Anthropic Claude 3.7+ / DeepSeek R1

---

## 11. Every API Endpoint

All routes are prefixed with `/api/v1`.

### Health (`/api/v1`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check → `{"status": "healthy"}` |
| GET | `/status` | Full status: LLM healthy, master resume exists, DB stats |
| GET | `/db-test` | Debug: test DB connection, returns resume count + engine type |

### Config (`/api/v1/config`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/config/llm-api-key` | Get current LLM config (API key masked) |
| PUT | `/config/llm-api-key` | Update LLM config (provider, model, api_base, reasoning_effort) |
| POST | `/config/llm-test` | Test LLM connection (with or without request body) |
| GET | `/config/features` | Get feature flags (cover_letter, outreach_message) |
| PUT | `/config/features` | Toggle feature flags |
| GET | `/config/language` | Get UI + content language |
| PUT | `/config/language` | Set UI + content language |
| GET | `/config/prompts` | Get improve prompt options + default |
| PUT | `/config/prompts` | Set default improve prompt ID |
| GET | `/config/feature-prompts` | Get custom cover letter / outreach prompts |
| PUT | `/config/feature-prompts` | Set custom prompts (validated for required placeholders) |
| GET | `/config/api-keys` | List all provider keys with masked values |
| POST | `/config/api-keys` | Update one or more provider API keys |
| DELETE | `/config/api-keys?confirm=CLEAR_ALL_KEYS` | Delete all API keys |
| DELETE | `/config/api-keys/{provider}` | Delete one provider's key |
| POST | `/config/reset` | Reset all DB data (requires `{"confirm": "RESET_ALL_DATA"}`) |

**Example — PUT /config/llm-api-key:**
```json
// Request
{"provider": "gemini", "model": "gemini/gemini-3-flash-preview", "reasoning_effort": null}
// Response
{"provider": "gemini", "model": "gemini/gemini-3-flash-preview", "api_key": "AIza****1234", "api_base": null}
```

### Resumes (`/api/v1/resumes`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/resumes/upload` | Upload PDF/DOCX, parse to JSON |
| GET | `/resumes?resume_id=<id>` | Fetch resume by ID (raw + processed + cover letter) |
| GET | `/resumes/list?include_master=false` | List all resumes sorted by updated_at desc |
| POST | `/resumes/improve/preview` | Tailor resume to JD (no DB write) |
| POST | `/resumes/improve/confirm` | Save tailored resume + create tracker card |
| POST | `/resumes/save` | Save builder edits to existing resume |
| DELETE | `/resumes/{resume_id}` | Delete a resume |
| POST | `/resumes/pdf` | Generate PDF from resume data |
| GET | `/resumes/{resume_id}/cover-letter` | Get cover letter |
| POST | `/resumes/{resume_id}/cover-letter` | Update cover letter |
| POST | `/resumes/{resume_id}/outreach` | Update outreach message |
| PUT | `/resumes/{resume_id}/title` | Update resume title |
| POST | `/resumes/generate-tailored-project` | Generate a new project for tailored resume |
| POST | `/resumes/{resume_id}/set-master` | Promote a resume to master |

**Example — POST /resumes/upload:**
```json
// Response
{
  "message": "File resume.pdf uploaded successfully",
  "request_id": "uuid",
  "resume_id": "uuid",
  "processing_status": "ready",
  "is_master": true
}
```

**Example — POST /resumes/improve/preview:**
```json
// Request
{"resume_id": "uuid", "job_id": "uuid", "prompt_id": "keywords"}
// Response (abbreviated)
{
  "request_id": "uuid",
  "resume_id": null,
  "resume_preview": { /* full ResumeData */ },
  "cover_letter": "Dear Hiring Manager...",
  "title": "Senior Engineer @ Stripe",
  "diff_summary": {"sections_changed": 3, "bullets_added": 2},
  "changes": [...]
}
```

### Jobs (`/api/v1/jobs`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/jobs/upload` | Upload one or more JDs, returns job_ids[] |
| GET | `/jobs/{job_id}` | Get job by ID |
| POST | `/jobs/extract-from-url` | Fetch JD from a URL |

**Example — POST /jobs/upload:**
```json
// Request
{"job_descriptions": ["We are hiring a..."], "resume_id": "uuid"}
// Response
{"message": "data successfully processed", "job_id": ["uuid"], "request": {...}}
```

### ATS (`/api/v1/ats`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/ats/analyze` | Full ATS analysis (request body: resume_id, job_id) |
| GET | `/ats/analyze/{resume_id}/{job_id}` | Same as above via GET |
| POST | `/ats/analyze-projects` | Rank all resume projects by JD relevance |
| POST | `/ats/suggest-project` | Suggest a new project to build |
| POST | `/ats/replace-project` | Generate a replacement for a specific project |

### Enrichment (`/api/v1/enrichment`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/enrichment/analyze/{resume_id}` | Identify weak bullets, generate questions (max 6) |
| POST | `/enrichment/enhance` | Generate new bullets from user answers |
| POST | `/enrichment/apply/{resume_id}` | Append new bullets to resume |
| POST | `/enrichment/regenerate` | Rewrite selected items based on user instruction |
| POST | `/enrichment/apply-regenerated/{resume_id}` | Apply rewritten items to resume |

### Applications (`/api/v1/applications`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/applications` | List all applications grouped by status column |
| POST | `/applications` | Manually add a card (paste JD) |
| GET | `/applications/{id}` | Get card with JD + applied resume |
| PATCH | `/applications/bulk` | Move many cards to one column |
| PATCH | `/applications/{id}` | Update card (status, position, notes, company, role) |
| DELETE | `/applications/{id}` | Delete a card |
| POST | `/applications/bulk-delete` | Delete many cards |

### Resume Wizard (`/api/v1/resume-wizard`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/resume-wizard/start` | Start wizard, get first question |
| POST | `/resume-wizard/answer` | Submit answer, get next question or final resume |

---

## 12. Every Dependency

### Backend (`pyproject.toml`)
| Package | Version | Why |
|---------|---------|-----|
| `fastapi` | 0.128.4 | Web framework (async routes, Pydantic integration) |
| `uvicorn` | 0.40.0 | ASGI server |
| `python-multipart` | 0.0.27 | File upload parsing (multipart/form-data) |
| `pydantic` | 2.12.5 | Data validation, schema definitions |
| `pydantic-settings` | 2.12.0 | Env var loading into Settings class |
| `tinydb` | 4.8.2 | Legacy (migration source only — DO NOT use for new features) |
| `sqlalchemy[asyncio]` | 2.0.36 | ORM + async session management |
| `aiosqlite` | 0.20.0 | Async SQLite driver for SQLAlchemy |
| `cryptography` | 46.0.7 | Fernet encryption for API keys at rest |
| `litellm` | 1.86.2 | Multi-provider LLM abstraction (routes to OpenAI, Anthropic, Gemini, etc.) |
| `markitdown[docx]` | 0.1.4 | Convert DOCX to markdown |
| `pdfminer.six` | 20260107 | Extract text from PDF |
| `playwright` | 1.58.0 | Headless Chromium for PDF rendering |
| `python-docx` | 1.2.0 | DOC/DOCX file handling |
| `python-dotenv` | 1.2.2 | Load `.env` file into environment |
| `fpdf2` | (transitive) | fpdf2 fallback PDF generation |
| `httpx` | (dev) | HTTP client for job URL fetching + test client |

### Frontend (`package.json`)
| Package | Version | Why |
|---------|---------|-----|
| `next` | ^16.2.6 | Framework: App Router, SSR, API proxy via rewrites |
| `react` / `react-dom` | ^19.2.4 | UI library |
| `tailwindcss` | ^4 | Utility-first CSS (v4, no config file) |
| `@tailwindcss/postcss` | ^4 | PostCSS integration for Tailwind v4 |
| `@dnd-kit/core` + `/sortable` + `/utilities` | ^6/^10/^3 | Drag-and-drop for Kanban + builder section reordering |
| `@tiptap/react` + `starter-kit` + `extension-link` + `extension-underline` | ^3.20 | Rich text editor (cover letter, outreach) |
| `lucide-react` | ^0.575.0 | Icon library |
| `clsx` | ^2.1.1 | Conditional className utility |
| `tailwind-merge` | ^3.5.0 | Merge Tailwind classes without conflicts |
| `tw-animate-css` | ^1.4.0 | Tailwind animation utilities |
| `isomorphic-dompurify` | ^3.0.0 | XSS sanitization for resume HTML preview |
| `vitest` | ^4.1.8 | Test runner |
| `@testing-library/react` | ^16.3.2 | React component testing |
| `jsdom` | ^28.1.0 | DOM simulation for tests |
| `eslint` / `eslint-config-next` | ^9/^16 | Linting |
| `prettier` | ^3.8.1 | Code formatting |
| `typescript` | ^5 | Type checking |

---

## 13. Every Environment Variable

### Backend (`.env` / environment)
| Variable | Default | Where Used |
|----------|---------|------------|
| `LLM_PROVIDER` | `openai` | `config.py` → LiteLLM provider selection |
| `LLM_MODEL` | `gpt-5-nano-2025-08-07` | `config.py` → LiteLLM model |
| `LLM_API_KEY` | `""` | `config.py` → fallback when no DB key exists |
| `LLM_API_BASE` | `None` | `config.py` → for Ollama, llama.cpp, custom endpoints |
| `HOST` | `0.0.0.0` | `config.py` → uvicorn host |
| `PORT` | `8000` | `config.py` + `start.sh` → uvicorn port |
| `RELOAD` | `False` | `config.py` → uvicorn auto-reload (dev only) |
| `LOG_LEVEL` | `INFO` | `config.py` → app logger level |
| `LOG_LLM` | `WARNING` | `config.py` → LiteLLM logger level |
| `FRONTEND_BASE_URL` | `http://localhost:3000` | `config.py` → PDF Playwright navigation URL + CORS |
| `REQUEST_TIMEOUT_SECONDS` | `240` | `config.py` → `asyncio.wait_for` on improve flow (30–1800) |
| `REASONING_EFFORT` | `""` (None) | `config.py` → for gpt-5/Claude/DeepSeek R1 |
| `CORS_ORIGINS` | `["http://localhost:3000","http://127.0.0.1:3000"]` | `config.py` → allowed CORS origins |
| `DATABASE_URL` | `""` (SQLite) | `db_engine.py` → if set, use PostgreSQL instead of SQLite |

### Frontend (`.env.local` / environment)
| Variable | Default | Where Used |
|----------|---------|------------|
| `BACKEND_ORIGIN` | `https://resume-matcher-6kv2.onrender.com` | `next.config.ts` → API proxy destination |
| `NEXT_PUBLIC_REQUEST_TIMEOUT_MS` | `240000` | `next.config.ts` + `lib/api/client.ts` → 3-layer timeout sync |

**CRITICAL TIMEOUT SYNC:** `REQUEST_TIMEOUT_SECONDS` (backend) × 1000 must equal `NEXT_PUBLIC_REQUEST_TIMEOUT_MS` (frontend). `next.config.ts` uses `proxyTimeout` with the same value. All three layers must be in sync, or the shortest one silently aborts the request.

---

## 14. Every External API / Service Used

| Service | How Used | Auth |
|---------|----------|------|
| **OpenAI API** | LLM completions via LiteLLM | `LLM_API_KEY` (stored encrypted in DB) |
| **Anthropic API** | LLM completions via LiteLLM | `anthropic` provider key in DB |
| **Google Gemini API** | LLM completions via LiteLLM | `google` provider key in DB |
| **OpenRouter** | LLM routing/aggregation via LiteLLM | `openrouter` provider key in DB |
| **DeepSeek API** | LLM completions via LiteLLM | `deepseek` provider key in DB |
| **Groq API** | LLM completions via LiteLLM | `groq` provider key in DB |
| **Ollama (local)** | LLM completions via LiteLLM | None (or `ollama` key if server has auth) |
| **Any OpenAI-compatible server** | llama.cpp, vLLM, LM Studio | Optional (sentinel `sk-no-key` if blank) |
| **Job posting URLs** | `httpx` fetches LinkedIn, Indeed, Glassdoor, etc. | None (Googlebot UA + fallbacks) |
| **Playwright/Chromium** | PDF rendering (headless) | None (local) |
| **Vercel** | Frontend hosting | Vercel account |
| **Render** | Backend hosting | Render account |
| **GitHub Container Registry** | Docker image distribution | GitHub Actions |

---

## 15. Current Git / Project Status

- **Active branch:** Not determined in this analysis (check `git branch`)
- **Version:** 1.2.0 (both frontend and backend)
- **Last deploy timestamp:** `2026-07-04T23:05:20Z` (from `app/.deploy-ts`)
- **Deployment targets:** Render (backend) + Vercel (frontend)
- **Backend render URL:** `https://resume-matcher-6kv2.onrender.com` (hardcoded default in `next.config.ts`)
- **Pre-push hooks:** `.githooks/pre-push` configured — check `.githooks/README.md` for hook setup
- **Pre-commit hooks:** `.pre-commit-config.yaml` present

---

## 16. Recent Changes Made

Based on code comments and deploy timestamps:

1. **`ats.py` router** — Added `/replace-project` endpoint with `already_generated` uniqueness list
2. **`resumes.py`** — Added `_protect_custom_sections()` and `_preserve_original_skills()` safety passes; fix for preview hash mismatch on schema-incomplete resumes (issue referenced as preview hash mismatch bug)
3. **`llm.py`** — Added `_scrub_secrets()` to redact API keys from error messages; added `reasoning_effort` support; LiteLLM `drop_params=True` + `modify_params=True`
4. **`config.py`** — Added `migrate_legacy_keys()` for one-time migration of plaintext keys; `_LEGACY_PROVIDER_KEY_MAP` to avoid circular import with `llm.py`
5. **`main.py`** — Added stale encrypted key cleanup on startup; Windows ProactorEventLoop fix
6. **`database.py`** — Switched from TinyDB to SQLAlchemy (behavior-preserving); `create_resume_atomic_master()` with asyncio.Lock
7. **`pdf.py`** — Fallback chain: Playwright frontend URL → Playwright built HTML → fpdf2; 7 templates; `max_pages` param
8. **`jobs.py`** — Added `extract-from-url` with LinkedIn JSON-LD, Indeed div, generic HTML parsing
9. **`next.config.ts`** — `proxyTimeout` driven by `NEXT_PUBLIC_REQUEST_TIMEOUT_MS`; optimizePackageImports for tree-shaking

---

## 17. Every Known Bug

### Bug 1: Timeout desync (was issue #776)
**Root cause:** `REQUEST_TIMEOUT_SECONDS` was raised on the backend but not `NEXT_PUBLIC_REQUEST_TIMEOUT_MS` on the frontend, causing the frontend proxy to abort first and appear as a "backend timeout."
**Status:** Fixed by documenting the 3-layer sync requirement. The comment in `config.py` and `next.config.ts` explains this.
**Risk:** If someone raises only one layer, it silently fails again.

### Bug 2: Preview hash mismatch on schema-incomplete resumes
**Root cause:** `improve/preview` hashed the raw `improved_data` dict, but `improve/confirm` hashed after `ResumeData.model_validate()` (which adds default fields). The hashes disagreed for resumes with missing optional fields.
**Status:** Fixed via `_hash_improved_data()` which canonicalizes through `ResumeData` before hashing.

### Bug 3: Stale API key ciphertexts after Render redeploy
**Root cause:** Render regenerates the secret key file on each deploy (ephemeral filesystem), making all previously encrypted keys unreadable.
**Status:** Partially mitigated — startup cleanup removes stale keys and logs a message. User must re-enter keys after redeploy.
**Proper fix:** Store `.secret_key` in a persistent volume or use an external secret manager.

### Bug 4: LinkedIn / Indeed job URL extraction may fail
**Root cause:** LinkedIn returns JS-rendered pages, and the static HTML extraction may miss the job description.
**Status:** LinkedIn JSON-LD extraction added as best-effort. Still falls back to 422 if nothing is extractable.
**Workaround:** User can paste JD text directly.

### Bug 5: Playwright unavailable on some hosts
**Root cause:** Chromium binary not installed or `playwright install chromium` not run.
**Status:** `fpdf2` fallback implemented. PDF quality is lower but functional.
**Note on production Render:** If Playwright fails, PDF still works via fpdf2.

### Bug 6: LLM drops months from dates
**Root cause:** LLM occasionally converts "Jan 2020 – Present" to "2020 – Present".
**Status:** Fixed via `_restore_original_dates()` pass in `resumes.py` — compares result vs original and restores month-precision dates.

### Bug 7: TinyDB migration creates duplicate resumes (edge case)
**Root cause:** If the old `database.json` has malformed records, the migration script may fail silently on some entries.
**Status:** Migration runs at startup; after first successful run, it's a no-op. The TinyDB file is not deleted automatically.
**Action needed:** After successful migration, verify data and optionally delete `data/database.json`.

---

## 18. Runtime / Build / Deployment Errors

### Build Error: `postcss` version conflict
`package.json` has `"overrides": {"postcss": "^8.5.10"}` to resolve a conflict between Tailwind 4 and older PostCSS consumers. If you upgrade Tailwind, re-verify this override.

### Runtime Error: `duplicate_v1_path` (LLM)
Error code surfaced in `/config/llm-test` when `api_base` includes `/v1` for Anthropic/Gemini/OpenRouter providers. LiteLLM appends `/v1` internally, creating `/v1/v1/` paths.
**Fix:** `_normalize_api_base()` in `llm.py` strips trailing `/v1` for these providers.

### Runtime Error: `html_response` (LLM)
Happens when the API base URL points at a non-API endpoint (e.g., the main website).
**Surfaced as:** error_code = `"html_response"` in health check response.

### Deployment: Vercel PDF download broken
PDF rendering requires Playwright, which uses the Chromium browser. Playwright cannot run on Vercel (serverless functions). The PDF endpoint is on the **backend** (Render), not Vercel. Calls from the frontend proxy to `/api/v1/resumes/pdf` go to the backend. The backend uses Playwright to navigate to `FRONTEND_BASE_URL/print/resumes/{id}`. This means the frontend must be publicly accessible when the backend generates PDFs.

### Windows Local Dev: Event Loop
`main.py` sets `asyncio.WindowsProactorEventLoopPolicy()` for Windows subprocess support (Playwright). This is applied only on `win32` platform.

---

## 19. Performance Issues

1. **LLM latency on improve/preview:** The tailoring flow makes 3 sequential LLM calls (keywords → skill plan → diffs) plus 3 parallel calls (cover letter + outreach + title). Total: ~15–60s depending on provider. The `asyncio.wait_for(timeout=REQUEST_TIMEOUT_SECONDS)` wrapper prevents infinite hangs but is set to 240s by default.

2. **Resume analysis (enrichment):** `complete_json()` with `max_tokens=8192` can be slow on smaller models. A 3-minute hard timeout wraps this call.

3. **ATS analysis:** `max_tokens=4000` for a full ATS analysis. This is expensive with large resumes + JDs. No streaming.

4. **PDF generation latency:** Playwright cold start adds ~2–5s on the first PDF per session. Subsequent calls reuse the browser instance. On Render free tier, the backend sleeps between requests, causing cold start on every PDF.

5. **Kanban board rendering:** No pagination on the tracker. With many applications, the board could become slow. This is a future concern.

6. **Frontend bundle:** `optimizePackageImports` in `next.config.ts` tree-shakes `lucide-react`, `@tiptap`, `@dnd-kit` to reduce cold start time.

---

## 20. Security Issues

1. **No authentication.** All endpoints are publicly accessible. Anyone who can reach the backend can read/write/delete all data. Acceptable for self-hosted single-user, unacceptable for multi-user deployments.

2. **API keys stored with symmetric encryption.** The Fernet key lives at `data/.secret_key`. If this file is compromised, all stored API keys are readable. On Render, the file is lost on redeploy (ephemeral disk).

3. **Job URL fetching uses external HTTP.** `jobs/extract-from-url` makes outbound requests to arbitrary URLs. It strips scripts and style blocks but doesn't do full sanitization. SSRF is possible if the server has internal network access.

4. **HTML sanitization for resume preview.** `isomorphic-dompurify` is used in the frontend for rich text display. Ensure all resume content rendered as HTML goes through `safe-html.tsx`.

5. **`/config/reset` is unauthenticated.** Only protected by a confirmation token. If someone discovers the endpoint, they can reset all data.

6. **LLM output injection.** LLM responses are parsed as JSON and applied to resume data. The safety passes (`_preserve_personal_info`, `_preserve_original_skills`, `_protect_custom_sections`) mitigate hallucination, but LLM output injection (prompt injection via JD) is a residual risk.

---

## 21. Technical Debt

1. **`tinydb` is a dependency but only used for migration.** It should be removed from `pyproject.toml` after all users have migrated. The migration script (`migrate_tinydb_to_sqlite.py`) runs at every startup but is a no-op after first migration.

2. **Dynamic fields on `Job` stored in `metadata_json`.** This is flexible but makes queries harder. `preview_hash`, `preview_hashes`, `job_keywords`, `company`, `role` should be first-class columns.

3. **No pagination on resume list or application list.** Both endpoints return all records. Will become a problem at scale.

4. **`resumes.py` is a 1000+ line file.** It has grown organically. The private helper functions (`_improve_preview_flow`, `_restore_original_dates`, etc.) should be extracted to `services/improver.py`.

5. **Config file `config.json` is read/written on every request** (via `config_cache.py` TTL cache, but cache invalidation adds complexity). Moving to a DB-backed config table would simplify this.

6. **Frontend has no global error state management.** Errors are handled per-component with local `useState`. A global error store (React Context or Zustand) would improve UX consistency.

7. **`fpdf2` fallback produces lower-quality PDFs** compared to Playwright HTML rendering. The two paths produce visually different output.

8. **Session-scoped Playwright browser** (`_browser_instance` global). This is a single shared instance. Under concurrent PDF requests, this could cause race conditions.

9. **No request IDs in logs.** Makes tracing a specific request's LLM calls across the async log stream difficult.

---

## 22. TODO / FIXME Comments in Codebase

Based on code analysis (search `grep -r "TODO\|FIXME\|HACK\|XXX\|BUG"` for current state):

Key known items from code comments:
- `resumes.py` — `stage = "load_job_keywords"` variable is referenced in error handling but never updated through the flow (the `stage` tracking is incomplete, so error logs may show the wrong stage)
- `llm.py` — `# Re-enable when a fallback deployment is added.` — Router cooldowns are disabled because there's only one deployment. This should be re-enabled if redundant LLM endpoints are added.
- `database.py` — `# Serializes concurrent master-resume promotion` — The asyncio.Lock is process-local. In a multi-process deployment (gunicorn with workers), the DB-level unique index is the only protection.
- `pdf.py` — `# fpdf2 fallback` — Acknowledged as lower quality. The comment says "use fpdf2 fallback" but no plan to improve it.
- `config.py` — `# Mirror of llm._PROVIDER_KEY_MAP, duplicated to avoid importing llm.py` — This duplication must be kept in sync manually.

---

## 23. Files Currently Under Development

Based on open editor files at time of handover:
- `apps/frontend/components/builder/resume-builder.tsx` — main builder component
- `apps/frontend/lib/i18n/messages.ts` — i18n message types
- `apps/frontend/components/common/theme-provider.tsx` — theme system
- `apps/frontend/components/resume/styles/_base.module.css` — base resume styles
- `apps/frontend/components/preview/paginated-preview.tsx` — preview pagination
- `apps/backend/app/routers/ats.py` — ATS endpoints (recently added replace-project)
- `apps/backend/app/pdf.py` — PDF rendering
- `apps/backend/start.sh` — production start script
- `apps/frontend/tsconfig.json` — TypeScript config

---

## 24. Files That Should NOT Be Modified

| File | Reason |
|------|--------|
| `apps/backend/app/scripts/migrate_tinydb_to_sqlite.py` | Migration is one-time; modifying it could corrupt data |
| `apps/backend/app/models.py` | SQLAlchemy models — any schema change requires a DB migration |
| `apps/backend/data/.secret_key` | If changed, all stored encrypted API keys become unreadable |
| `apps/backend/data/resume_matcher.db` | Production database — never edit directly |
| `apps/frontend/.next/` | Build output — regenerated by `next build` |
| `apps/frontend/node_modules/` | Dependencies — managed by npm |

---

## 25. Recommended Order to Finish the Project

1. **Fix ephemeral secret key on Render** — store `.secret_key` in a persistent volume or use Render's secret files feature. This blocks the "API keys lost on redeploy" bug permanently.

2. **Remove TinyDB from dependencies** — after confirming all data is migrated (`data/database.json` can be deleted or archived). Update `pyproject.toml`.

3. **Add authentication** — even a simple `Authorization: Bearer <token>` header check via middleware if multi-user is needed, or IP allowlist for single-user.

4. **Increase ATS test coverage** — the ATS scoring logic (`ats_analyzer.py`) has no unit tests. Add tests with mocked LLM responses to verify formula application and schema parsing.

5. **Improve error UX on tailoring timeout** — the 504 timeout response currently shows a raw error. Add a graceful UI state with a "try a simpler prompt" suggestion.

6. **Add streaming to LLM calls** — especially for the improve/preview flow. Streaming would allow the frontend to show progress instead of a blank loading spinner for 30+ seconds.

7. **Paginate resume list and applications** — add `limit`/`offset` to both list endpoints.

8. **Make `Job` metadata columns first-class** — add `company`, `role`, `job_keywords`, `preview_hash` as proper columns to the `jobs` table.

9. **PDF quality — improve fpdf2 fallback** — add custom fonts and better layout to match the Playwright output.

10. **Frontend global error handling** — add a React Context for global error/toast state.

---

## 26. Hidden Assumptions and Project-Specific Knowledge

1. **Single master resume invariant.** The system assumes one "master" resume exists. The first upload becomes master. All tailored resumes have `parent_id` pointing to the master. The builder always edits the master directly. The tailoring flow always produces a new child resume. This invariant is enforced by `asyncio.Lock` in `create_resume_atomic_master()`.

2. **`original_markdown` is sacred.** It's stored at upload and never overwritten. Even when the builder saves JSON, `original_markdown` is preserved. The tailoring pipeline reads it via `_get_original_markdown()` to restore date precision. Never overwrite this field.

3. **Preview hash validation flow.** The improve flow has a two-step confirm pattern: `preview` hashes the tailored data and stores it on the job; `confirm` re-hashes the submitted data and compares. This prevents the client from submitting modified data in the confirm step. The hash uses `json.dumps(sorted_keys=True, ensure_ascii=False)` for determinism.

4. **`config.json` stores non-secrets only.** The API key migration removed all secrets from this file. Any code that writes `api_key` or `api_keys` to `config.json` is a bug.

5. **LiteLLM model naming conventions.** The `get_model_name()` function handles provider prefixes. OpenAI models don't need a prefix. Ollama uses `ollama_chat/` (not `ollama/`). OpenRouter always needs `openrouter/` prefix. `openai_compatible` uses `openai/` prefix. Getting this wrong causes 404s or auth failures.

6. **`reasoning_effort` migration for gpt-5.** If the config has `provider=openai`, `model` contains `gpt-5`, and `reasoning_effort` is **absent from config.json** (not blank, absent), the system auto-migrates it to `minimal`. This migration fires once per config, then stores the value. Users who explicitly clear the field won't have it restored.

7. **Kanban status column ordering.** The seven statuses are defined in `APPLICATION_STATUS_ORDER` in schemas and must match the frontend's `STATUS_COLUMNS` constant. Adding a new status requires updating both.

8. **i18n content language vs UI language.** These are separate. `ui_language` controls the frontend interface. `content_language` tells the LLM what language to generate output in. They can be different (e.g., UI in English but generate resumes in Spanish).

9. **PDF generation requires the frontend to be accessible.** The backend navigates to `FRONTEND_BASE_URL/print/resumes/{id}`. If the frontend is down or the URL is wrong, Playwright fails and falls back to the `_build_resume_html()` HTML builder. In local dev, `FRONTEND_BASE_URL=http://localhost:3000` and you must have the frontend running.

10. **Database dual-engine design.** The `api_keys` table is read synchronously on the LLM hot path. The sync engine and async engine both point to the same file. The sync engine uses `scoped_session`. Never use the async engine for `api_keys` and never use the sync engine for document tables (resume, job, etc.).

11. **`tinydb` is only for migration.** The `tinydb==4.8.2` import only appears in `migrate_tinydb_to_sqlite.py`. No new code should use TinyDB.

12. **Windows-only: ProactorEventLoop.** The `asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())` in `main.py` is needed for Playwright subprocess support on Windows. Remove this line only if you're sure the app will never run on Windows.

---

## 27. Developer Continuation Guide

This section gives a new AI engineer everything needed to continue without asking any questions.

### Local Setup (Backend)

```bash
# Prerequisites: Python 3.13+, uv (pip install uv)
cd apps/backend

# Install dependencies
uv sync

# Install Playwright browsers (for PDF)
uv run playwright install chromium

# Create .env (copy from example and fill in your LLM API key)
copy .env.example .env
# Edit .env: set LLM_PROVIDER, LLM_MODEL, LLM_API_KEY

# Run development server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or use the app console script
uv run app
```

### Local Setup (Frontend)

```bash
cd apps/frontend

# Install dependencies
npm install

# Create .env.local
echo "BACKEND_ORIGIN=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_REQUEST_TIMEOUT_MS=240000" >> .env.local

# Run development server
npm run dev
```

### Run Tests

```bash
# Backend tests
cd apps/backend
uv run pytest

# Frontend tests
cd apps/frontend
npm run test
```

### Build Commands

```bash
# Frontend production build
cd apps/frontend
npm run build

# Backend has no build step (Python, no compilation)
```

### Run Commands (Production)

```bash
# Backend
cd apps/backend
sh start.sh
# or: uvicorn app.main:app --host 0.0.0.0 --port 10000

# Frontend
cd apps/frontend
npm run build
npm run start
```

### Docker

```bash
# Build backend image
docker build -t resume-matcher-backend ./apps/backend

# Run backend
docker run -p 8000:8000 \
  -e LLM_PROVIDER=openai \
  -e LLM_MODEL=gpt-4o-mini \
  -e LLM_API_KEY=sk-... \
  -v $(pwd)/data:/app/data \
  resume-matcher-backend
```

### Deployment Commands

```bash
# Render (backend) — auto-deploys on push to main
# Manual trigger: render deploy --service-id <id>

# Vercel (frontend) — auto-deploys on push to main
# Manual trigger:
cd apps/frontend
npx vercel --prod

# Required Vercel env vars:
# BACKEND_ORIGIN=https://resume-matcher-6kv2.onrender.com
# NEXT_PUBLIC_REQUEST_TIMEOUT_MS=240000
```

### Adding a New LLM Provider

1. Add provider string to `Literal` type in `config.py:Settings.llm_provider`
2. Add to `_PROVIDER_KEY_MAP` in `llm.py`
3. Add to `_LEGACY_PROVIDER_KEY_MAP` in `config.py` (duplicate, see tech debt note)
4. Add prefix to `provider_prefixes` dict in `llm.py:get_model_name()`
5. Add to `SUPPORTED_PROVIDERS` list in `routers/config.py`
6. Add field to `ApiKeysUpdateRequest` schema in `schemas/models.py`
7. Handle it in the `update_api_keys()` router function
8. Update frontend API key settings UI

### Making a Schema Change (DB migration)

SQLAlchemy uses `create_all()` which only creates new tables/columns, never drops or alters. For any breaking schema change:
1. Add the column to the model with a default value
2. The next startup will add the column to SQLite via `CREATE TABLE IF NOT EXISTS`
3. For PostgreSQL, you need an Alembic migration (not currently set up) or manual `ALTER TABLE`

### Debugging LLM Issues

1. Check `/api/v1/status` — shows `llm_healthy`
2. Check `/api/v1/config/llm-test` — runs a test completion with `include_details: true`
3. Set `LOG_LLM=DEBUG` env var to see all LiteLLM traffic
4. For timeout issues, check that all three layers are in sync: `REQUEST_TIMEOUT_SECONDS`, `NEXT_PUBLIC_REQUEST_TIMEOUT_MS`, and `proxyTimeout` in `next.config.ts`

### Key File Relationships to Know

```
When you change ATS scoring weights:
→ Update ATS_ANALYSIS_PROMPT in app/prompts/ats_analysis.py
→ Update _parse_analysis() in app/services/ats_analyzer.py (recalculation formula)

When you add a new resume field:
→ Update ResumeData in app/schemas/models.py
→ Update RESUME_SCHEMA_EXAMPLE in app/prompts/templates.py
→ Update IMPROVE_SCHEMA_EXAMPLE in app/prompts/templates.py
→ Update PARSE_RESUME_PROMPT
→ Update resume templates in apps/frontend/components/resume/
→ Update the builder form in apps/frontend/components/builder/resume-form.tsx

When you add a new tailoring strategy:
→ Add to IMPROVE_RESUME_PROMPTS dict in app/prompts/templates.py
→ Add to IMPROVE_PROMPT_OPTIONS list
→ Add to DIFF_STRATEGY_INSTRUCTIONS dict
→ Update frontend strategy selector in components/builder/
```

### Current Blockers

1. **API keys lost on Render redeploy** — Users must re-enter keys after every backend deployment. No persistent volume configured.
2. **No authentication** — Cannot safely expose to multiple users.
3. **LinkedIn job URL extraction unreliable** — JS-rendered pages not supported (no Playwright for scraping).
4. **Playwright cold start on Render free tier** — First PDF after a period of inactivity takes 10–15s.

---

## 28. pyproject.toml (Backend)

```toml
[project]
name = "rm-backend"
version = "1.2.0"
description = "Resume Matcher Backend API"
requires-python = ">=3.13"
dependencies = [
    "fastapi==0.128.4",
    "uvicorn==0.40.0",
    "python-multipart==0.0.27",
    "pydantic==2.12.5",
    "pydantic-settings==2.12.0",
    "tinydb==4.8.2",
    "sqlalchemy[asyncio]==2.0.36",
    "aiosqlite==0.20.0",
    "cryptography==46.0.7",
    "litellm==1.86.2",
    "markitdown[docx]==0.1.4",
    "pdfminer.six==20260107",
    "playwright==1.58.0",
    "python-docx==1.2.0",
    "python-dotenv==1.2.2",
]
```

## 29. .env.example (Backend, secrets masked)

```dotenv
LLM_PROVIDER=openai
LLM_MODEL=gpt-5-nano-2025-08-07
LLM_API_KEY=sk-your-api-key-here

HOST=0.0.0.0
PORT=8000
RELOAD=false
LOG_LEVEL=INFO
LOG_LLM=WARNING
FRONTEND_BASE_URL=http://localhost:3000
REQUEST_TIMEOUT_SECONDS=240

# DATABASE_URL=postgresql://user:pass@host:5432/db  # leave blank for SQLite
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

---

*End of handover document. Generated by full codebase analysis on 2026-07-15.*
