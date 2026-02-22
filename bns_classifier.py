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
Analyze the complaint and extract the following information in strict JSON format:

1. **crime_type**: Primary crime category (e.g., Theft, Assault, Threat, Harassment, Fraud, etc.)
2. **location**: Location where incident occurred (if mentioned, otherwise "Not Specified")
3. **date**: Date of incident (if mentioned, otherwise "Not Specified")
4. **time**: Time of incident (if mentioned, otherwise "Not Specified")
5. **persons_involved**: Names or descriptions of accused/victim/witnesses (if mentioned, otherwise "Not Specified")
6. **key_event_summary**: Concise 2-3 sentence summary of what happened
7. **bns_sections**: Array of applicable BNS section numbers with reasons (e.g., [{{"section": "303", "reason": "Theft offense"}}])
8. **severity**: Low/Medium/High based on nature of crime
9. **additional_notes**: Any important observations or escalation flags

RULES:
- Do NOT hallucinate or invent information not present in the complaint
- If information is not mentioned, use "Not Specified"
- Match crimes to appropriate BNS sections based on the dataset provided
- Be precise and factual
- Output ONLY valid JSON, no additional text

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
        Simple rule-based fallback when Gemini is unavailable
        """
        import re
        
        lowered = text.lower()
        
        # Crime type detection
        if "theft" in lowered or "stole" in lowered or "stolen" in lowered:
            crime_type = "Theft"
            predicted_section = "BNS Section 303 - Theft"
        elif "assault" in lowered or "attacked" in lowered or "hit" in lowered:
            crime_type = "Assault"
            predicted_section = "BNS Section 115 - Assault"
        elif "threat" in lowered or "threatened" in lowered:
            crime_type = "Threat"
            predicted_section = "BNS Section 351 - Criminal Intimidation"
        elif "fraud" in lowered or "cheat" in lowered or "scam" in lowered:
            crime_type = "Fraud"
            predicted_section = "BNS Section 316 - Cheating"
        elif "harassment" in lowered or "harass" in lowered:
            crime_type = "Harassment"
            predicted_section = "BNS Section 78 - Criminal Harassment"
        else:
            crime_type = "Unknown"
            predicted_section = "Section not determined - requires further review"
        
        # Time extraction
        time_match = re.search(r"\b\d{1,2}[:.]?\d{0,2}\s*(?:am|pm|AM|PM|hours|hrs)\b", text)
        time = time_match.group(0) if time_match else "Not Specified"
        
        # Date extraction
        date_match = re.search(r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b(?:yesterday|today|last night|last week)\b", text, re.IGNORECASE)
        date = date_match.group(0) if date_match else "Not Specified"
        
        # Location extraction
        location = "Not Specified"
        location_pattern = r"(?:at|near|in|on)\s+(?:the\s+)?([a-zA-Z0-9\s]+?(?:park|street|road|market|mall|shop|store|building|station))"
        loc_match = re.search(location_pattern, text, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip().title()
        
        # Summary
        summary = text[:200] + "..." if len(text) > 200 else text
        
        return {
            "crime_type": crime_type,
            "location": location,
            "date": date,
            "time": time,
            "persons_involved": "Not Specified",
            "key_event_summary": summary,
            "predicted_section": predicted_section,
            "severity": "Medium",
            "additional_notes": "⚠️ Basic rule-based classification (Gemini AI not configured)",
            "ai_classification": False,
            "bns_sections": []
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
