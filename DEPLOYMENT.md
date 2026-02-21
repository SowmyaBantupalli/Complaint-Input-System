# Deployment Guide

## Auto-Redeploy on Git Push

### Vercel (Frontend)
✅ **Yes, auto-redeploy is enabled by default**

When you:
1. Make changes to code
2. Commit: `git add . && git commit -m "your message"`
3. Push: `git push origin main`

Vercel will automatically:
- Detect the push to your repository
- Trigger a new build
- Deploy the updated frontend
- No manual action required!

You can:
- Watch build progress in Vercel dashboard
- See build logs and deployment status
- Rollback to previous deployments if needed

### Render/Railway (Backend)
✅ **Yes, auto-redeploy is also enabled**

Same process:
- Push your code changes to main branch
- The service detects the change
- Automatically rebuilds and redeploys

## Important Notes

### For Code Changes:
- Backend changes (main.py) → Backend redeployment triggered
- Frontend changes (src/) → Frontend redeployment triggered
- Both can happen simultaneously if you change both

### Environment Variables:
- If you update `VITE_BACKEND_URL` in Vercel settings, you must:
  1. Save the new variable
  2. Trigger a manual redeploy (or push any change)
  3. The new variable will be used in the build

### First-Time Setup:
After connecting your GitHub repo to Vercel/Render:
1. Enable automatic deployments (usually ON by default)
2. Set main/master as the production branch
3. Every push to that branch = automatic deployment

## Quick Commands

```bash
# Check git status
git status

# Add all changes
git add .

# Commit with message
git commit -m "Added comments and improved code documentation"

# Push to trigger deployment
git push origin main

# Check deployment status
# Go to: https://vercel.com/dashboard or your hosting dashboard
```

## Viewing Deployment Logs
- Vercel: Dashboard → Your Project → Deployments → Click latest deployment
- Render: Dashboard → Your Service → Logs tab
- Railway: Dashboard → Your Project → Deployments

## Pro Tips
- Wait for build to complete before testing (usually 1-3 minutes)
- Check deployment logs if something breaks
- Test locally first: `npm run dev` (frontend) and `uvicorn main:app --reload` (backend)
- Small commits are better than large ones for easier debugging
