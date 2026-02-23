# AI-Based Complaint Management System - Backend
# This FastAPI application provides AI-powered complaint analysis using Google Gemini
# Uses BNS dataset for intelligent legal classification
# Uses Tesseract OCR for handwritten complaint digitization

from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import re
import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import io
import os
import platform
from bns_classifier import get_classifier

app = FastAPI(
    title="AI Complaint Analyzer",
    description="Intelligent complaint classification using Google Gemini and BNS dataset",
    version="2.0.0"
)

# Configure Tesseract path for different environments
# This handles Windows installations where Tesseract may not be in PATH
if platform.system() == "Windows":
    # Common Windows installation paths
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv("USERNAME", "")),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            print(f"Tesseract found at: {path}")
            break
else:
    # On Linux/Render, Tesseract should be in PATH via Aptfile
    print("Running on Linux - Tesseract should be installed via Aptfile")

# Enable CORS to allow frontend (on different domain) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize BNS Classifier on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the BNS classifier when the app starts"""
    classifier = get_classifier()
    if classifier.is_initialized:
        print("🚀 AI-powered complaint analyzer ready with Gemini API")
    else:
        print("⚠️ Running in fallback mode - set GEMINI_API_KEY environment variable for AI features")


@app.get("/")
async def root():
    """Health check and API info endpoint"""
    classifier = get_classifier()
    return {
        "status": "online",
        "service": "AI Complaint Analyzer",
        "version": "2.0.0",
        "ai_enabled": classifier.is_initialized,
        "bns_sections_loaded": len(classifier.bns_data) if classifier.bns_data is not None else 0,
        "engine": "Google Gemini 1.5 Flash" if classifier.is_initialized else "Rule-based fallback"
    }


@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    classifier = get_classifier()
    return {
        "status": "healthy",
        "gemini_api": "active" if classifier.is_initialized else "not configured",
        "gemini_model": classifier.model_name if getattr(classifier, "model_name", None) else None,
        "bns_dataset": "loaded" if classifier.bns_data is not None else "error",
        "ocr_engine": "tesseract" if check_tesseract_available() else "unavailable"
    }


def check_tesseract_available() -> bool:
    """Check if Tesseract OCR is available"""
    try:
        pytesseract.get_tesseract_version()
        return True
    except:
        return False


# MODULE 2: Image Preprocessing for OCR
# Enhances image quality for better text extraction
def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Preprocesses uploaded image to improve OCR accuracy:
    1. Convert to grayscale
    2. Remove noise using bilateral filter
    3. Enhance contrast
    4. Apply adaptive thresholding for better text clarity
    
    Args:
        image_bytes: Raw image file bytes
    
    Returns:
        Preprocessed image as numpy array
    """
    # Convert bytes to PIL Image
    pil_image = Image.open(io.BytesIO(image_bytes))
    
    # Enhance contrast using PIL
    enhancer = ImageEnhance.Contrast(pil_image)
    pil_image = enhancer.enhance(2.0)  # Increase contrast by 2x
    
    # Convert PIL image to numpy array for OpenCV processing
    img_array = np.array(pil_image)
    
    # Convert to grayscale if image is in color
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply bilateral filter to remove noise while preserving edges
    # This is crucial for handwritten text
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Apply adaptive thresholding to make text stand out
    # This converts image to black and white, making text clearer
    thresh = cv2.adaptiveThreshold(
        denoised, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        11, 2
    )
    
    return thresh


# MODULE 2: OCR Text Extraction
# Extracts text from preprocessed image using Tesseract OCR
def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extracts text from handwritten complaint image using Tesseract OCR.
    
    Process:
    1. Preprocess image (noise removal, contrast enhancement)
    2. Run Tesseract OCR to detect and extract text
    3. Clean and return the extracted text
    
    Args:
        image_bytes: Raw image file bytes
    
    Returns:
        Extracted text string
    """
    try:
        # Check if Tesseract is available
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            # Tesseract not installed - return informative error
            return "TESSERACT_NOT_INSTALLED"
        
        # Preprocess the image for better OCR accuracy
        preprocessed_img = preprocess_image(image_bytes)
        
        # Convert numpy array to PIL Image for pytesseract
        pil_img = Image.fromarray(preprocessed_img)
        
        # Use Tesseract to extract text
        # PSM 6 = Assume a single uniform block of text
        # --oem 3 = Default OCR Engine Mode (LSTM neural network)
        custom_config = r'--oem 3 --psm 6'
        extracted_text = pytesseract.image_to_string(pil_img, config=custom_config)
        
        # Clean up the text
        extracted_text = " ".join(extracted_text.split())
        
        return extracted_text if extracted_text.strip() else "No text detected in image"
        
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return f"OCR_ERROR: {str(e)}"


# MODULE 1 & 2: Complaint Input and Analysis Endpoint
# Accepts either text input or image upload with real OCR processing
# Uses Gemini AI for intelligent classification
@app.post("/analyze")
async def handle_analyze(
    complaint: str = Form(None),  # Optional text input
    image: UploadFile | None = File(None),  # Optional image file
):
    """
    Analyze complaint using AI and BNS dataset
    
    Accepts:
    - Text complaint (typed by user)
    - Image complaint (handwritten, processed via OCR)
    
    Returns:
    - Structured JSON with crime classification, BNS sections, and extracted details
    """
    # MODULE 2: Real OCR Implementation
    if image:
        # Read image file bytes
        image_bytes = await image.read()
        
        # Validate image file
        if not image.content_type or not image.content_type.startswith('image/'):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "detail": "Invalid file type. Please upload an image file."
                }
            )
        
        # Extract text using OCR with preprocessing
        text_to_analyze = extract_text_from_image(image_bytes)
        
        # Check for Tesseract installation issues
        if text_to_analyze == "TESSERACT_NOT_INSTALLED":
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "detail": "OCR is not available on this server. Tesseract OCR is not installed. Please use Docker deployment or deploy to a platform that supports system packages. For now, please use text input instead of image upload."
                }
            )
        
        # Check if OCR encountered errors
        if text_to_analyze.startswith("OCR_ERROR"):
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "detail": f"OCR processing failed: {text_to_analyze.replace('OCR_ERROR: ', '')}. Please try again or use text input."
                }
            )
        
        # Check if no text was detected
        if text_to_analyze == "No text detected in image":
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "detail": "No text detected in image. Please ensure the image contains clear, readable text."
                }
            )
        
        # If extracted text is too short, it might be a bad scan
        if len(text_to_analyze.strip()) < 10:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "detail": "Could not extract enough text from image. Please ensure the image is clear and contains readable text."
                }
            )
            
    elif complaint:
        text_to_analyze = complaint
    else:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "detail": "Provide complaint text or image."
            }
        )

    # MODULE 3: AI-Powered Classification using Gemini and BNS dataset
    try:
        classifier = get_classifier()
        analysis = classifier.classify_complaint(text_to_analyze)
        
        # Return success status with analysis results
        return {
            "status": "ok",
            "extracted_text": text_to_analyze if image else None,
            "ai_powered": analysis.get("ai_classification", False),
            **analysis
        }
        
    except Exception as e:
        print(f"❌ Classification error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "detail": f"Error analyzing complaint: {str(e)}"
            }
        )
