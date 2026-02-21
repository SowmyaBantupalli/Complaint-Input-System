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
