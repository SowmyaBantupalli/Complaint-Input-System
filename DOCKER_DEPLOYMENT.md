# Docker Deployment Guide for Render

## Why Docker?
Render's free tier doesn't support `apt-get` commands or Aptfile for native Python environments. Using Docker gives you full control over system packages.

## Quick Deployment Steps

### 1. Ensure Files are in Repository
Make sure these files exist in your repo root:
- ✅ `Dockerfile`
- ✅ `.dockerignore`

### 2. Push to GitHub
```bash
git add Dockerfile .dockerignore
git commit -m "Add Docker support for deployment"
git push origin main
```

### 3. Deploy on Render

#### Option A: New Service (Recommended)
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `Complaint-Input-System`
4. Configure:
   - **Name**: `complaint-backend` (or any name)
   - **Environment**: Select **"Docker"** 
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Dockerfile Path**: Leave empty (auto-detected)
   - **Docker Build Context Directory**: Leave empty (uses root)
5. Click **"Create Web Service"**

#### Option B: Update Existing Service
1. Go to your existing service in Render
2. Click **"Settings"**
3. Scroll to **"Build & Deploy"**
4. Change **"Environment"** from **"Python 3"** to **"Docker"**
5. Save changes
6. Go to **"Manual Deploy"** → **"Clear build cache & deploy"**

### 4. Wait for Build
- First build takes ~5-10 minutes (installing Tesseract, Python dependencies)
- Subsequent builds are faster (~2-3 minutes)
- Watch the logs to see progress

### 5. Verify Deployment
Once deployed, test your API:
```bash
# Check health
curl https://your-app.onrender.com

# Test with text
curl -X POST https://your-app.onrender.com/analyze \
  -F "complaint=Someone stole my bike at 8 PM"
```

## Troubleshooting

### Build fails with "Dockerfile not found"
- Ensure `Dockerfile` is in the **root** of your repository
- Check capitalization: must be exactly `Dockerfile`, not `dockerfile`

### "Port not found" or "Service unavailable"
- The Dockerfile already handles `$PORT` environment variable
- Render automatically sets this
- No action needed

### Build is slow
- First build installs all system packages (normal)
- Builds are cached - future deployments are faster
- Consider upgrading to Render's paid tier for faster builds

### Out of memory during build
- Current Dockerfile is optimized for free tier
- If issues persist, try paid tier with more resources

## What Docker Does

The Dockerfile:
1. ✅ Installs Tesseract OCR system packages
2. ✅ Installs Python dependencies
3. ✅ Configures proper port binding
4. ✅ Runs uvicorn server

## Cost
- Render Free Tier: **$0/month**
  - 750 hours/month free
  - Service spins down after 15 min inactivity
  - Cold starts take ~30 seconds

## Alternative Platforms

If Render doesn't work:

### Railway
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repo
4. Railway auto-detects Dockerfile
5. Deploy!

### Fly.io
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
cd "E:\Dev Projects\Complaint Input System"
flyctl launch
flyctl deploy
```

Both platforms have free tiers and excellent Docker support.
