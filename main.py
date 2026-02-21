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

    # Step 3: Location Extraction using keyword-based approach
    # Look for location indicators like "at", "near", "in", "on" followed by place names
    location = "Not specified"
    location_patterns = [
        r"(?:at|near|in|on|from|around)\s+(?:the\s+)?([A-Z][a-zA-Z\s]+?)(?:\s+at|\s+near|\.|,|$)",
        r"(?:at|near|in|on)\s+([a-z]+(?:\s+[a-z]+){0,3})",
    ]
    for pattern in location_patterns:
        loc_match = re.search(pattern, text, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip()
            break
    
    # Step 4: Persons Involved using simple name pattern matching
    # Look for capitalized names or person descriptors
    persons = []
    # Pattern for capitalized names (e.g., "John Smith", "Maria")
    name_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b"
    name_matches = re.findall(name_pattern, text)
    # Filter out common words and location keywords
    common_words = {"Someone", "The", "At", "Near", "In", "On", "PM", "AM", "Section"}
    persons = [name for name in name_matches if name not in common_words][:3]  # Limit to 3 names
    
    # Also check for person descriptors
    descriptor_pattern = r"\b(suspect|victim|witness|accused|man|woman|person|individual|perpetrator)\b"
    descriptors = re.findall(descriptor_pattern, lowered)
    
    if persons:
        persons_involved = ", ".join(persons)
    elif descriptors:
        persons_involved = descriptors[0].capitalize()
    else:
        persons_involved = "Not mentioned"

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
