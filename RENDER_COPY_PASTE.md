# 🎯 QUICK SETUP - Copy & Paste for Render

## Your Gemini API Key
**Paste this in Render Environment Variables:**

```
Variable Name: GEMINI_API_KEY
Variable Value: [YOUR_API_KEY_HERE]
```

Get your key: https://makersuite.google.com/app/apikey

---

## Render Service Configuration

### **Build Command:**
```bash
pip install -r requirements.txt
```

### **Start Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### **Runtime:**
```
Python 3
```

### **Branch:**
```
main
```

---

## After Deployment - Verify These URLs

Replace `your-service-name` with your actual Render service name:

### 1. Health Check
```
https://your-service-name.onrender.com/health
```
**Must show:**
- `"gemini_api": "active"` ✅
- `"bns_dataset": "loaded"` ✅

### 2. Service Info
```
https://your-service-name.onrender.com/
```
**Must show:**
- `"ai_enabled": true` ✅
- `"bns_sections_loaded": 1530` ✅

### 3. Test Classification
```bash
curl -X POST https://your-service-name.onrender.com/analyze \
  -F "complaint=Someone stole my phone yesterday"
```
**Must show:**
- `"ai_powered": true` ✅
- `"crime_type": "Theft"` ✅
- `"predicted_section": "Section 303..."` ✅

---

## Frontend Update

Update your frontend backend URL:

**Vercel Environment Variable:**
```
Name: VITE_BACKEND_URL
Value: https://your-service-name.onrender.com
```

**Local Development (.env.local):**
```
VITE_BACKEND_URL=https://your-service-name.onrender.com
```

---

## ✅ Success Checklist

- [ ] Gemini API key obtained
- [ ] API key added to Render environment variables
- [ ] Service deployed (green status)
- [ ] `/health` shows Gemini active
- [ ] Test classification works
- [ ] `ai_powered: true` in response
- [ ] Frontend connected to backend

---

## 🚨 If Something's Wrong

### Gemini Not Active
```
Check: Render → Environment tab → GEMINI_API_KEY exists
Fix: Add the variable, save (auto-redeploys)
```

### BNS Not Loaded
```
Check: data/bns_sections.csv in repository
Fix: Commit the file, push to GitHub
```

### Service Won't Start
```
Check: Render logs (bottom of dashboard)
Common: Missing dependencies, wrong start command
Fix: Verify commands above, check logs for specific error
```

---

## 📊 Expected Response Format

```json
{
  "status": "ok",
  "ai_powered": true,
  "crime_type": "Theft",
  "location": "Market Street",
  "date": "Yesterday",
  "time": "8 PM",
  "persons_involved": "Unknown person",
  "key_event_summary": "Phone stolen from victim",
  "predicted_section": "Section 303: Theft offense",
  "bns_sections": [
    {"section": "303", "reason": "Theft of personal property"}
  ],
  "severity": "Medium",
  "additional_notes": "File FIR immediately"
}
```

---

## 💡 Important Notes

1. **Free Tier Limit:** 1500 AI requests/day (plenty for testing)
2. **Sleep Mode:** Render free tier sleeps after 15 min (first request slower)
3. **No Credit Card:** Everything is FREE ✅
4. **Security:** API key never exposed to frontend/users
5. **Fallback:** If Gemini quota exceeded → rule-based still works

---

## 🔗 Quick Links

- **Get API Key:** https://makersuite.google.com/app/apikey
- **Render Dashboard:** https://dashboard.render.com
- **API Documentation:** `your-service.onrender.com/docs`
- **Health Check:** `your-service.onrender.com/health`

---

**You're all set! Deploy and test.** 🚀
