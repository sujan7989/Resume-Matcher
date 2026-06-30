# Quick Reference Card

## The Fix (TL;DR)

```
Go to: https://dashboard.render.com

YOUR SERVICE → Settings → Environment Variables

Add:
┌─────────────────────────────────────────────────────────────────┐
│ Key:   DATABASE_URL                                             │
│ Value: postgresql://postgres:Sujankumar%40143@                  │
│        aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres  │
└─────────────────────────────────────────────────────────────────┘

Add:
┌─────────────────────────────────────────────────────────────────┐
│ Key:   CORS_ORIGINS                                             │
│ Value: ["https://resume-matcher-zeta.vercel.app"]              │
└─────────────────────────────────────────────────────────────────┘

Click: Save Changes

Then: Deployments → Redeploy latest

Wait: 5-10 minutes for build
```

## Test URLs

```
Health:  https://resume-matcher-gw36.onrender.com/api/v1/health
Status:  https://resume-matcher-gw36.onrender.com/api/v1/status

Frontend: https://resume-matcher-zeta.vercel.app
```

## API Endpoints

```
POST /api/v1/resumes/upload         → Upload resume
GET  /api/v1/resumes?resume_id=xxx  → Get resume
GET  /api/v1/resumes/list           → List resumes
POST /api/v1/jobs                   → Add job description
POST /api/v1/improve-preview        → Preview tailoring
POST /api/v1/improve-confirm        → Confirm tailoring
GET  /api/v1/resumes/{id}/download  → Download PDF
GET  /api/v1/health                 → Health check
GET  /api/v1/status                 → Full status
```

## Supabase Connection String Parts

```
postgresql://     ← Protocol
postgres:         ← Username
Sujankumar%40143  ← Password (URL-encoded, @ → %40)
@                 ← Separator
aws-1-ap-southeast-1.pooler.supabase.com ← Host
:6543             ← Port (Session Pooler = 6543, not 5432!)
/postgres         ← Database name
```

## Environment Variables

| Variable | Value | Where Set |
|----------|-------|-----------|
| DATABASE_URL | `postgresql://...` | Render dashboard |
| LLM_PROVIDER | `groq` | Render dashboard |
| LLM_MODEL | `llama-3.3-70b-versatile` | Render dashboard |
| LLM_API_KEY | `gsk_...` | Render dashboard |
| CORS_ORIGINS | `["https://vercel-url"]` | Render dashboard |
| FRONTEND_BASE_URL | `https://render-url` | Render dashboard (optional) |

## Troubleshooting

| Issue | Check | Fix |
|-------|-------|-----|
| 500 error | Render logs | DATABASE_URL set? Password encoded? |
| 404 resume | Database connected? | Query DB directly from Supabase |
| CORS error | Frontend URL | Add to CORS_ORIGINS |
| PDF fails | Browser console | Check Render logs |
| Can't upload | Health check | Test `/api/v1/health` first |

## One-Minute Checklist

- [ ] Added DATABASE_URL to Render environment
- [ ] Added CORS_ORIGINS to Render environment
- [ ] Clicked Save Changes
- [ ] Redeployed on Render
- [ ] Waited for build to complete
- [ ] Tested health endpoint → 200 OK
- [ ] Uploaded test resume → Success
- [ ] Downloaded PDF → Works

## Files Created/Modified

```
Modified:
├── apps/backend/.env                    (added DATABASE_URL)
├── apps/backend/.env.example            (added DATABASE_URL docs)

Created:
├── IMMEDIATE_ACTIONS.md                 (quick fix guide)
├── SUPABASE_RENDER_SETUP.md             (detailed setup)
├── ARCHITECTURE_AND_FLOW.md             (system architecture)
├── DEPLOYMENT_CHECKLIST.md              (full checklist)
├── FIX_SUMMARY.md                       (comprehensive summary)
└── QUICK_REFERENCE.md                   (this file)
```

## Key Points

✅ **Frontend code:** Correct
✅ **Backend code:** Correct
✅ **API endpoints:** Correct
❌ **DATABASE_URL in Render:** Missing ← THIS WAS THE PROBLEM

**Solution:** Add DATABASE_URL to Render → Redeploy → Done

## Need Help?

1. **Quick fix?** → Read IMMEDIATE_ACTIONS.md
2. **Detailed setup?** → Read SUPABASE_RENDER_SETUP.md
3. **How it works?** → Read ARCHITECTURE_AND_FLOW.md
4. **Full checklist?** → Read DEPLOYMENT_CHECKLIST.md
5. **Why it failed?** → Read FIX_SUMMARY.md

## Timeline

- **5 min:** Add environment variables
- **10 min:** Redeploy on Render
- **1 min:** Test health check
- **1 min:** Upload test resume
- **Done!** System is working

**Total:** ~20 minutes to fully operational

