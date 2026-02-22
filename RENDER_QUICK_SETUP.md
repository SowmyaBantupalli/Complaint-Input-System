# 🚀 Quick Render Deployment Guide with Gemini API

## Step-by-Step Setup (5 minutes)

### 1️⃣ Get Your FREE Gemini API Key

1. Go to: **https://makersuite.google.com/app/apikey**
2. Sign in with Google account
3. Click **"Create API Key"**
4. Copy the key (format: `AIzaSy...`)
5. **IMPORTANT:** Keep this key private!

---

### 2️⃣ Deploy to Render

#### First-Time Deployment:

1. **Go to Render Dashboard** → https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. **Connect Repository:**
   - Click "Connect GitHub"
   - Select your `Complaint-Input-System` repository
4. **Configure Service:**
   - **Name:** `complaint-analyzer-backend` (or your choice)
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Root Directory:** Leave blank (or `.`)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Select Free Plan** ✅ FREE
6. **Advanced Settings** → Click "Add Environment Variable"
   
   **CRITICAL STEP:**
   ```
   Key: GEMINI_API_KEY
   Value: [paste your API key here - no quotes]
   ```
   
7. Click **"Create Web Service"**
8. **Wait 3-5 minutes** for deployment to complete

---

### 3️⃣ Verify Deployment

Once deployed, your service URL will be:
```
https://your-service-name.onrender.com
```

**Test it:**

1. **Check Health:**
   ```
   https://your-service-name.onrender.com/health
   ```
   
   Expected response:
   ```json
   {
     "status": "healthy",
     "gemini_api": "active",  ✅ Must say "active"
     "bns_dataset": "loaded",
     "ocr_engine": "tesseract"
   }
   ```

2. **Check Service Info:**
   ```
   https://your-service-name.onrender.com/
   ```
   
   Expected response:
   ```json
   {
     "status": "online",
     "ai_enabled": true,  ✅ Must be true
     "bns_sections_loaded": 1530,  ✅ Should be > 0
     "engine": "Google Gemini 1.5 Flash"
   }
   ```

3. **Test Classification:**
   Use API testing tool (Postman, Thunder Client, or curl):
   ```bash
   curl -X POST https://your-service-name.onrender.com/analyze \
     -F "complaint=Someone stole my phone yesterday at 8 PM"
   ```

---

### 4️⃣ Update Frontend

Update your frontend's environment variable:

**In Vercel:**
1. Go to Project Settings → Environment Variables
2. Edit `VITE_BACKEND_URL`
3. Set value to: `https://your-service-name.onrender.com`
4. Save and redeploy

**In local dev:**
Create `frontend/.env.local`:
```
VITE_BACKEND_URL=https://your-service-name.onrender.com
```

---

## ✅ Deployment Checklist

- [ ] Gemini API key obtained from Google AI Studio
- [ ] Repository connected to Render
- [ ] Environment variable `GEMINI_API_KEY` added
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Service deployed successfully (green status)
- [ ] `/health` returns `gemini_api: "active"`
- [ ] `/` returns `ai_enabled: true`
- [ ] Test complaint classification works
- [ ] Frontend updated with backend URL

---

## 🔧 If Something Goes Wrong

### Issue: `gemini_api: "not configured"`

**Fix:**
1. Go to Render Dashboard → Your Service → "Environment"
2. Check if `GEMINI_API_KEY` exists
3. If missing, add it (see Step 2️⃣)
4. If exists, verify no typos in key name
5. Click "Save" (auto-redeploys)

### Issue: `ai_enabled: false`

**Fix:**
1. Check Render logs for errors
2. Verify API key is valid at Google AI Studio
3. Regenerate key if needed
4. Update in Render environment variables
5. Trigger manual redeploy

### Issue: `bns_sections_loaded: 0`

**Fix:**
1. Ensure `data/bns_sections.csv` is in repository
2. Check Render logs for file errors
3. Verify file is not in `.gitignore`
4. Commit and push if missing

### Issue: Service won't start

**Fix:**
1. Check Render logs (bottom of dashboard)
2. Common issues:
   - Missing dependency in `requirements.txt`
   - Syntax error in code
   - Port binding issue (should use `$PORT`)
3. Fix in code, commit, push (auto-redeploys)

---

## 📊 Monitoring Your Service

**Check these regularly:**
- **Logs:** Render Dashboard → Logs tab
- **Health:** `https://your-service.onrender.com/health`
- **Uptime:** Render shows service status
- **API Usage:** Google AI Studio dashboard

---

## 💡 Pro Tips

1. **Free tier sleeps after 15 min inactivity** - first request after sleep takes ~30 seconds
2. **Keep service alive** - set up UptimeRobot (free) to ping every 5 minutes
3. **Monitor Gemini quota** - 1500 requests/day free
4. **Check logs weekly** for any errors
5. **Test after each deployment** using `/health` endpoint

---

## 🆘 Quick Support Links

- **Gemini API Key:** https://makersuite.google.com/app/apikey
- **Render Dashboard:** https://dashboard.render.com
- **Render Docs:** https://render.com/docs
- **Check Logs:** Dashboard → Your Service → Logs

---

## 🎉 You're All Set!

Your AI-powered complaint analyzer is now live:
- ✅ Gemini AI enabled
- ✅ 1530+ BNS sections loaded
- ✅ Intelligent classification working
- ✅ Zero cost deployment

**Next:** Test with real complaints and monitor accuracy!
