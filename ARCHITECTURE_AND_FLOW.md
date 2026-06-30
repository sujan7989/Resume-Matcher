# Resume Matcher — Architecture & Data Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│ User's Browser                                          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│ Vercel (Next.js Frontend)                               │
│ https://resume-matcher-zeta.vercel.app                  │
├─────────────────────────────────────────────────────────┤
│ - Upload resume form                                    │
│ - Job description input                                 │
│ - Resume tailoring UI                                   │
│ - Application tracker                                   │
│ - PDF download button                                   │
└────────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │ Makes API     │ Calls via     │ Redirect to
         │ requests to   │ fetch()       │ backend for
         │ backend       │               │ PDF download
         ▼               ▼               ▼
┌──────────────────────────────────────────────────────────┐
│ Render Web Service (FastAPI Backend)                     │
│ https://resume-matcher-gw36.onrender.com                │
├──────────────────────────────────────────────────────────┤
│ Routes:                                                  │
│ - POST /api/v1/resumes/upload        (upload resume)    │
│ - GET  /api/v1/resumes?resume_id=... (fetch resume)    │
│ - GET  /api/v1/resumes/list          (list resumes)    │
│ - POST /api/v1/jobs                  (add job desc)     │
│ - POST /api/v1/improve-preview       (preview tailoring)│
│ - POST /api/v1/improve-confirm       (finalize tailoring)
│ - GET  /api/v1/resumes/{id}/download (PDF)            │
│ - GET  /api/v1/health                (health check)    │
│ - GET  /api/v1/status                (full status)     │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ Supabase PostgreSQL Database                             │
│ aws-1-ap-southeast-1.pooler.supabase.com:6543           │
├──────────────────────────────────────────────────────────┤
│ Tables:                                                  │
│ - resumes          (original & tailored resumes)        │
│ - jobs             (job descriptions)                   │
│ - improvements     (tailoring history)                  │
│ - applications     (tracker cards)                      │
│ - api_keys         (encrypted LLM credentials)          │
└──────────────────────────────────────────────────────────┘
```

---

## Data Flow Example: Upload & Tailor Resume

### Step 1: Upload Resume
```
User selects PDF → Frontend
         │
         ▼
POST /api/v1/resumes/upload (multipart/form-data)
         │
         ▼
Backend FastAPI
    ├─ Parse PDF/text
    ├─ Extract structured data (name, email, skills, experience)
    ├─ Generate markdown representation
    ├─ Save to database with status="processing"
    └─ Return resume_id
         │
         ▼
Frontend shows in "My Resumes" list
```

**Database Record:**
```python
Resume(
    resume_id="6edde992-48a9-42b3-8137-e3971defa4a6",
    content="Full resume text/markdown",
    content_type="md",
    is_master=true,  # First upload is master
    processed_data={
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "experience": [...]
    },
    processing_status="ready",
    created_at="2026-06-30T12:00:00+00:00"
)
```

### Step 2: Add Job Description
```
User pastes job description → Frontend
         │
         ▼
POST /api/v1/jobs (JSON body)
    {
        "content": "Job description text...",
        "resume_id": "6edde992-48a9-42b3-8137-e3971defa4a6"
    }
         │
         ▼
Backend FastAPI
    ├─ Extract job keywords (Python, FastAPI, etc.)
    ├─ Generate job hash for caching
    ├─ Save to database
    └─ Return job_id
         │
         ▼
Frontend stores job_id for next step
```

### Step 3: Select Tailoring Options
```
User chooses:
- ✓ Focus on: ["Backend Development", "API Design"]
- ✓ Tone: ["professional", "detailed"]
- ✓ Format: "ATS-friendly"
- ✓ Include cover letter: true
         │
         ▼
Frontend sends to backend:
POST /api/v1/improve-preview
    {
        "original_resume_id": "6edde992...",
        "job_id": "abc123...",
        "selected_skills": ["Python", "FastAPI"],
        "improvement_options": {
            "tone": "professional",
            "focus_areas": ["Backend Development"]
        }
    }
         │
         ▼
Backend FastAPI
    ├─ Call LLM (Groq) with resume + job + options
    ├─ Generate diff: "Added 3 lines, removed 1 line"
    ├─ Generate preview markdown
    └─ Return preview without saving
         │
         ▼
Frontend shows preview (can revise/cancel)
```

### Step 4: Confirm & Create Tailored Resume
```
User clicks "Tailor Resume" → Frontend
         │
         ▼
POST /api/v1/improve-confirm
    {
        "original_resume_id": "6edde992...",
        "job_id": "abc123...",
        "improvements_accepted": true
    }
         │
         ▼
Backend FastAPI
    ├─ Apply diffs to original resume
    ├─ Create new Resume record (parent_id=original)
    ├─ Save as tailored_resume_id
    ├─ Create Improvement record (linking original → tailored)
    ├─ Generate cover letter (optional)
    ├─ Create Application tracker card
    └─ Return tailored_resume_id
         │
         ▼
Frontend redirects to download page
```

**Database Records Created:**
```python
# Original resume (unchanged)
Resume(id="6edde992...", is_master=true, content="...")

# Tailored resume (new)
Resume(
    id="def456...",
    parent_id="6edde992...",
    content="Tailored text...",  # Modified to match job
    processed_data={...}  # Updated skills/experience
)

# History record
Improvement(
    request_id="xyz789...",
    original_resume_id="6edde992...",
    tailored_resume_id="def456...",
    job_id="abc123...",
    improvements=[
        {"section": "summary", "type": "modified", "diff": "..."}
    ]
)

# Tracker card
Application(
    job_id="abc123...",
    resume_id="def456...",
    status="applied",
    company="Acme Corp",
    role="Senior Backend Engineer"
)
```

### Step 5: Download Tailored Resume as PDF
```
User clicks "Download PDF" → Frontend
         │
         ▼
GET /api/v1/resumes/{id}/download
         │
         ▼
Backend FastAPI
    ├─ Fetch Resume record
    ├─ Render markdown → HTML
    ├─ Convert HTML → PDF using Playwright/Chromium
    ├─ Set header: Content-Disposition: attachment
    └─ Return PDF binary
         │
         ▼
Browser downloads: "resume-tailored.pdf"
```

---

## API Endpoints & Database Queries

### Critical Endpoints for the Flow

| Endpoint | Method | Purpose | Query |
|----------|--------|---------|-------|
| `/resumes/upload` | POST | Upload PDF/text | N/A |
| `/resumes?resume_id=xxx` | GET | Fetch single resume | `SELECT * FROM resumes WHERE resume_id=?` |
| `/resumes/list` | GET | List all resumes | `SELECT * FROM resumes ORDER BY created_at` |
| `/jobs` | POST | Add job description | `INSERT INTO jobs (...) VALUES (...)` |
| `/improve-preview` | POST | Preview tailoring | Query LLM (no DB insert) |
| `/improve-confirm` | POST | Confirm tailoring | `INSERT INTO resumes, improvements, applications` |
| `/resumes/{id}/download` | GET | PDF download | `SELECT content FROM resumes WHERE resume_id=?` |

---

## Why It Was Failing

### Before Fix (❌)
```
Render Web Service
    ▼
    No DATABASE_URL environment variable
    ▼
    Backend tries to use SQLite (local file)
    ▼
    But Render environment is ephemeral (files deleted after restart)
    ▼
    OR Render's DATABASE_URL was set to wrong value
    ▼
    PostgreSQL connection failed
    ▼
    All queries returned 404/500
    ▼
    Frontend couldn't fetch/save resumes
```

### After Fix (✅)
```
Render Web Service
    ▼
    DATABASE_URL set to Supabase connection string
    ▼
    Backend connects to PostgreSQL on Supabase
    ▼
    All queries succeed
    ▼
    Resumes persist across Render restarts
    ▼
    Frontend can upload, tailor, download
    ▼
    System works end-to-end
```

---

## Database Schema

### Resumes Table
```python
class Resume(Base):
    __tablename__ = "resumes"
    
    resume_id: str = PrimaryKey()
    content: str              # Raw markdown/text
    content_type: str         # "md", "txt", "pdf"
    filename: str             # "my-resume.pdf"
    is_master: bool = False   # First upload is master
    parent_id: str | None     # For tailored resumes
    
    processed_data: dict      # Structured (name, email, skills)
    processing_status: str    # "pending", "processing", "ready", "failed"
    
    cover_letter: str | None
    outreach_message: str | None
    title: str | None
    
    created_at: str
    updated_at: str
```

### Jobs Table
```python
class Job(Base):
    __tablename__ = "jobs"
    
    job_id: str = PrimaryKey()
    content: str              # Full job description
    resume_id: str | None     # Associated resume
    
    metadata_json: dict       # Keywords, company, role, etc.
    created_at: str
```

### Improvements Table
```python
class Improvement(Base):
    __tablename__ = "improvements"
    
    request_id: str = PrimaryKey()
    original_resume_id: str   # Before
    tailored_resume_id: str   # After
    job_id: str               # What it was tailored for
    
    improvements: list[dict]  # Line-by-line changes
    created_at: str
```

### Applications Table (Tracker)
```python
class Application(Base):
    __tablename__ = "applications"
    
    application_id: str = PrimaryKey()
    job_id: str
    resume_id: str            # Which resume was used
    master_resume_id: str | None
    
    status: str               # "saved", "applied", "interview", etc.
    company: str | None
    role: str | None
    applied_at: str | None
    notes: str | None
    
    position: int             # Order in column
    created_at: str
    updated_at: str
```

---

## Environment Variables Explained

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:6543/db` |
| `LLM_PROVIDER` | Which AI service to use | `groq` |
| `LLM_MODEL` | Which model | `llama-3.3-70b-versatile` |
| `LLM_API_KEY` | API key for LLM | `gsk_...` |
| `FRONTEND_BASE_URL` | URL of Next.js frontend | `https://vercel-url.vercel.app` |
| `CORS_ORIGINS` | Which origins can call API | `["https://vercel-url"]` |
| `PORT` | What port backend runs on | `8000` (Render uses `$PORT` env var) |

---

## Success Indicators

✅ **System is working when:**
1. `GET /api/v1/health` returns `{"status": "healthy"}`
2. `GET /api/v1/status` shows `"status": "ready"`
3. Resume upload succeeds and appears in list
4. Job description is saved and linked to resume
5. Tailoring preview shows diffs
6. Tailored resume is created
7. PDF download generates and downloads
8. Tracker card shows "applied"

❌ **System has issues if:**
- ❌ Health check returns 500
- ❌ Status shows `"status": "setup_required"`
- ❌ Resume upload fails with 404
- ❌ Tailoring returns 500
- ❌ PDF download fails

---

## Typical User Journey

```
1. User lands on frontend
   ↓
2. Clicks "Upload Resume"
   ↓
3. Selects PDF file
   ↓
4. Resume appears in "My Resumes"
   ↓
5. User pastes job description
   ↓
6. Job is saved with keywords extracted
   ↓
7. User clicks "Tailor to Job"
   ↓
8. Frontend shows preview with diffs
   ↓
9. User clicks "Confirm"
   ↓
10. Tailored resume created with cover letter
   ↓
11. User clicks "Download PDF"
   ↓
12. PDF downloads to their computer
   ↓
13. User sees "Applied" card in tracker
   ↓
14. User can upload more resumes, tailor to more jobs
```

This entire flow depends on DATABASE_URL being correctly configured so all data persists in Supabase PostgreSQL.

