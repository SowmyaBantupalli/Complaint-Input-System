# Tesseract Installation Guide for Windows

## Quick Installation (Recommended)

### Option 1: Using Chocolatey (Easiest)
```powershell
# Open PowerShell as Administrator
choco install tesseract

# Restart your terminal after installation
```

### Option 2: Manual Installation
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Choose: `tesseract-ocr-w64-setup-5.x.x.exe` (64-bit) or `tesseract-ocr-w32-setup-5.x.x.exe` (32-bit)
3. Run the installer
4. During installation, select "Add to PATH" option
5. Default installation path: `C:\Program Files\Tesseract-OCR\`
6. Restart your terminal/VS Code after installation

## Verify Installation

```powershell
# Check if tesseract is accessible
tesseract --version

# Should output something like:
# tesseract 5.x.x
```

## If "tesseract is not installed" Error Persists

### Manual PATH Configuration:
1. Right-click "This PC" → Properties
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "System variables", find "Path"
5. Click "Edit"
6. Click "New"
7. Add: `C:\Program Files\Tesseract-OCR`
8. Click OK on all dialogs
9. Restart VS Code and terminal

### Alternative: Set Path in Code (Already Done)
The code automatically checks these paths:
- `C:\Program Files\Tesseract-OCR\tesseract.exe`
- `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`
- `C:\Users\{USERNAME}\AppData\Local\Tesseract-OCR\tesseract.exe`

## Test OCR After Installation

```powershell
# Navigate to project directory
cd "E:\Dev Projects\Complaint Input System"

# Install Python dependencies
pip install -r requirements.txt

# Run the backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## For Render Deployment

No manual installation needed! The `Aptfile` automatically installs Tesseract on Render's servers during deployment.
