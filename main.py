from fastapi import FastAPI, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI(title="Complaint Analyzer Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def classify_legal_section(crime_type: str, summary: str) -> tuple[str, str | None]:
    # Base mapping keeps the classification simple and easy to explain.
    law_map = {
        "Theft": "BNS Section 303",
        "Threat": "BNS Section 351",
        "Assault": "BNS Section 115",
    }

    lowered_summary = summary.lower()
    # Escalate when a weapon is mentioned, rule-based without ML.
    if "weapon" in lowered_summary or "knife" in lowered_summary:
        return "Aggravated Assault – BNS Section 118", "Weapon reference escalates the charge."

    note = None
    if "minor" in lowered_summary and "theft" in lowered_summary:
        note = "Minor theft noted; monitor for follow-up."

    predicted_section = law_map.get(crime_type, "Section Not Found")
    return predicted_section, note


def analyze_complaint(text: str) -> dict:
    lowered = text.lower()
    if "theft" in lowered or "stole" in lowered:
        crime_type = "Theft"
    elif "threat" in lowered:
        crime_type = "Threat"
    elif "assault" in lowered:
        crime_type = "Assault"
    else:
        crime_type = "Unknown"

    time_match = re.search(r"\b\d{1,2}\s*(?:am|pm|AM|PM)\b", text)
    time = time_match.group(0) if time_match else "Not provided"

    summary = (text.strip()[:100]).rstrip()

    predicted_section, special_note = classify_legal_section(crime_type, summary)

    return {
        "crime_type": crime_type,
        "time": time,
        "summary": summary,
        "predicted_section": predicted_section,
        "special_note": special_note,
    }


@app.post("/analyze")
async def handle_analyze(
    complaint: str = Form(None),
    image: UploadFile | None = File(None),
):
    if image:
        text_to_analyze = "Someone stole my bike near the park at 8 PM"
    elif complaint:
        text_to_analyze = complaint
    else:
        return {"status": "bad_request", "detail": "Provide complaint text or image."}

    analysis = analyze_complaint(text_to_analyze)
    return {"status": "ok", **analysis}
