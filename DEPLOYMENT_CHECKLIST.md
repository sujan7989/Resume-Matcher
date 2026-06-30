# Resume Matcher — Deployment Checklist

## Pre-Deployment ✅

### Supabase Setup
- [ ] Supabase account created (https://supabase.com)
- [ ] Project created (e.g., "resume-matcher")
- [ ] PostgreSQL database initialized
- [ ] Got the **Session Pooler** connection string (port 6543)
- [ ] Connection string format verified: `postgresql://postgres:PASSWORD@HOST:6543/postgres`
- [ ] Password is URL-encoded (@ → %40, # → %23, etc.)

### Render Setup
- [ ] Render account created (https://render.com)
- [ ] GitHub repository connected
- [ ] Web Service created
- [ ] Service name noted: `resume-matcher-gw36` (or your service)

### Local Development (Optional, but recommended)
- [ ] Python 3.13+ installed
- [ ] `uv` package manager installed
- [ ] Cloned repo locally
- [ ] Backend dependencies installed: `pip install -r requirements.txt`
- [ ] Tested locally with SQLite first

---

## Environment Variables on Render 🔑

### Step 1: Open Render Dashboard
```
https://dashboard.render.com → Your Service → Settings
```

### Step 2: Add These Variables

#### DATABASE_URL (Required ⚠️)
```
Key:   DATABASE_URL
Value: postgresql://postgres:Sujankumar%40143@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
```
- [ ] Copied exact value from Supabase
- [ ] Password is URL-encoded
- [ ] Using Session Pooler (port 6543, not 5432)
- [ ] Saved

#### LLM_PROVIDER (If different from groq)
```
Key:   LLM_PROVIDER
Value: groq
```
- [ ] Set or verified (default: groq)
- [ ] Saved

#### LLM_API_KEY
```
Key:   LLM_API_KEY
Value: gsk_j8qTp2S9pEGCtJx6h9ozWGdyb3FYS3FI6wnt315UsX1Apw67byxmgroq
```
- [ ] Copied from groq.com
- [ ] Not exposed in git (already in .gitignore)
- [ ] Saved

#### LLM_MODEL
```
Key:   LLM_MODEL
Value: llama-3.3-70b-versatile
```
- [ ] Set to your chosen model
- [ ] Saved

#### CORS_ORIGINS (Required for frontend)
```
Key:   CORS_ORIGINS
Value: ["https://resume-matcher-zeta.vercel.app"]
```
- [ ] Set to your actual Vercel frontend URL (not localhost!)
- [ ] Saved

#### FRONTEND_BASE_URL (Optional but recommended)
```
Key:   FRONTEND_BASE_URL
Value: https://resume-matcher-gw36.onrender.com
```
- [ ] Set to your actual Render backend URL
- [ ] Saved

---

## Deploy to Render 🚀

### Step 1: Trigger Redeploy
```
Render Dashboard → Deployments → Latest Build
  → Three Dots (...) → Redeploy
```

### Step 2: Monitor Build
- [ ] Build started
- [ ] Waiting for logs to show
- [ ] Docker image building...
- [ ] Python dependencies installing...
- [ ] Playwright chromium installing...
- [ ] Build completed (took ~5-10 minutes)

### Step 3: Watch for Startup
```
Look for in logs:
✅ "Database initialized successfully"
✅ "Started server process"
✅ "Waiting for application startup"
✅ "Application startup complete"
✅ "Uvicorn running on http://0.0.0.0:8000"
```

### Step 4: Check Status
```
Render Dashboard shows:
✅ Service: Running (green icon)
✅ No errors in Logs tab
```

---

## Post-Deployment Verification ✅

### Test 1: Backend Health Check
```bash
curl https://resume-matcher-gw36.onrender.com/api/v1/health
```
Expected response:
```json
{"status":"healthy"}
```
- [ ] Receives 200 OK
- [ ] JSON contains `"status":"healthy"`

### Test 2: Backend Status
```bash
curl https://resume-matcher-gw36.onrender.com/api/v1/status
```
Expected response:
```json
{
  "status": "ready",
  "llm_configured": true,
  "llm_healthy": true,
  "has_master_resume": false,
  "database_stats": {
    "total_resumes": 0,
    "total_jobs": 0,
    "total_improvements": 0,
    "has_master_resume": false
  }
}
```
- [ ] Returns 200 OK
- [ ] `llm_configured` is true
- [ ] `llm_healthy` is true
- [ ] `database_stats` shows valid numbers (not empty)

### Test 3: Frontend Connection
1. Open your Vercel frontend URL
2. Check browser console (F12 → Console tab)
3. Look for errors:
   - [ ] No "CORS error"
   - [ ] No "Failed to fetch"
   - [ ] No "404" for `/api/v1/` endpoints

### Test 4: Upload Resume
1. Click "Upload Resume" button
2. Select a PDF or text file
3. Wait for processing
4. Verify:
   - [ ] No errors in console
   - [ ] Resume appears in "My Resumes" list
   - [ ] Shows filename and upload date

### Test 5: Create Job Description
1. Click "Add Job Description"
2. Paste a job posting (copy from LinkedIn, etc.)
3. Click "Save"
4. Verify:
   - [ ] Job appears in UI
   - [ ] No 500 errors in logs

### Test 6: Tailor Resume
1. Select resume from dropdown
2. Select job description
3. Choose tailoring options:
   - [ ] Select some skills to focus on
   - [ ] Choose tone (professional/casual)
   - [ ] Enable cover letter generation
4. Click "Tailor Resume"
5. Verify:
   - [ ] Preview shows differences (green/red diffs)
   - [ ] LLM API was called (check Groq dashboard)
   - [ ] No 500 errors

### Test 7: Confirm & Download
1. Click "Confirm Tailoring"
2. System creates tailored resume
3. Click "Download PDF"
4. Verify:
   - [ ] PDF downloads successfully
   - [ ] File has actual content (not empty)
   - [ ] Tailored text appears in PDF

### Test 8: Application Tracker
1. Verify new application appears in tracker
2. Check:
   - [ ] Status shows "applied"
   - [ ] Company/role extracted from job
   - [ ] Can move between columns (drag & drop)

---

## Troubleshooting 🔧

### Issue: Database Connection Failed
```
Error: FATAL: database "postgres" does not exist
```
**Fix:**
- [ ] Check DATABASE_URL is set in Render
- [ ] Verify connection string from Supabase (Session Pooler)
- [ ] Test connection string locally
- [ ] Redeploy after fix

### Issue: CORS Error
```
Access to XMLHttpRequest at 'https://...' blocked by CORS policy
```
**Fix:**
- [ ] Add your frontend URL to CORS_ORIGINS
- [ ] Use exact URL from browser (protocol, domain, port)
- [ ] Redeploy after fix

### Issue: 404 on Resume Upload
```
POST /api/v1/resumes/upload returns 404
```
**Fix:**
- [ ] Check backend is running (health check works)
- [ ] Verify CORS_ORIGINS includes frontend
- [ ] Check browser console for exact error
- [ ] Look at Render logs for backend errors

### Issue: LLM API Not Working
```
Error: Invalid API key for provider 'groq'
```
**Fix:**
- [ ] Verify LLM_API_KEY is set in Render (not just locally)
- [ ] Check key is valid (test on groq.com)
- [ ] Check LLM_PROVIDER matches the key (groq key for groq provider)
- [ ] Redeploy after fix

### Issue: PDF Download Fails
```
Error downloading PDF
```
**Fix:**
- [ ] Check FRONTEND_BASE_URL is set correctly
- [ ] Verify browser has enough memory
- [ ] Check Render logs for Playwright errors
- [ ] Try smaller resume first

---

## Performance Tips 🚀

### Render Service
- [ ] Using free tier? Upgrade to standard tier if needed
- [ ] RAM: At least 512MB recommended
- [ ] Build times: 5-10 minutes normal for first deploy

### Supabase Database
- [ ] Using free tier? Limits: 50k requests/month
- [ ] Session Pooler: Reduces connection overhead (use this!)
- [ ] Monitor usage in Supabase dashboard

### Frontend (Vercel)
- [ ] Deployed on free tier? No cold starts
- [ ] Environment variables set correctly
- [ ] Redeploy after updating BACKEND_ORIGIN

---

## Monitoring & Maintenance 🔍

### Daily Checks
- [ ] Backend health check passes
- [ ] No errors in Render logs
- [ ] Resumes upload successfully
- [ ] Tailoring works end-to-end

### Weekly Checks
- [ ] Supabase database size (monitor growth)
- [ ] Render build times (getting slower?)
- [ ] Check for any 500 errors in logs

### Monthly Checks
- [ ] Update dependencies: `pip list --outdated`
- [ ] Check Groq API quota usage
- [ ] Review database backup (Supabase)
- [ ] Test disaster recovery plan

---

## Rollback Plan 🔄

If something breaks on Render:

1. **Don't Panic** ✅ — Render keeps previous deployments

2. **Find Previous Working Deployment:**
   ```
   Render Dashboard → Deployments → Find green "Deployed" status
   ```

3. **Redeploy Previous Version:**
   ```
   Click that deployment → Three Dots → Redeploy
   ```

4. **Verify:**
   - [ ] Health check passes
   - [ ] Resume upload works
   - [ ] Frontend connects

5. **Fix Root Cause:**
   - [ ] Review what changed
   - [ ] Fix code or environment variables
   - [ ] Test locally first
   - [ ] Push fix to main
   - [ ] Render auto-redeploys

---

## Success! 🎉

You should now have:
- ✅ PostgreSQL database on Supabase
- ✅ Backend running on Render with database connected
- ✅ Frontend on Vercel pointing to backend
- ✅ End-to-end resume tailoring working
- ✅ All data persisting across deployments
- ✅ Ready for production use

---

## Support & Resources

**Documentation:**
- IMMEDIATE_ACTIONS.md — Quick fix guide
- SUPABASE_RENDER_SETUP.md — Detailed setup
- ARCHITECTURE_AND_FLOW.md — How everything works

**External Resources:**
- Render Docs: https://render.com/docs
- Supabase Docs: https://supabase.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com/
- Next.js Docs: https://nextjs.org/docs

