# Deployment Guide - AI-Powered Complaint Analyzer

## 🔑 Required Setup: Google Gemini API Key

### Step 1: Get Your Free Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key (format: `AIzaSy...`)
5. **Keep it secure - never commit it to git!**

**Free Tier Details:**
- ✅ 1500 requests per day (free)
- ✅ No credit card required
- ✅ Gemini 1.5 Flash model (fast & accurate)

---

## 🚀 Deployment Setup

### Render (Backend) - Environment Variables

**CRITICAL: Set environment variable before deploying**

1. Go to your Render dashboard
2. Select your web service
3. Navigate to "Environment" tab
4. Add the following environment variable:

```
Key: GEMINI_API_KEY
Value: your_actual_api_key_here (e.g., AIzaSyABC123...)
```

5. Click "Save Changes"
6. Render will automatically redeploy with the new variable

**Without this key:**
- ⚠️ AI classification will be disabled
- ⚠️ System will fall back to basic rule-based classification
- ⚠️ Accuracy will be significantly reduced

---

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
---

## 🔍 Troubleshooting Gemini API Integration

### How to Verify AI is Working

**Method 1: Check API Health Endpoint**
```bash
# Visit or curl this endpoint
https://your-backend-url.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "gemini_api": "active",  // ✅ Should say "active" not "not configured"
  "bns_dataset": "loaded",
  "ocr_engine": "tesseract"
}
```

**Method 2: Check Root Endpoint**
```bash
https://your-backend-url.onrender.com/
```

Expected response:
```json
{
  "status": "online",
  "ai_enabled": true,  // ✅ Should be true
  "bns_sections_loaded": 1530,  // ✅ Should show number > 0
  "engine": "Google Gemini 1.5 Flash"  // ✅ Should show Gemini
}
```

### Common Issues & Solutions

#### Issue 1: API Key Not Set
**Symptoms:**
- `ai_enabled: false` in response
- `engine: "Rule-based fallback"` 
- Less accurate results

**Solution:**
1. Go to Render Dashboard → Environment tab
2. Verify `GEMINI_API_KEY` is set correctly
3. No quotes or spaces around the key
4. Save and wait for auto-redeploy

#### Issue 2: Invalid API Key
**Symptoms:**
- Errors in Render logs mentioning "401" or "invalid API key"

**Solution:**
1. Verify your key at [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Generate a new key if needed
3. Update in Render environment variables
4. Redeploy

#### Issue 3: Rate Limit Exceeded
**Symptoms:**
- Errors mentioning "quota exceeded" or "429"

**Solution:**
- Free tier: 1500 requests/day
- Wait for quota reset (resets daily)
- Or upgrade to paid tier (if needed in production)

#### Issue 4: BNS Dataset Not Loading
**Symptoms:**
- `bns_sections_loaded: 0`

**Solution:**
- Check that `data/bns_sections.csv` is in your repository
- Verify file is not corrupted
- Check Render logs for file path errors

### Testing Locally with Gemini

1. Create `.env` file in project root:
```bash
GEMINI_API_KEY=your_key_here
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run backend:
```bash
uvicorn main:app --reload
```

4. Test at `http://localhost:8000/health`

### Monitoring Application Health

**Check these regularly:**
1. Response times (should be < 5 seconds for most complaints)
2. Error rates in Render logs
3. Gemini API usage (visit Google AI Studio dashboard)
4. Classification accuracy
5. Daily request count (stay under 1500 for free tier)

---

## 📊 Deployment Checklist

Before going live:
- [ ] Gemini API key set in Render environment variables
- [ ] `/health` endpoint returns `ai_enabled: true`
- [ ] BNS dataset loaded (1500+ sections)
- [ ] Frontend `VITE_BACKEND_URL` points to correct Render URL
- [ ] Test complaint submission end-to-end
- [ ] Verify structured JSON output is correct
- [ ] Check Tesseract OCR works (if using image upload)
- [ ] Review Render logs for any errors

---

## 🆘 Need Help?

1. **Check Render Logs**: Most issues show up here
2. **Test `/health` endpoint**: Quick diagnostic
3. **Verify environment variables**: Common mistake
4. **Check Gemini API dashboard**: Monitor usage/quotas