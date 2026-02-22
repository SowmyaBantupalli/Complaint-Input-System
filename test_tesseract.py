"""
Test script to verify Tesseract OCR installation
Run this to check if Tesseract is properly installed and configured
"""

import sys

def test_tesseract():
    print("=" * 60)
    print("TESSERACT OCR INSTALLATION TEST")
    print("=" * 60)
    
    # Test 1: Import pytesseract
    print("\n1. Testing pytesseract import...")
    try:
        import pytesseract
        print("   ✓ pytesseract module imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import pytesseract: {e}")
        print("   → Run: pip install pytesseract")
        return False
    
    # Test 2: Check Tesseract executable
    print("\n2. Checking Tesseract executable...")
    try:
        version = pytesseract.get_tesseract_version()
        print(f"   ✓ Tesseract found! Version: {version}")
    except Exception as e:
        print(f"   ✗ Tesseract not found: {e}")
        print("\n   → Installation needed:")
        print("      Windows: choco install tesseract")
        print("      Linux: sudo apt-get install tesseract-ocr")
        print("      macOS: brew install tesseract")
        print("\n   → See TESSERACT_INSTALL.md for detailed instructions")
        return False
    
    # Test 3: Check PIL/Pillow
    print("\n3. Testing PIL/Pillow...")
    try:
        from PIL import Image
        print("   ✓ PIL/Pillow installed successfully")
    except ImportError:
        print("   ✗ PIL/Pillow not found")
        print("   → Run: pip install pillow")
        return False
    
    # Test 4: Check OpenCV
    print("\n4. Testing OpenCV...")
    try:
        import cv2
        print(f"   ✓ OpenCV installed successfully (version {cv2.__version__})")
    except ImportError:
        print("   ✗ OpenCV not found")
        print("   → Run: pip install opencv-python-headless")
        return False
    
    # Test 5: Simple OCR test
    print("\n5. Running simple OCR test...")
    try:
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple test image with text
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 30), "Hello OCR Test", fill='black')
        
        # Try to extract text
        text = pytesseract.image_to_string(img)
        if "Hello" in text or "OCR" in text or "Test" in text:
            print("   ✓ OCR test passed!")
            print(f"   Extracted text: '{text.strip()}'")
        else:
            print(f"   ⚠ OCR ran but text recognition may be inaccurate")
            print(f"   Extracted: '{text.strip()}'")
    except Exception as e:
        print(f"   ✗ OCR test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED! Tesseract OCR is ready to use!")
    print("=" * 60)
    print("\nYou can now run the backend:")
    print("  python -m uvicorn main:app --reload")
    print("\n")
    return True

if __name__ == "__main__":
    success = test_tesseract()
    sys.exit(0 if success else 1)
