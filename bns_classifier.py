"""
BNS Classification Module using Google Gemini API
This module loads the BNS dataset and uses Gemini AI to intelligently classify complaints
"""

import os
import pandas as pd
import google.generativeai as genai
from typing import Optional, Dict
import json

class BNSClassifier:
    """Intelligent complaint classifier using Gemini API and BNS dataset"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the BNS classifier with Gemini API
        
        Args:
            api_key: Google Gemini API key (if None, reads from GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.bns_data = None
        self.model = None
        self.is_initialized = False
        
        # Load BNS dataset
        self._load_bns_data()
        
        # Initialize Gemini if API key is available
        if self.api_key:
            self._initialize_gemini()
        else:
            print("⚠️ Warning: GEMINI_API_KEY not found. AI classification will be unavailable.")
    
    def _load_bns_data(self):
        """Load BNS sections from CSV file"""
        try:
            csv_path = os.path.join(os.path.dirname(__file__), "data", "bns_sections.csv")
            self.bns_data = pd.read_csv(csv_path)
            print(f"✅ Loaded {len(self.bns_data)} BNS sections from dataset")
        except Exception as e:
            print(f"❌ Error loading BNS dataset: {e}")
            self.bns_data = None
    
    def _initialize_gemini(self):
        """Configure Gemini API"""
        try:
            genai.configure(api_key=self.api_key)
            
            # Use Gemini 1.5 Flash (free tier, fast, good for structured output)
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "temperature": 0.2,  # Low temperature for consistent, factual outputs
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            self.is_initialized = True
            print("✅ Gemini API initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing Gemini: {e}")
            self.is_initialized = False
    
    def _build_bns_context(self, max_sections: int = 50) -> str:
        """
        Build a condensed BNS context for the prompt
        
        Args:
            max_sections: Maximum number of sections to include (to avoid token limits)
        
        Returns:
            Formatted string with BNS sections
        """
        if self.bns_data is None or self.bns_data.empty:
            return "BNS dataset not available"
        
        # Focus on criminal offense sections (typically chapters 5-23 in BNS)
        # Filter relevant chapters for common crimes
        relevant_chapters = ["OF OFFENCES", "OF CRIMES", "THEFT", "ASSAULT", 
                            "CRIMINAL", "VIOLENCE", "THREAT", "ROBBERY", 
                            "BURGLARY", "HARASSMENT", "FRAUD", "HURT",
                            "WRONGFUL", "CHEATING", "MISCHIEF"]
        
        # Filter sections that contain relevant keywords
        filtered_data = self.bns_data[
            self.bns_data['Chapter_name'].str.upper().str.contains('|'.join(relevant_chapters), na=False) |
            self.bns_data['Section _name'].str.contains('theft|assault|threat|robbery|hurt|harassment|fraud|murder|rape|kidnap|extortion|criminal|violence', case=False, na=False)
        ].head(max_sections)
        
        # If filtering gives too few results, use first N sections
        if len(filtered_data) < 20:
            filtered_data = self.bns_data.head(max_sections)
        
        # Build condensed context
        context_lines = ["BNS (Bharatiya Nyaya Sanhita) Legal Sections:"]
        context_lines.append("=" * 60)
        
        for _, row in filtered_data.iterrows():
            section_info = (
                f"Section {row['Section']}: {row['Section _name']}\n"
                f"Chapter: {row['Chapter_name']}\n"
                f"Description: {row['Description'][:200]}...\n"
                f"{'-' * 60}"
            )
            context_lines.append(section_info)
        
        return "\n".join(context_lines)
    
    def classify_complaint(self, complaint_text: str) -> Dict:
        """
        Classify complaint using Gemini AI and BNS dataset
        
        Args:
            complaint_text: The complaint text to analyze
        
        Returns:
            Dictionary with structured classification results
        """
        # Fallback to rule-based if Gemini not available
        if not self.is_initialized:
            return self._fallback_classification(complaint_text)
        
        try:
            # Build BNS context
            bns_context = self._build_bns_context()
            
            # Create structured prompt
            prompt = f"""You are an expert legal analyst specializing in Indian criminal law under the Bharatiya Nyaya Sanhita (BNS).

{bns_context}

COMPLAINT TEXT:
{complaint_text}

TASK:
Analyze the complaint THOROUGHLY and extract ALL mentioned information in strict JSON format:

1. **crime_type**: SPECIFIC crime category based on severity:
   - "Grievous Hurt" if: fractures, broken bones, permanent disfigurement, serious bodily injury, weapon causing injury
   - "Assault" if: simple physical attack without serious injury
   - "Theft" for stolen items
   - "Threat/Criminal Intimidation" for verbal threats
   - Use OTHER specific categories: Murder, Rape, Kidnapping, Robbery, Burglary, Fraud, Harassment, etc.

2. **location**: ONLY the place/area/city - NOT time or date:
   - Extract: "Railway Station, Lucknow" or "Near Railway Station, Lucknow"
   - Do NOT include time in location (e.g., NOT "8 PM near railway station")
   - Format: [Landmark/Place], [Area], [City]

3. **date**: Complete date if mentioned (e.g., "8 April 2026", "yesterday", "last week")

4. **time**: Exact time if mentioned (e.g., "8 PM", "around 8:30 PM")

5. **persons_involved**: ALL names mentioned - victim, accused, witnesses, complainant (e.g., "Imran Khan (Complainant/Victim)", "Unknown accused")

6. **key_event_summary**: Clear 2-3 sentence summary including WHAT happened, WHO was involved, WHERE it happened, injury/damage details

7. **bns_sections**: Applicable BNS sections with specific reasons:
   - Section 116 for Grievous Hurt (fractures, serious injury with weapon)
   - Section 115 for simple Assault (no serious injury)
   - Section 118 for Grievous Hurt with deadly weapons
   - Section 303 for Theft
   - Section 351 for Criminal Intimidation
   - Format: [{{"section": "116", "reason": "Grievous hurt - fracture caused by metal rod"}}]

8. **severity**: 
   - High: Grievous hurt, weapons used, serious injury, high-value theft
   - Medium: Simple assault, threats, minor theft
   - Low: Harassment, verbal disputes

9. **additional_notes**: Important observations, injury details, weapon used, medical attention needed, escalation flags

CRITICAL CLASSIFICATION RULES:
- FRACTURES, BROKEN BONES = "Grievous Hurt" (Section 116), NOT "Assault"
- WEAPON CAUSING INJURY = "Grievous Hurt" (Section 116 or 118)
- SIMPLE ATTACK WITHOUT INJURY = "Assault" (Section 115)
- Location should NOT contain time/date - only place names
- Do NOT write "Not Specified" if information IS present in the text
- Be THOROUGH - read the entire complaint carefully

OUTPUT FORMAT:
```json
{{
    "crime_type": "",
    "location": "",
    "date": "",
    "time": "",
    "persons_involved": "",
    "key_event_summary": "",
    "bns_sections": [],
    "severity": "",
    "additional_notes": ""
}}
```
"""
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            result_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            classification = json.loads(result_text)
            
            # Format BNS sections for display
            if classification.get("bns_sections"):
                sections_formatted = []
                for sec in classification["bns_sections"]:
                    if isinstance(sec, dict):
                        sections_formatted.append(f"Section {sec.get('section', 'N/A')}: {sec.get('reason', '')}")
                    else:
                        sections_formatted.append(str(sec))
                classification["predicted_section"] = "; ".join(sections_formatted)
            else:
                classification["predicted_section"] = "Section not determined"
            
            # Add success flag
            classification["ai_classification"] = True
            
            return classification
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing error: {e}")
            print(f"Response text: {result_text[:200]}")
            return self._fallback_classification(complaint_text)
            
        except Exception as e:
            print(f"⚠️ Gemini classification error: {e}")
            return self._fallback_classification(complaint_text)
    
    def _fallback_classification(self, text: str) -> Dict:
        """
        Enhanced rule-based fallback when Gemini is unavailable
        """
        import re
        
        lowered = text.lower()
        
        # Crime type detection with severity escalation
        stolen_item = "property"
        
        # Check for Grievous Hurt FIRST (more specific than assault)
        grievous_hurt_keywords = [
            "fracture", "fractured", "broken bone", "broken arm", "broken leg",
            "permanent", "disfigure", "loss of limb", "severe injury", "serious injury",
            "hospitalized", "surgery", "stitches", "internal bleeding"
        ]
        
        weapon_keywords = [
            "knife", "rod", "stick", "bat", "weapon", "blade", "gun", "pistol",
            "metal rod", "iron rod", "wooden stick", "sharp object", "bottle"
        ]
        
        has_grievous_hurt = any(keyword in lowered for keyword in grievous_hurt_keywords)
        has_weapon = any(keyword in lowered for keyword in weapon_keywords)
        is_attack = "attack" in lowered or "assault" in lowered or "hit" in lowered or "beat" in lowered
        
        if has_grievous_hurt and (is_attack or has_weapon):
            crime_type = "Grievous Hurt"
            if has_weapon:
                predicted_section = "BNS Section 118 - Voluntarily Causing Grievous Hurt with Dangerous Weapon"
                severity = "High"
            else:
                predicted_section = "BNS Section 116 - Voluntarily Causing Grievous Hurt"
                severity = "High"
        elif has_weapon and is_attack:
            crime_type = "Grievous Hurt"
            predicted_section = "BNS Section 118 - Assault with Dangerous Weapon"
            severity = "High"
        elif "motorcycle" in lowered or "bike" in lowered or "two wheeler" in lowered:
            crime_type = "Theft"
            stolen_item = "motorcycle"
            predicted_section = "BNS Section 303 - Theft of Motor Vehicle"
            severity = "High"
        elif "theft" in lowered or "stole" in lowered or "stolen" in lowered:
            crime_type = "Theft"
            # Try to identify what was stolen
            if "phone" in lowered or "mobile" in lowered:
                stolen_item = "mobile phone"
            elif "wallet" in lowered or "purse" in lowered:
                stolen_item = "wallet"
            elif "car" in lowered or "vehicle" in lowered:
                stolen_item = "vehicle"
            predicted_section = f"BNS Section 303 - Theft of {stolen_item}"
            severity = "Medium" if stolen_item in ["wallet", "mobile phone"] else "High"
        elif is_attack:
            crime_type = "Assault"
            predicted_section = "BNS Section 115 - Assault or Criminal Force"
            severity = "Medium"
        elif "threat" in lowered or "threatened" in lowered:
            crime_type = "Threat"
            predicted_section = "BNS Section 351 - Criminal Intimidation"
            severity = "Medium"
        elif "fraud" in lowered or "cheat" in lowered or "scam" in lowered:
            crime_type = "Fraud"
            predicted_section = "BNS Section 316 - Cheating"
            severity = "Medium"
        elif "harassment" in lowered or "harass" in lowered:
            crime_type = "Harassment"
            predicted_section = "BNS Section 78 - Criminal Harassment"
            severity = "Medium"
        else:
            crime_type = "Unknown"
            predicted_section = "Section not determined - requires further review"
        # IMPORTANT: Exclude time patterns from location
        location = "Not Specified"
        location_patterns = [
            # Pattern 1: "near [place] in [city]" - most specific
            r"(?:near|at)\s+(?:the\s+)?([a-zA-Z\s]+?(?:station|park|mall|market|building|complex|temple|mosque|church))\s+in\s+([A-Z][a-zA-Z]+)",
            # Pattern 2: City/Area names (Andheri East, Mumbai)
            r"(?:in|at|near|outside|from)\s+(?:my\s+)?(?:apartment\s+in\s+)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*,\s*[A-Z][a-zA-Z]+)",
            # Pattern 3: Area with landmarks
            r"(?:in|at|near|outside)\s+(?:my\s+)?(?:apartment|house|home)\s+(?:in|at)\s+([A-Z][a-zA-Z\s]+(?:East|West|North|South)?(?:,\s*[A-Z][a-zA-Z]+)?)",
            # Pattern 4: Outside/near apartment in [location]
            r"(?:outside|near)\s+(?:my\s+)?apartment\s+in\s+([A-Z][a-zA-Z\s,]+)",
            # Pattern 5: Common places (avoid capturing time)
            r"(?:at|near|in|on|from|outside)\s+(?:the\s+)?([a-zA-Z\s]+?(?:park|street|road|market|mall|shop|store|building|station|gate|area|colony|complex))(?:\s+in\s+)?([A-Z][a-zA-Z]+)?",
            # Pattern 6: General area names
            r"(?:in|at)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)"
        ]
        
        for i, pattern in enumerate(location_patterns):
            loc_match = re.search(pattern, text)
            if loc_match:
                if i == 0:  # Pattern 1: near [place] in [city]
                    place = loc_match.group(1).strip().title()
                    city = loc_match.group(2).strip().title()
                    location = f"{place}, {city}"
                    break
                elif i == 4:  # Pattern 5: might have city in group 2
                    found_loc = loc_match.group(1).strip()
                    city = loc_match.group(2) if loc_match.lastindex >= 2 else None
                    # Exclude time patterns
                    if not re.match(r'\d+\s*(?:am|pm|AM|PM)', found_loc):
                        found_loc = re.sub(r'\s+', ' ', found_loc).title()
                        if city:
                            location = f"{found_loc}, {city}"
                        else:
                            location = found_loc
                        if len(location) > 3 and len(location) < 100:
                            break
                else:
                    found_loc = loc_match.group(1).strip()
                    # Exclude time patterns like "8 PM near"
                    if not re.match(r'\d+\s*(?:am|pm|AM|PM)', found_loc):
                        # Clean up location
                        found_loc = re.sub(r'\s+', ' ', found_loc)
                        if len(found_loc) > 3 and len(found_loc) < 100:
                            location = found_loc
                for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE)
            if date_match:
                date = date_match.group(1)
                break
         with injury details
        key_event_summary = ""
        if crime_type == "Theft":
            key_event_summary = f"Theft of {stolen_item}"
        elif crime_type == "Grievous Hurt":
            injury_detail = ""
            if "fracture" in lowered or "broken" in lowered:
                injury_detail = "causing fracture/serious injury"
            weapon_used = ""
            if has_weapon:
                for weapon in weapon_keywords:
                    if weapon in lowered:
                        weapon_used = f" with {weapon}"
                        break
            key_event_summary = f"Grievous hurt {injury_detail}{weapon_used}"
        else:
            key_event_summary = f"{crime_type} incident"
        
        if location != "Not Specified":
            key_event_summary += f" at {location}"
        if date != "Not Specified":
            key_event_summary += f" on {date}"
        if time != "Not Specified":
            key_event_summary += f" at {time}"
        
        # Full summary
        summary = text[:200] + "..." if len(text) > 200 else text
        
        additional_notes = "⚠️ Basic rule-based classification (Gemini AI not configured). "
        if crime_type == "Grievous Hurt":
            additional_notes += "Serious bodily injury - medical attention required. Escalate immediately. "
        el    r"(?:in|at)\s+([A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+)"
        ]
        
        for pattern in location_patterns:
            loc_match = re.search(pattern, text)
            if loc_match:
                found_loc = loc_match.group(1).strip()
                # Clean up location
                found_loc = re.sub(r'\s+', ' ', found_loc)
                if len(found_loc) > 3 and len(found_loc) < 100:
                    location = found_loc
                    break
        
        # Enhanced person extraction
        persons_involved = "Not Specified"
        person_patterns = [
            # Pattern 1: "Name: [Name]"
            r"Name:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            # Pattern 2: Direct names in text
            r"\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)\b"
        ]
        
        for pattern in person_patterns:
            person_match = re.search(pattern, text)
            if person_match:
                name = person_match.group(1).strip()
                # Exclude common non-name words
                excluded = {"Not Specified", "January February", "Mumbai Police"}
                if name not in excluded and len(name.split()) <= 4:
                    persons_involved = f"{name} (Complainant/Victim)"
                    break
        
        # If still not found, check for descriptors
        if persons_involved == "Not Specified":
            if "suspect" in lowered or "accused" in lowered:
                persons_involved = "Unknown accused"
            elif "someone" in lowered or "somebody" in lowered:
                persons_involved = "Unknown person"
        
        # Enhanced summary
        key_event_summary = f"{crime_type} of {stolen_item}" if crime_type == "Theft" else f"{crime_type} incident"
        if location != "Not Specified":
            key_event_summary += f" at {location}"
        if date != "Not Specified":
            key_event_summary += f" on {date}"
        if time != "Not Specified":
            key_event_summary += f" at {time}"
        
        # Full summary
        summary = text[:200] + "..." if len(text) > 200 else text
        
        additional_notes = "⚠️ Basic rule-based classification (Gemini AI not configured). "
        if crime_type == "Theft" and stolen_item == "motorcycle":
            additional_notes += "High-value item stolen - escalate to senior officer. "
        additional_notes += "For more accurate extraction, configure GEMINI_API_KEY environment variable."
        
        return {
            "crime_type": crime_type,
            "location": location,
            "date": date,
            "time": time,
            "persons_involved": persons_involved,
            "key_event_summary": key_event_summary,
            "predicted_section": predicted_section,
            "severity": severity,
            "additional_notes": additional_notes,
            "ai_classification": False,
            "bns_sections": [{"section": predicted_section.split()[2] if "Section" in predicted_section else "N/A", 
                             "reason": crime_type}]
        }
    
    def get_section_details(self, section_number: str) -> Optional[Dict]:
        """
        Get detailed information about a specific BNS section
        
        Args:
            section_number: BNS section number
        
        Returns:
            Dictionary with section details or None if not found
        """
        if self.bns_data is None:
            return None
        
        section = self.bns_data[self.bns_data['Section'].astype(str) == str(section_number)]
        
        if section.empty:
            return None
        
        row = section.iloc[0]
        return {
            "section": row['Section'],
            "name": row['Section _name'],
            "chapter": row['Chapter_name'],
            "description": row['Description']
        }


# Global classifier instance (initialized on first use)
_classifier_instance = None

def get_classifier() -> BNSClassifier:
    """Get or create the global BNS classifier instance"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = BNSClassifier()
    return _classifier_instance
