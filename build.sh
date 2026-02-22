#!/usr/bin/env bash
# Build script for Render deployment
# Installs Python dependencies

set -e

echo "===== Build Starting ====="

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python packages..."
pip install -r requirements.txt

# Check if Tesseract is available (installed via Aptfile)
echo "Checking Tesseract installation..."
if command -v tesseract &> /dev/null; then
    echo "✓ Tesseract found:"
    tesseract --version
else
    echo "⚠ WARNING: Tesseract not found!"
    echo "Make sure Aptfile is in the root directory and contains:"
    echo "  tesseract-ocr"
    echo "  tesseract-ocr-eng"
fi

echo "===== Build Complete ====="
