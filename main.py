# AI-Based Complaint Management System - Backend
# This FastAPI application provides AI-powered complaint analysis using Google Gemini
# Uses BNS dataset for intelligent legal classification
# Uses Tesseract OCR for handwritten complaint digitization

from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import re
from difflib import SequenceMatcher
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


def _normalize_for_similarity(text: str) -> str:
    """Normalize text for a rough similarity comparison (OCR vs typed)."""
    if not text:
        return ""
    lowered = text.lower()
    # Keep letters/numbers, normalize whitespace
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def _token_set(text: str) -> set[str]:
    normalized = _normalize_for_similarity(text)
    tokens = {t for t in normalized.split() if len(t) >= 4}
    return tokens


def _compute_text_similarity(a: str, b: str) -> float:
    """Compute a similarity score in [0, 1] for two texts."""
    a_norm = _normalize_for_similarity(a)
    b_norm = _normalize_for_similarity(b)
    if not a_norm or not b_norm:
        return 0.0

    seq_ratio = SequenceMatcher(None, a_norm, b_norm).ratio()

    a_tokens = _token_set(a_norm)
    b_tokens = _token_set(b_norm)
    if not a_tokens or not b_tokens:
        jaccard = 0.0
    else:
        inter = len(a_tokens & b_tokens)
        union = len(a_tokens | b_tokens)
        jaccard = inter / union if union else 0.0

    # Weighted blend (SequenceMatcher handles OCR noise fairly well; Jaccard adds keyword overlap signal)
    return (0.65 * seq_ratio) + (0.35 * jaccard)


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
    typed_text = (complaint or "").strip()
    extracted_text = None

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
        extracted_text = extract_text_from_image(image_bytes)
        
        # Check for Tesseract installation issues
        if extracted_text == "TESSERACT_NOT_INSTALLED":
            return JSONResponse(
                status_code=503,
                content={
                    "status": "error",
                    "detail": "OCR is not available on this server. Tesseract OCR is not installed. Please use Docker deployment or deploy to a platform that supports system packages. For now, please use text input instead of image upload."
                }
            )
        
        # Check if OCR encountered errors
        if extracted_text.startswith("OCR_ERROR"):
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "detail": f"OCR processing failed: {extracted_text.replace('OCR_ERROR: ', '')}. Please try again or use text input."
                }
            )
        
        # Check if no text was detected
        if extracted_text == "No text detected in image":
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "detail": "No text detected in image. Please ensure the image contains clear, readable text."
                }
            )
        
        # If extracted text is too short, it might be a bad scan
        if len(extracted_text.strip()) < 10:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "detail": "Could not extract enough text from image. Please ensure the image is clear and contains readable text."
                }
            )

    if not typed_text and not extracted_text:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "detail": "Please provide complaint text or upload an image."
            }
        )

    # If both typed text and image are provided, verify they refer to the same complaint.
    consistency = {
        "typed_provided": bool(typed_text),
        "image_provided": bool(extracted_text),
        "match_score": None,
        "matched": None,
    }

    if typed_text and extracted_text:
        # Only enforce mismatch if both inputs are substantive; allow short typed summaries.
        typed_tokens = _token_set(typed_text)
        ocr_tokens = _token_set(extracted_text)
        is_substantive = (len(typed_text) >= 60 and len(extracted_text) >= 60 and len(typed_tokens) >= 8 and len(ocr_tokens) >= 8)

        score = _compute_text_similarity(typed_text, extracted_text)
        consistency["match_score"] = round(score, 3)

        # Conservative thresholds to avoid false mismatches with noisy OCR
        matched = True
        if is_substantive:
            matched = score >= 0.45

        consistency["matched"] = matched

        if not matched:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "detail": "The typed complaint details do not appear to correspond to the attached written complaint. Please ensure both inputs describe the same incident, or submit only one input.",
                    "consistency": consistency,
                },
            )

        # Combine both for analysis as a whole (keep typed text first; append OCR text).
        text_to_analyze = (
            f"Typed complaint details:\n{typed_text}\n\n"
            f"Extracted text from attached image:\n{extracted_text}"
        )
    elif extracted_text:
        text_to_analyze = extracted_text
        consistency["matched"] = None
    else:
        text_to_analyze = typed_text
        consistency["matched"] = None

    # MODULE 3: AI-Powered Classification using Gemini and BNS dataset
    try:
        classifier = get_classifier()
        analysis = classifier.classify_complaint(text_to_analyze)
        
        # Return success status with analysis results
        return {
            "status": "ok",
            "extracted_text": extracted_text if image else None,
            "consistency": consistency,
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
