# Resume Matcher — Render + Supabase Deployment Guide

## Problem Summary
The backend was failing with:
```
Database initialization error: (psycopg2.OperationalError) connection to server at "aws-1-ap-southeast-1.pooler.supabase.com" (13.213.241.248), port 6543 failed: FATAL: database "postgres" does not exist
```

This happens because:
1. The backend code checks for `DATABASE_URL` environment variable
2. If set, it uses PostgreSQL (Supabase); if not set, it uses SQLite
3. Render was receiving DATABASE_URL from somewhere, but it was incorrect/incomplete
4. **The fix:** Configure the correct Supabase connection string in Render's dashboard

---

## Step 1 — Set DATABASE_URL in Render Dashboard

### Go to Render Settings
1. Navigate to https://dashboard.render.com
2. Find your service: **resume-matcher-gw36** (or your service name)
3. Click **Settings** in the top navigation
4. Scroll to **Environment** section

### Add DATABASE_URL Variable
1. Click **Add Environment Variable**
2. Set:
   - **Key:** `DATABASE_URL`
   - **Value:** `postgresql://postgres:Sujankumar%40143@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres`
3. Click **Save Changes**

### Important Notes
- **Use the "Session Pooler" URL** from Supabase (not the direct URL)
- The password `Sujankumar%40143` is URL-encoded (`@` → `%40`)
- The port **6543** is the pooler port (not 5432)
- Never commit `.env` files to git (it's already in `.gitignore`)

---

## Step 2 — Update CORS_ORIGINS for Your Deployment

The backend blocks requests from unauthorized origins. Update this too:

1. In Render dashboard, add another environment variable:
   - **Key:** `CORS_ORIGINS`
   - **Value:** `["https://resume-matcher-zeta.vercel.app"]` (or your Vercel frontend URL)

---

## Step 3 — Update FRONTEND_BASE_URL

If your frontend needs to know the backend URL:

1. Add environment variable:
   - **Key:** `FRONTEND_BASE_URL`
   - **Value:** `https://resume-matcher-gw36.onrender.com`

---

## Step 4 — Redeploy

After adding environment variables:

1. Go to **Deployments** tab in Render
2. Click the three dots on the latest deployment
3. Select **Redeploy**
4. Wait for the build to complete

---

## Step 5 — Verify the Fix

### Check Backend Health
Open in your browser or curl:
```
https://resume-matcher-gw36.onrender.com/api/v1/health
```

Should return:
```json
{
  "status": "healthy"
}
```

### Check Full Status
```
https://resume-matcher-gw36.onrender.com/api/v1/status
```

Should show:
```json
{
  "status": "ready",
  "llm_configured": true,
  "llm_healthy": true,
  "has_master_resume": false
}
```

### Check Frontend
Navigate to your Vercel frontend and try:
1. Upload a resume
2. Create a job description
3. Tailor the resume to the JD

---

## Troubleshooting

### Still Getting 404 or 500 Errors

**Check Render Logs:**
1. In Render dashboard, click **Logs** tab
2. Look for errors like `Database initialization error` or `connection refused`

**Common Issues:**
- ❌ Wrong password in DATABASE_URL → Check Supabase password is URL-encoded
- ❌ Wrong port (5432 instead of 6543) → Use the **Session Pooler** URL
- ❌ DATABASE_URL not set → Verify it's in Render's environment variables
- ❌ CORS error → Check CORS_ORIGINS includes your frontend URL

### PostgreSQL Connection Failed

If you see: `FATAL: database "postgres" does not exist`

**Solution:** This means Supabase's `postgres` database was deleted or not created. You need to:
1. Go to Supabase dashboard
2. Create a new project (or use existing)
3. Get the **Session Pooler** connection string
4. Update DATABASE_URL in Render

---

## How the Routing Works

```
Frontend Request
        ↓
GET /api/v1/resumes?resume_id=xxx
        ↓
Backend (/apps/backend/app/routers/resumes.py)
        ↓
Query database (PostgreSQL/Supabase)
        ↓
Response with resume data
```

**Endpoint:** `GET /api/v1/resumes?resume_id={id}`
- Uses **query parameter** (not path parameter)
- Frontend calls: `/api/v1/resumes?resume_id=6edde992-48a9-42b3-8137-e3971defa4a6`
- Backend handler: `async def get_resume(resume_id: str = Query(...))`

---

## Local Development

To test locally with Supabase instead of SQLite:

1. Copy `.env.example` to `.env` in `apps/backend/`:
   ```bash
   cp apps/backend/.env.example apps/backend/.env
   ```

2. Add DATABASE_URL:
   ```
   DATABASE_URL=postgresql://postgres:Sujankumar%40143@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
   ```

3. Run backend:
   ```bash
   cd apps/backend
   uv run app
   ```

---

## Next Steps

After verifying the backend works:

1. **Upload a resume** in the frontend
2. **Add a job description** 
3. **Select tailoring options** (skills to focus on, tone, format)
4. **Download tailored resume as PDF**
5. **Check application tracker** to see history

If any of these fail, check:
- Browser console for errors
- Render logs for backend errors
- Supabase dashboard for database issues

---

## Contact & Support

If you need to:
- Migrate data from SQLite to PostgreSQL: See `app/scripts/migrate_tinydb_to_sqlite.py`
- Change LLM provider: Update `LLM_PROVIDER` and `LLM_API_KEY` in Render environment
- Use different Supabase project: Get new connection string and update `DATABASE_URL`

