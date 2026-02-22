# AI-Based Complaint Management System

## Project Overview
This is a production-ready complaint intake platform built for academic purposes. Users submit either text or an image (handwritten or printed) to describe an incident, and the backend analyzes the content with OCR and rule-based NLP to extract the crime type, location, time, persons involved, and the corresponding BNS legal section.

## Features
- ✅ **Real OCR Implementation**: Extracts text from handwritten/printed complaints using Tesseract OCR
- ✅ **Image Preprocessing**: Automatic noise removal, contrast enhancement, and thresholding for better OCR accuracy
- ✅ **Text Input Support**: Direct text entry for typed complaints
- ✅ **Rule-Based NLP**: Extracts crime type, location, time, persons involved, and key events
- ✅ **Legal Classification**: Maps complaints to BNS legal sections with escalation rules
- ✅ **Interactive UI**: Clean React-based interface with real-time analysis
- ✅ **Deployment-Ready**: Lightweight dependencies suitable for free hosting tiers

## System Architecture
- **Frontend**: Vite + React app that submits multipart form data with text or an image, then displays the returned analysis.
- **Backend**: FastAPI + Uvicorn server with Tesseract OCR for text extraction, image preprocessing with OpenCV and PIL, and rule-based NLP/classification.

## Module Explanation
- **Module 1: Complaint Input** – `ComplaintForm` captures the complaint story or image upload, and submits them via `fetch` using `FormData`.
- **Module 2: Handwritten Complaint Digitization (OCR)** – Real OCR implementation:
  - **Preprocessing**: Noise removal using bilateral filter, contrast enhancement, grayscale conversion, and adaptive thresholding
  - **Text Extraction**: Tesseract OCR engine extracts text from handwritten/printed images
  - **Validation**: Text length and quality validation
- **Module 3: Rule-Based NLP** – `analyze_complaint` extracts:
  - Crime type (theft, threat, assault)
  - Location (using pattern matching)
  - Time (regex for time formats)
  - Persons involved (name extraction and role detection)
  - Key events (action verb extraction)
- **Module 4: Legal Section Classification** – `classify_legal_section` maps crime types to BNS sections with escalation rules for weapons and special notes for minor theft.

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

#### 1. Install Python dependencies
```bash
# Install all required dependencies
pip install -r requirements.txt

# This will install:
# - FastAPI (web framework)
# - Uvicorn (ASGI server)
# - pytesseract (OCR Python wrapper)
# - OpenCV (image processing)
# - Pillow (image enhancement)
# - NumPy (array operations)
```

#### 2. Install Tesseract OCR Engine

**Windows:**
```bash
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
# Or use chocolatey:
choco install tesseract

# Add Tesseract to PATH or set in code:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

**Linux/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng libtesseract-dev
```

**macOS:**
```bash
brew install tesseract
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

**Important**: The `Aptfile` in the repository tells Render to automatically install Tesseract OCR engine during deployment.

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

## OCR Usage & Best Practices

### Using Image Upload
1. **Supported Formats**: JPG, PNG, JPEG, BMP, TIFF
2. **Image Quality Tips**:
   - ✅ Good lighting with no shadows
   - ✅ Clear, legible handwriting
   - ✅ High contrast (dark text on light background)
   - ✅ Flat paper (no wrinkles or folds)
   - ✅ Straight orientation (not tilted)
   - ❌ Avoid blurry or low-resolution images
   - ❌ Avoid images with complex backgrounds

### OCR Processing
The system automatically:
1. Enhances image contrast (2x)
2. Converts to grayscale
3. Removes noise using bilateral filtering
4. Applies adaptive thresholding for text clarity
5. Extracts text using Tesseract OCR engine (LSTM mode)
6. Cleans and validates the extracted text

### Expected Response
```json
{
  "status": "ok",
  "extracted_text": "Text detected from your image",
  "crime_type": "Theft",
  "location": "Central Park",
  "time": "8 PM",
  "persons_involved": "Unknown person",
  "key_event": "Stole my bike",
  "summary": "...",
  "predicted_section": "BNS Section 303",
  "special_note": null
}
```

**Note**: OCR processing typically takes 2-5 seconds per image.

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
