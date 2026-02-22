# 🐋 Docker Deployment Guide - Render

## ✅ **Fixed Issues**

### **Problem:** `ModuleNotFoundError: No module named 'bns_classifier'`
**Root Cause:** Dockerfile was only copying `main.py`, missing `bns_classifier.py` and `data/` folder

### **Solution Applied:**
✅ Updated Dockerfile to copy all required files
✅ Fixed `.dockerignore` to not exclude necessary Python modules
✅ Ensures `data/bns_sections.csv` is included in container

---

## 📁 **Project Structure**

```
Complaint Input System/
├── main.py                  # FastAPI application
├── bns_classifier.py        # AI classifier module ✅ REQUIRED
├── data/
│   └── bns_sections.csv     # BNS dataset ✅ REQUIRED
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration ✅ FIXED
├── .dockerignore           # Files to exclude from Docker
└── render.yaml             # Render configuration (optional)
```

---

## 🐋 **Corrected Dockerfile**

```dockerfile
FROM python:3.11-slim

# Install Tesseract OCR and system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code - ALL necessary files
COPY main.py .
COPY bns_classifier.py .    # ✅ AI classifier module
COPY data/ ./data/           # ✅ BNS dataset

# Expose port (Render sets $PORT dynamically)
EXPOSE 8000

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**Key Changes:**
- ✅ Added `COPY bns_classifier.py .`
- ✅ Added `COPY data/ ./data/`
- ✅ Preserves correct Python module structure

---

## 🚀 **Deploy to Render with Docker**

### **Step 1: Prepare Your Repository**

Ensure these files are committed:
```bash
git add Dockerfile .dockerignore main.py bns_classifier.py data/
git commit -m "Fix Docker deployment - include all required files"
git push origin main
```

### **Step 2: Create Render Service**

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name:** `complaint-analyzer-api`
   - **Environment:** `Docker`
   - **Region:** Choose nearest
   - **Branch:** `main`
   - **Dockerfile Path:** `./Dockerfile` (auto-detected)

### **Step 3: Set Environment Variables**

In Render dashboard, add:
```
Key: GEMINI_API_KEY
Value: [your_actual_api_key_from_google]
```

**Get API key:** https://makersuite.google.com/app/apikey

### **Step 4: Deploy**

Click **"Create Web Service"**

Render will:
1. Clone your repository
2. Build Docker image (5-8 minutes first time)
3. Run container
4. Assign a URL: `https://your-service.onrender.com`

---

## 🔍 **Verify Deployment**

### **1. Check Health**
```bash
curl https://your-service.onrender.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "gemini_api": "active",
  "bns_dataset": "loaded",
  "ocr_engine": "tesseract"
}
```

### **2. Test Classification**
```bash
curl -X POST https://your-service.onrender.com/analyze \
  -F "complaint=Someone stole my phone at City Mall yesterday"
```

**Expected response:**
```json
{
  "status": "ok",
  "ai_powered": true,
  "crime_type": "Theft",
  "bns_sections": [...]
}
```

---

## 🐛 **Troubleshooting**

### **Issue: ModuleNotFoundError**
**Symptoms:**
```
ModuleNotFoundError: No module named 'bns_classifier'
```

**Solutions:**
1. ✅ Verify `bns_classifier.py` is in repository
2. ✅ Check Dockerfile has `COPY bns_classifier.py .`
3. ✅ Ensure `.dockerignore` doesn't exclude `*.py` files
4. ✅ Rebuild: Push changes to trigger new build

### **Issue: BNS Dataset Not Found**
**Symptoms:**
```
FileNotFoundError: data/bns_sections.csv
```

**Solutions:**
1. ✅ Verify `data/bns_sections.csv` is in repository
2. ✅ Check Dockerfile has `COPY data/ ./data/`
3. ✅ Ensure `.dockerignore` doesn't exclude `data/`
4. ✅ Rebuild: Push changes to trigger new build

### **Issue: Import Errors**
**Symptoms:**
```
ImportError: cannot import name 'get_classifier'
```

**Solutions:**
1. ✅ Verify import in `main.py`: `from bns_classifier import get_classifier`
2. ✅ Ensure both files are in same directory (WORKDIR /app)
3. ✅ Check file permissions in container
4. ✅ Rebuild with `--no-cache` if needed

### **Issue: Port Binding Error**
**Symptoms:**
```
Error binding to port
```

**Solutions:**
1. ✅ Ensure CMD uses: `--port ${PORT:-8000}`
2. ✅ Render sets `$PORT` automatically (don't hardcode)
3. ✅ Use `0.0.0.0` not `localhost` or `127.0.0.1`

---

## 📊 **Best Practices for Production**

### **1. Multi-Stage Builds (Optional Optimization)**
```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
RUN apt-get update && apt-get install -y tesseract-ocr && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY main.py bns_classifier.py ./
COPY data/ ./data/
ENV PATH=/root/.local/bin:$PATH
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### **2. Health Checks**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"
```

### **3. Non-Root User (Security)**
```dockerfile
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
```

### **4. Build Optimization**
- ✅ Copy `requirements.txt` before code (leverage Docker cache)
- ✅ Use `.dockerignore` to exclude unnecessary files
- ✅ Use `--no-cache-dir` for pip to reduce image size
- ✅ Clean up apt cache after install

---

## 🔄 **Local Testing Before Deploy**

### **Build Image:**
```bash
docker build -t complaint-analyzer .
```

### **Run Container:**
```bash
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key_here \
  complaint-analyzer
```

### **Test Locally:**
```bash
curl http://localhost:8000/health
```

---

## 📈 **Performance & Scaling**

### **Container Resources (Render Free Tier):**
- **RAM:** 512 MB
- **CPU:** Shared
- **Disk:** Ephemeral
- **Sleep:** After 15 min inactivity

### **Scaling Options:**
1. **Vertical:** Upgrade to Starter ($7/month) for 2GB RAM
2. **Horizontal:** Add multiple instances with load balancer
3. **Caching:** Add Redis for BNS dataset caching

---

## ✅ **Deployment Checklist**

Before deploying:
- [ ] `bns_classifier.py` in repository
- [ ] `data/bns_sections.csv` in repository
- [ ] Dockerfile copies all necessary files
- [ ] `.dockerignore` doesn't exclude Python files
- [ ] `requirements.txt` has all dependencies
- [ ] `GEMINI_API_KEY` set in Render environment
- [ ] Build succeeds locally
- [ ] `/health` endpoint returns correct status

---

## 🎯 **Why This Structure Works**

```python
# In main.py:
from bns_classifier import get_classifier  # ✅ Works because both in /app

# Docker structure:
/app/
  ├── main.py               # Entry point
  ├── bns_classifier.py    # Module (importable)
  └── data/
      └── bns_sections.csv  # Data (accessible via relative path)
```

**WORKDIR is `/app`** → All imports work from this directory
**uvicorn main:app** → Finds `app` in `main.py`
**Relative imports work** → Same directory structure

---

## 🆘 **Still Having Issues?**

1. **Check Render Logs:**
   - Dashboard → Your Service → Logs tab
   - Look for specific error messages

2. **Verify Files in Container:**
   ```bash
   # SSH into running container (if enabled)
   docker exec -it <container_id> ls -la /app
   ```

3. **Test Build Locally:**
   ```bash
   docker build -t test . && docker run test python -c "import bns_classifier"
   ```

4. **Check Environment:**
   ```bash
   docker run test env | grep GEMINI
   ```

---

**Deployment should now work successfully!** 🎉 for Render

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
