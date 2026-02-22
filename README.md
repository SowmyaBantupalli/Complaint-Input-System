# AI-Based Complaint Management System

## Project Overview
This is a demo-ready complaint intake platform built for academic purposes. Users submit either text or an image to describe an incident, and the backend analyzes the content with simple rule-based logic to surface the crime type, time, summary, and the corresponding BNS legal section.

## Features
- Accepts complaint text or optional image uploads (image path uses a mock text response).
- Performs lightweight rule-based NLP to detect crime types and extract reported time.
- Classifies complaints into BNS legal sections via a dictionary-based lookup, including rules that escalate based on key terms like `weapon` or `knife`.
- Returns structured JSON and presents the result in a beginner-friendly React card UI.

## System Architecture
- **Frontend**: Vite + React app that submits multipart form data with text or an image, then displays the returned analysis.
- **Backend**: FastAPI + Uvicorn server that parses the form, applies rule-based NLP/classification, and exposes `/analyze` with CORS enabled.

## Module Explanation
- **Module 1: Complaint Input** – `ComplaintForm` captures the complaint story, optional image, and submits them via `fetch` using `FormData`.
- **Module 2: OCR (Mock or Basic)** – Incoming image uploads are handled with a mocked text response (e.g., "Someone stole my bike…") to keep the demo simple while illustrating how OCR output would be used.
- **Module 3: Rule-Based NLP** – `analyze_complaint` checks for keywords (`theft`, `threat`, `assault`), runs a regex for times like `8 PM`, and creates a 100-character summary.
- **Module 4: Legal Section Classification** – `classify_legal_section` maps crime types to BNS sections, with extra rules for weapons (`knife`, `weapon`) to escalate to `Aggravated Assault – BNS Section 118` and small thefts to include a note.

## Folder Structure
```
Complaint Input System/
├── backend (root)
│   ├── main.py
│   └── requirements.txt
└── frontend/
    ├── package.json
    ├── src/
    │   ├── App.jsx
    │   ├── main.jsx
    │   ├── style.css
    │   └── components/
    │       ├── ComplaintForm.jsx
    │       └── ResultDisplay.jsx
    └── index.html
```

## Installation Instructions
### Backend setup
```bash
python -m pip install fastapi uvicorn python-multipart
```
### Frontend setup
```bash
cd frontend
npm install
```

### Environment Configuration
The frontend includes a `.env` file to configure the backend URL:
- **For local backend**: Change `VITE_BACKEND_URL` to `http://localhost:8000`
- **For production backend**: Use `https://complaint-input-system.onrender.com` (already set)

Edit `frontend/.env`:
```env
# Use local backend
VITE_BACKEND_URL=http://localhost:8000

# OR use production backend from local frontend
VITE_BACKEND_URL=https://complaint-input-system.onrender.com
```

## How to Run the Project

### Option 1: Run Both Frontend and Backend Locally
1. Start the backend:
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
2. Set `.env` to use local backend: `VITE_BACKEND_URL=http://localhost:8000`
3. Launch the frontend (from `frontend` directory):
   ```bash
   npm run dev -- --host 0.0.0.0 --port 5173
   ```
4. Open `http://localhost:5173/`, enter a complaint or upload an image, and submit.

### Option 2: Run Frontend Locally with Production Backend
1. Set `.env` to use production backend: `VITE_BACKEND_URL=https://complaint-input-system.onrender.com`
2. Launch the frontend:
   ```bash
   npm run dev -- --host 0.0.0.0 --port 5173
   ```
3. Open `http://localhost:5173/` - it will connect to the deployed backend

## Deployment
### Backend (Render)
✅ **Deployed**: https://complaint-input-system.onrender.com

**Steps to deploy:**
1. Create new **Web Service** on [Render](https://render.com)
2. Connect your GitHub repository
3. Configure service:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Deploy and note your backend URL

### Frontend (Vercel)
1. Go to [Vercel](https://vercel.com) and create new project
2. Import your GitHub repository
3. Configure project settings:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: Leave default or set to `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: Leave default or set to `npm install`
4. Add environment variable:
   - Name: `VITE_BACKEND_URL`
   - Value: `https://complaint-input-system.onrender.com` (without trailing slash)
5. Click "Deploy"

Your frontend will be available at the Vercel URL (e.g., `https://complaint-app.vercel.app`)

**Important Notes:**
- ⚠️ Do NOT add a trailing slash to `VITE_BACKEND_URL` (use `https://...com` not `https://...com/`)
- The code automatically handles URL formatting to prevent double slashes
- If you update environment variables in Vercel, trigger a new deployment for changes to take effect

**Troubleshooting**: If build fails, ensure Root Directory is set to `frontend` (not blank or root).

## Sample Input and Output
**Input (text form data):**
```
Someone stole my bike near the park at 8 PM and it had a small lock.
```
**Output (JSON):**
```json
{
  "status": "ok",
  "crime_type": "Theft",
  "time": "8 PM",
  "summary": "Someone stole my bike near the park at 8 PM and it had a small lock.",
  "predicted_section": "BNS Section 303",
  "special_note": "Minor theft noted; monitor for follow-up."
}
```

## Limitations
- Image handling uses a fixed mock string, so real OCR is not implemented.
- Crime detection relies on keyword matching; synonyms or complex phrasing may be missed.
- Time extraction only recognizes `hh AM/PM` formats.

## Future Enhancements
- Add optional OCR integration for real images.
- Expand the keyword set and basic text normalization for better NLP coverage.
- Store complaints temporarily (e.g., JSON file) to review past analyses.

## Author
- _Your Name Here_
