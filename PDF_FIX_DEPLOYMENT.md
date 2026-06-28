# PDF Download Fix - Deployment Guide

## Problem Summary
PDF downloads were failing with 404 errors because the frontend couldn't route requests to the backend properly. The frontend was trying to reach the backend at the wrong URL.

## Root Cause
1. **Frontend** (`next.config.ts`) had a fallback backend URL: `http://127.0.0.1:8000` (localhost)
2. **Vercel** (where frontend is hosted) cannot reach localhost
3. **Result**: PDF download requests failed because they were routed to an unreachable localhost instead of the actual Render backend

## Solution Implemented

### 1. Frontend Changes (apps/frontend/next.config.ts)
- **Changed default BACKEND_ORIGIN** from `http://127.0.0.1:8000` to `https://resume-matcher-gw36.onrender.com`
- **Added logging** to help debug routing issues
- This ensures that PDF download requests go to the correct production backend

### 2. Frontend Error Logging (apps/frontend/lib/api/resume.ts)
- **Enhanced downloadResumePdf()** with better error logging
- Now logs the full URL being requested and response details
- Makes future debugging easier

### 3. Backend Configuration (render.yaml - Already Correct)
```yaml
- key: FRONTEND_BASE_URL
  value: https://resume-matcher-zeta.vercel.app
```
The backend correctly points to the frontend for PDF rendering.

## Verification Checklist

### ✅ Backend (Render)
- [ ] Backend URL: https://resume-matcher-gw36.onrender.com
- [ ] Health check passes: `curl https://resume-matcher-gw36.onrender.com/api/v1/health`
- [ ] FRONTEND_BASE_URL set to: `https://resume-matcher-zeta.vercel.app`
- [ ] GROQ_API_KEY configured (LLM for resume tailoring)

### ✅ Frontend (Vercel)
- [ ] Frontend URL: https://resume-matcher-zeta.vercel.app
- [ ] Environment variable set (in Vercel dashboard):
  - `BACKEND_ORIGIN=https://resume-matcher-gw36.onrender.com` (optional, uses default now)
  - Or leave unset to use the new default in next.config.ts

### ✅ PDF Download Flow
1. User uploads resume ✅
2. User tailors resume to job description ✅
3. User clicks "Download PDF"
4. Frontend calls: `/api/v1/resumes/{id}/pdf?...params`
5. Next.js rewrites to: `https://resume-matcher-gw36.onrender.com/api/v1/resumes/{id}/pdf?...params`
6. Backend fetches: `https://resume-matcher-zeta.vercel.app/print/resumes/{id}?...params`
7. Playwright renders print page to PDF
8. Frontend receives PDF blob and downloads

## Environment Variables Reference

### Vercel Frontend
```
# Optional - uses sensible default if not set
BACKEND_ORIGIN=https://resume-matcher-gw36.onrender.com

# Request timeout (ms) - should match backend REQUEST_TIMEOUT_SECONDS
NEXT_PUBLIC_REQUEST_TIMEOUT_MS=240000
```

### Render Backend (.env)
```
# Critical for PDF generation - points to your frontend
FRONTEND_BASE_URL=https://resume-matcher-zeta.vercel.app

# LLM configuration (for resume tailoring and parsing)
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_j8qTp2S9pEGCtJx6h9ozWGdyb3FYS3FI6wnt315UsX1Apw67byxmgroq

# Request timeout must match frontend
REQUEST_TIMEOUT_SECONDS=240

# CORS - allows Vercel frontend to access backend API
CORS_ORIGINS=["https://resume-matcher-zeta.vercel.app"]
```

## Troubleshooting

### Problem: PDF still fails with 404
**Diagnosis Steps:**
1. Check browser console (F12 → Console tab) for the logged URL
2. Example: `[downloadResumePdf] Fetching PDF from: https://resume-matcher-gw36.onrender.com/api/v1/resumes/{id}/pdf...`
3. Try accessing that URL directly in browser to see actual error
4. Check Render backend logs for the corresponding request

**Common Issues:**
- **Resume ID not found in backend**: Database might not have the resume
  - Solution: Re-upload the resume
- **Playwright browser failure**: Print page failed to render to PDF
  - Solution: Fallback PDF will be generated instead (basic text-based)
  - Check backend logs for the specific Playwright error

### Problem: 503 Service Unavailable
**Likely Cause:** Playwright browser failed or frontend unreachable

**Solutions:**
1. Check Render backend logs for PDF rendering errors
2. Verify FRONTEND_BASE_URL is accessible from Render
3. Check if frontend is up: `curl https://resume-matcher-zeta.vercel.app`
4. If Playwright crashes, fallback PDF will be used

### Problem: Timeout (after 240s)
**Likely Cause:** Playwright is taking too long to render

**Solutions:**
1. Increase REQUEST_TIMEOUT_SECONDS in render.yaml (max 1800s)
2. Simplify the resume (remove unnecessary sections)
3. Try a different template (e.g., "clean" instead of "modern")
4. Check Render resource usage (may be CPU throttled)

### Problem: CORS errors in browser
**Likely Cause:** CORS_ORIGINS not configured correctly

**Check:**
```
GET https://resume-matcher-gw36.onrender.com/api/v1/health
Response headers should include:
Access-Control-Allow-Origin: https://resume-matcher-zeta.vercel.app
```

**Fix:**
Update render.yaml CORS_ORIGINS to match your frontend URL

## Deployment Steps

### Step 1: Update Frontend (Vercel)
```bash
git add apps/frontend/next.config.ts apps/frontend/lib/api/resume.ts
git commit -m "fix: PDF routing - use production backend URL"
git push origin codex/resume-wizard-design
```
Vercel will auto-deploy on push.

### Step 2: Verify Frontend Deployment
- [ ] Wait for Vercel deployment to complete
- [ ] Visit https://resume-matcher-zeta.vercel.app
- [ ] Open browser console (F12 → Console)
- [ ] Check for any deployment warnings

### Step 3: Test PDF Download
1. Upload a test resume
2. Find a job posting
3. Tailor the resume to the job
4. Click "Download PDF"
5. Verify PDF downloads successfully
6. Check browser console for logging output

### Step 4: Monitor for Errors
- Watch browser console for logging during PDF download
- Check Render backend logs for rendering issues
- If timeout occurs, increase REQUEST_TIMEOUT_SECONDS

## Expected Behavior After Fix

### Happy Path:
```
[Console Logs]
[downloadResumePdf] Fetching PDF from: https://resume-matcher-gw36.onrender.com/api/v1/resumes/2c3d0364-568b-4a86-8908-1304236f7778/pdf?template=swiss-single&pageSize=A4&lang=en

[Network Tab]
GET /api/v1/resumes/2c3d0364-568b-4a86-8908-1304236f7778/pdf?... 200 OK

[Download]
resume_2c3d0364-568b-4a86-8908-1304236f7778.pdf (successfully downloaded)
```

### If Playwright Fails (Fallback):
```
[Network Tab]
GET /api/v1/resumes/2c3d0364-568b-4a86-8908-1304236f7778/pdf?... 200 OK

[Download]
resume_2c3d0364-568b-4a86-8908-1304236f7778.pdf (basic PDF with fallback message)

[Render Backend Logs]
WARNING: Browser rendering failed, trying thread-based approach
WARNING: Thread-based rendering failed
[Falls back to simple PDF generation]
```

## Files Modified
- `apps/frontend/next.config.ts` - Changed default BACKEND_ORIGIN
- `apps/frontend/lib/api/resume.ts` - Added error logging
- `render.yaml` - Already correctly configured

## Key Takeaways

| Component | URL | Purpose |
|-----------|-----|---------|
| Frontend | https://resume-matcher-zeta.vercel.app | React/Next.js UI |
| Backend | https://resume-matcher-gw36.onrender.com | FastAPI server, PDF generation, LLM calls |
| Frontend → Backend | next.config.ts rewrites `/api/*` | API proxy from Vercel to Render |
| Backend → Frontend | FRONTEND_BASE_URL | Playwright needs this to render PDFs |

The fix ensures both directions work correctly for the PDF download pipeline.
