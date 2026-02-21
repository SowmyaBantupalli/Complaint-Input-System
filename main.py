# AI-Based Complaint Management System - Backend
# This FastAPI application provides a rule-based NLP system for complaint analysis
# No ML models or external APIs are used - purely dictionary and regex based

from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI(title="Complaint Analyzer Demo")

# Enable CORS to allow frontend (on different domain) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    # Step 3: Generate summary (first 100 characters)
    summary = (text.strip()[:100]).rstrip()

    # Step 4: Call Module 4 to get BNS legal section
    predicted_section, special_note = classify_legal_section(crime_type, summary)

    # Return structured JSON response
    return {
        "crime_type": crime_type,
        "time": time,
        "summary": summary,
        "predicted_section": predicted_section,
        "special_note": special_note,
    }


# MODULE 1 & 2: Complaint Input Endpoint
# Accepts either text input or image upload (image uses mock OCR)
@app.post("/analyze")
async def handle_analyze(
    complaint: str = Form(None),  # Optional text input
    image: UploadFile | None = File(None),  # Optional image file
):
    # MODULE 2: Mock OCR - In real system, this would use OCR library
    # For demo purposes, we return a fixed sample text when image is uploaded
    if image:
        text_to_analyze = "Someone stole my bike near the park at 8 PM"
    elif complaint:
        text_to_analyze = complaint
    else:
        return {"status": "bad_request", "detail": "Provide complaint text or image."}

    # Call Module 3 to analyze the complaint
    analysis = analyze_complaint(text_to_analyze)
    
    # Return success status with analysis results
    return {"status": "ok", **analysis}
