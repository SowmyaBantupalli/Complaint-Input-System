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

    section_map = {
        "Theft": "BNS Section 303",
        "Threat": "BNS Section 351",
        "Assault": "BNS Section 115",
    }
    predicted_section = section_map.get(crime_type, "Not assigned")

    return {
        "crime_type": crime_type,
        "time": time,
        "summary": summary,
        "predicted_section": predicted_section,
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
