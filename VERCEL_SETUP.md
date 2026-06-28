# Vercel Environment Variables Setup

## For PDF Downloads to Work

You need to set environment variables in your Vercel project. This is a one-time setup.

## Steps

### 1. Go to Vercel Dashboard
Visit: https://vercel.com/dashboard

### 2. Select Your Project
Find and click on: `resume-matcher` (or your project name)

### 3. Go to Settings
Click on "Settings" tab at the top

### 4. Environment Variables
Click "Environment Variables" in the left sidebar

### 5. Add These Variables

#### Option A: (RECOMMENDED - Already Works)
If you see `BACKEND_ORIGIN` already set to:
```
BACKEND_ORIGIN=https://resume-matcher-gw36.onrender.com
```
✅ **No action needed!** The fix is already active.

#### Option B: (If BACKEND_ORIGIN is not set)
Click "Add New"
- **Name**: `BACKEND_ORIGIN`
- **Value**: `https://resume-matcher-gw36.onrender.com`
- **Environments**: Select all (Development, Preview, Production)
- Click "Save"

#### Option C: (Already using localhost)
If you see:
```
BACKEND_ORIGIN=http://127.0.0.1:8000
```
Edit this variable and change the value to:
```
https://resume-matcher-gw36.onrender.com
```

### 6. Redeploy
Click the "Deployments" tab, then click the three dots (⋯) on the latest deployment and select "Redeploy"

**Wait 2-3 minutes for the new deployment to complete.**

### 7. Test PDF Download
1. Go to https://resume-matcher-zeta.vercel.app
2. Upload a resume
3. Find a job posting and tailor your resume
4. Click "Download PDF"
5. Should download successfully ✅

## What These Variables Do

| Variable | Value | Purpose |
|----------|-------|---------|
| `BACKEND_ORIGIN` | `https://resume-matcher-gw36.onrender.com` | Tells Vercel frontend where the backend API is located |
| `NEXT_PUBLIC_REQUEST_TIMEOUT_MS` | `240000` | (Optional) 240 second timeout for long operations like PDF rendering |

## Environment Visibility

| Variable | Accessible From |
|----------|-----------------|
| `BACKEND_ORIGIN` | ✅ Server (Build time & Runtime) |
| `NEXT_PUBLIC_*` | ✅ Browser (Client-side) & Server |

**Note:** The fix uses `BACKEND_ORIGIN` which is server-side only, so it works even though browsers can't see it directly.

## Troubleshooting

### Problem: "No variables set"
- This is fine! The new `next.config.ts` has a sensible default.
- But for explicit control, add `BACKEND_ORIGIN` as shown above.

### Problem: "I set the variable but PDF still fails"
1. Make sure the deployment completed (check Deployments tab)
2. Hard refresh browser: `Ctrl+Shift+Delete` → Clear cache → Refresh
3. Wait 5 minutes and try again (Vercel CDN may need to update)
4. Check browser console (F12) for exact error

### Problem: "Variable is set but I don't see it in logs"
- Environment variables are applied at build time
- You need to **redeploy** for changes to take effect
- Click "Redeploy" on your latest deployment

## Vercel Redeployment FAQ

### Do I need to edit code to update environment variables?
**No.** Just update the variable in Vercel Settings and redeploy.

### How long does redeployment take?
**2-3 minutes** typically. You can watch the progress in the Deployments tab.

### Will redeployment cause downtime?
**No.** Vercel keeps the previous version live until the new one is ready.

### What if the redeployment fails?
1. Check the deployment logs (click the failed deployment to see errors)
2. Usually it's due to missing dependencies or syntax errors
3. If it's from your code changes, fix them and push to GitHub
4. Vercel will auto-redeploy

## Manual Git-based Deployment

If you prefer to trigger deployment via Git instead:

```bash
cd resume-matcher-deploy
git add .
git commit -m "Update environment variables"
git push origin codex/resume-wizard-design
```

Vercel will automatically detect the push and redeploy.

## Backend Render Configuration

**For reference, your backend on Render should have:**

```
FRONTEND_BASE_URL=https://resume-matcher-zeta.vercel.app
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_j8qTp2S9pEGCtJx6h9ozWGdyb3FYS3FI6wnt315UsX1Apw67byxmgroq
REQUEST_TIMEOUT_SECONDS=240
CORS_ORIGINS=["https://resume-matcher-zeta.vercel.app"]
```

**Is your backend working?**
Test: https://resume-matcher-gw36.onrender.com/api/v1/health

Should return `200 OK`

## Still Having Issues?

### Check the Console Logs
When downloading a PDF, check browser console (F12 → Console):

**Good (you should see this):**
```
[next.config.ts] BACKEND_ORIGIN: https://resume-matcher-gw36.onrender.com
[downloadResumePdf] Fetching PDF from: https://resume-matcher-gw36.onrender.com/api/v1/resumes/...
```

**Bad (means frontend doesn't have the config):**
```
[next.config.ts] BACKEND_ORIGIN: http://127.0.0.1:8000
[downloadResumePdf] Fetching PDF from: http://127.0.0.1:8000/api/v1/resumes/...
```

If you see the "Bad" version:
- Environment variable not set correctly
- OR redeployment hasn't completed yet
- Try waiting 5 minutes and hard refresh (Ctrl+F5)

### Network Tab Analysis
1. Press F12 → Network tab
2. Click "Download PDF"
3. Look for the PDF request (should show `/api/v1/resumes/.../pdf`)
4. Check the response status:
   - **200**: Good! (If download still fails, check file permissions)
   - **404**: Resume not found in backend (re-upload resume)
   - **503**: Backend error (check Render logs)
   - **Other errors**: Check the error message in the response

### Direct Backend Test
Open in your browser:
```
https://resume-matcher-gw36.onrender.com/api/v1/health
```

Should show:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-29T...",
  ...
}
```

If this fails, the backend is down - check Render dashboard.

## Summary

✅ **Frontend code fix**: Updated `next.config.ts` to use production backend URL  
✅ **Backend code**: Already correctly configured  
✅ **What you need to do**: 
- Optional: Set `BACKEND_ORIGIN` in Vercel (defaults work now)
- If you do set it: Redeploy from Vercel dashboard
- Test PDF download

The system will now properly route PDF requests from Vercel frontend to your Render backend!
