# AI-Based Complaint Management System - Backend
# This FastAPI application provides a rule-based NLP system for complaint analysis
# Uses Tesseract OCR for handwritten complaint digitization

from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import re
import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageEnhance
import io

app = FastAPI(title="Complaint Analyzer Demo")

# Enable CORS to allow frontend (on different domain) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        return f"Error processing image: {str(e)}"


# MODULE 4: Legal Section (BNS/BNSS) Classification
# This function uses rule-based mapping to classify crimes into BNS sections
# Input: crime_type (from Module 3) and summary text
# Output: BNS section and optional special note
def classify_legal_section(crime_type: str, summary: str) -> tuple[str, str | None]:
    # Dictionary-based mapping: crime type → BNS section
    # This is NOT machine learning - just a lookup table
    law_map = {
        "Theft": "BNS Section 303",
        "Threat": "BNS Section 351",
        "Assault": "BNS Section 115",
    }

    lowered_summary = summary.lower()
    
    # Rule-based escalation: Check for weapon keywords in summary
    # If weapon mentioned → escalate to aggravated assault
    if "weapon" in lowered_summary or "knife" in lowered_summary:
        return "Aggravated Assault – BNS Section 118", "Weapon reference escalates the charge."

    # Additional rule: Flag minor theft cases for review
    note = None
    if "minor" in lowered_summary and "theft" in lowered_summary:
        note = "Minor theft noted; monitor for follow-up."

    # Default: Return mapped section or "Section Not Found" for unknown crimes
    predicted_section = law_map.get(crime_type, "Section Not Found")
    return predicted_section, note


# MODULE 3: Rule-Based NLP Analysis
# This function extracts crime type, time, and summary from complaint text
# Uses simple keyword matching and regex - NO machine learning
def analyze_complaint(text: str) -> dict:
    # Step 1: Crime Type Detection using keyword matching
    lowered = text.lower()
    if "theft" in lowered or "stole" in lowered:
        crime_type = "Theft"
    elif "threat" in lowered:
        crime_type = "Threat"
    elif "assault" in lowered:
        crime_type = "Assault"
    else:
        crime_type = "Unknown"  # No keywords matched

    # Step 2: Time Extraction using Regular Expression
    # Pattern matches: "8 PM", "10am", "3 PM" etc.
    time_match = re.search(r"\b\d{1,2}\s*(?:am|pm|AM|PM)\b", text)
    time = time_match.group(0) if time_match else "Not provided"

    # Step 3: Location Extraction using keyword-based approach
    # Look for location indicators like "at", "near", "in", "on" followed by place names
    location = "Not specified"
    
    # Try multiple patterns for location extraction
    location_patterns = [
        r"(?:at|near|in|on|from|around|outside|inside)\s+(?:the\s+)?([a-zA-Z0-9\s]+?(?:park|street|road|avenue|mall|store|shop|building|station|market|center|campus|school|college|temple|mosque|church|hospital))",
        r"(?:at|near|in|on)\s+(?:the\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})",
        r"(?:at|near|in|on)\s+([a-z]+\s+[a-z]+)",
    ]
    
    for pattern in location_patterns:
        loc_match = re.search(pattern, text, re.IGNORECASE)
        if loc_match:
            found_location = loc_match.group(1).strip()
            # Clean up and validate
            if len(found_location) > 2 and len(found_location) < 50:
                location = found_location.title()
                break
    
    # Step 4: Persons Involved - Extract names or person descriptors
    persons_involved = "Not mentioned"
    
    # First, check for person descriptors (suspect, victim, etc.)
    descriptor_pattern = r"\b(suspect|victim|witness|accused|attacker|perpetrator|thief|criminal)\b"
    descriptor_match = re.search(descriptor_pattern, lowered)
    
    if descriptor_match:
        persons_involved = descriptor_match.group(1).capitalize()
    else:
        # Look for capitalized proper names (2-3 word names)
        name_pattern = r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,2})\b"
        name_matches = re.findall(name_pattern, text)
        
        # Filter out common words that aren't names
        excluded_words = {
            "Someone", "Something", "Anyone", "The", "This", "That", "These", "Those",
            "What", "When", "Where", "Which", "Who", "Why", "How",
            "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
            "January", "February", "March", "April", "May", "June", "July", "August", 
            "September", "October", "November", "December",
            "Police", "Section", "Complaint", "Officer"
        }
        
        valid_names = []
        for name in name_matches:
            words = name.split()
            # Check if any word in the name is in excluded list
            if not any(word in excluded_words for word in words):
                # Verify it's not a common word by checking length and structure
                if len(name) >= 3 and len(words) <= 3:
                    valid_names.append(name)
        
        if valid_names:
            # Take up to 2 most unique names
            unique_names = list(dict.fromkeys(valid_names))[:2]
            persons_involved = ", ".join(unique_names)
        elif "someone" in lowered or "somebody" in lowered:
            persons_involved = "Unknown person"

    # Step 5: Key Event Extraction - identify main action
    # Look for action verbs and their context
    key_event = "Not identified"
    event_patterns = [
        r"(stole\s+(?:my|a|the)\s+\w+)",
        r"(threatened\s+(?:me|us|to|with)\s+[\w\s]+)",
        r"(assaulted\s+(?:me|us|someone))",
        r"(broke\s+(?:into|the|my)\s+\w+)",
        r"(attacked\s+(?:me|us|someone))",
    ]
    for pattern in event_patterns:
        event_match = re.search(pattern, lowered)
        if event_match:
            key_event = event_match.group(1).capitalize()
            break
    
    # If no specific pattern, extract first sentence as key event
    if key_event == "Not identified":
        first_sentence = re.split(r'[.!?]', text)[0].strip()
        if len(first_sentence) > 10:
            key_event = first_sentence[:80] + "..." if len(first_sentence) > 80 else first_sentence

    # Step 6: Generate summary (first 150 characters)
    summary = (text.strip()[:150]).rstrip()

    # Step 7: Call Module 4 to get BNS legal section
    predicted_section, special_note = classify_legal_section(crime_type, summary)

    # Return structured JSON response
    return {
        "crime_type": crime_type,
        "location": location,
        "time": time,
        "persons_involved": persons_involved,
        "key_event": key_event,
        "summary": summary,
        "predicted_section": predicted_section,
        "special_note": special_note,
    }


# MODULE 1 & 2: Complaint Input Endpoint
# Accepts either text input or image upload with real OCR processing
@app.post("/analyze")
async def handle_analyze(
    complaint: str = Form(None),  # Optional text input
    image: UploadFile | None = File(None),  # Optional image file
):
    # MODULE 2: Real OCR Implementation
    if image:
        # Read image file bytes
        image_bytes = await image.read()
        
        # Validate image file
        if not image.content_type or not image.content_type.startswith('image/'):
            return {
                "status": "error",
                "detail": "Invalid file type. Please upload an image file."
            }
        
        # Extract text using OCR with preprocessing
        text_to_analyze = extract_text_from_image(image_bytes)
        
        # Check if OCR successfully extracted text
        if text_to_analyze.startswith("Error") or text_to_analyze == "No text detected in image":
            return {
                "status": "error",
                "detail": text_to_analyze
            }
        
        # If extracted text is too short, it might be a bad scan
        if len(text_to_analyze.strip()) < 10:
            return {
                "status": "error",
                "detail": "Could not extract enough text from image. Please ensure the image is clear and contains readable text."
            }
            
    elif complaint:
        text_to_analyze = complaint
    else:
        return {"status": "error", "detail": "Provide complaint text or image."}

    # Call Module 3 to analyze the complaint
    analysis = analyze_complaint(text_to_analyze)
    
    # Return success status with analysis results
    # Include extracted_text field to show what OCR detected
    return {
        "status": "ok",
        "extracted_text": text_to_analyze if image else None,
        **analysis
    }
