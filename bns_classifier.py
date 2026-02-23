"""
BNS Classification Module using Google Gemini API
This module loads the BNS dataset and uses Gemini AI to intelligently classify complaints
"""

import os
import pandas as pd
import google.generativeai as genai
from typing import Optional, Dict, List, Any
import json
import re
import math
from collections import Counter, defaultdict

class BNSClassifier:
    """Intelligent complaint classifier using Gemini API and BNS dataset"""

    _STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "if", "then", "else", "when", "where", "why", "how",
        "i", "me", "my", "mine", "we", "our", "ours", "you", "your", "yours", "he", "she", "they",
        "him", "her", "them", "this", "that", "these", "those", "is", "are", "was", "were", "be",
        "been", "being", "to", "of", "in", "on", "at", "from", "near", "outside", "inside", "with",
        "for", "as", "by", "it", "its", "into", "over", "under", "between", "during", "after", "before",
        "yesterday", "today", "tomorrow", "around", "about",
    }

    @staticmethod
    def _extract_json_block(text: str) -> str:
        """Extract the most likely JSON object from a model response."""
        result_text = (text or "").strip()

        # Remove markdown code blocks if present
        if "```json" in result_text:
            result_text = result_text.split("```json", 1)[1]
            result_text = result_text.split("```", 1)[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```", 1)[1]
            result_text = result_text.split("```", 1)[0].strip()

        # Grab from first '{' to last '}'
        start = result_text.find("{")
        end = result_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return result_text[start : end + 1].strip()

        return result_text

    def _repair_json_with_gemini(self, broken_json_text: str) -> Optional[Dict]:
        """If Gemini returns non-parseable JSON, ask it to repair into strict JSON."""
        if not self.model:
            return None

        repair_prompt = f"""You are a strict JSON formatter.

Convert the content below into VALID JSON that matches this schema exactly:
{{
  \"crime_type\": \"\",
  \"location\": \"\",
  \"date\": \"\",
  \"time\": \"\",
  \"persons_involved\": \"\",
  \"key_event_summary\": \"\",
  \"bns_sections\": [{{\"section\": \"\", \"reason\": \"\"}}],
  \"severity\": \"\",
  \"additional_notes\": \"\"
}}

Rules:
- Output ONLY JSON (no markdown, no commentary).
- Escape any quotes inside strings.
- Do not include unescaped newlines inside string values; use spaces.

CONTENT TO FIX:
{broken_json_text}
"""

        response = self.model.generate_content(repair_prompt)
        repaired_text = self._extract_json_block(getattr(response, "text", "") or "")
        return json.loads(repaired_text)
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the BNS classifier with Gemini API
        
        Args:
            api_key: Google Gemini API key (if None, reads from GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.bns_data = None
        self._all_section_ids: set[str] = set()
        # Map section id -> row index (avoids duplicating long descriptions in memory)
        self._section_row_by_id: Dict[str, int] = {}

        # Precomputed BM25 structures (CSV-grounded)
        self._bm25_df: Dict[str, int] = {}
        self._bm25_idf: Dict[str, float] = {}
        self._bm25_doc_tf: List[Dict[str, int]] = []
        self._bm25_doc_len: List[int] = []
        self._bm25_avgdl: float = 0.0

        self.model = None
        self.model_name = None
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
            self.bns_data = pd.read_csv(csv_path).reset_index(drop=True)
            # Precompute normalized fields for fast, consistent matching.
            # All section selection must be grounded in this CSV.
            for col in ["Chapter_name", "Section _name", "Description", "Section"]:
                if col not in self.bns_data.columns:
                    raise ValueError(f"Missing required column in BNS CSV: {col}")

            self.bns_data["_section_str"] = self.bns_data["Section"].astype(str).str.strip()
            self._all_section_ids = set(self.bns_data["_section_str"].tolist())

            searchable = (
                self.bns_data["Chapter_name"].fillna("").astype(str)
                + " | "
                + self.bns_data["Section _name"].fillna("").astype(str)
                + " | "
                + self.bns_data["Description"].fillna("").astype(str)
            )
            self.bns_data["_search_text"] = searchable.str.lower()

            # Keep only row indices for details (to minimize memory use)
            self._section_row_by_id = {}
            for idx, row in self.bns_data.iterrows():
                sid = str(row.get("Section", "")).strip()
                if not sid:
                    continue
                self._section_row_by_id[sid] = int(idx)

            # Build BM25 index over (Section name + Description) for local semantic-ish matching.
            self._build_bm25_index()
            print(f"✅ Loaded {len(self.bns_data)} BNS sections from dataset")
        except Exception as e:
            print(f"❌ Error loading BNS dataset: {e}")
            self.bns_data = None
            self._all_section_ids = set()
            self._section_row_by_id = {}
            self._bm25_df = {}
            self._bm25_idf = {}
            self._bm25_doc_tf = []
            self._bm25_doc_len = []
            self._bm25_avgdl = 0.0

    def _tokens_for_similarity(self, text: str) -> List[str]:
        lowered = (text or "").lower()
        words = re.findall(r"[a-z]{3,}", lowered)
        return [w for w in words if w not in self._STOPWORDS]

    def _build_bm25_index(self) -> None:
        """Build a compact BM25 index over official section name + description."""
        if self.bns_data is None or self.bns_data.empty:
            self._bm25_df = {}
            self._bm25_idf = {}
            self._bm25_doc_tf = []
            self._bm25_doc_len = []
            self._bm25_avgdl = 0.0
            return

        doc_tf: List[Dict[str, int]] = []
        doc_len: List[int] = []
        df_counts: Dict[str, int] = defaultdict(int)

        for _, row in self.bns_data.iterrows():
            combined = f"{row.get('Section _name', '')}\n{row.get('Description', '')}"
            tokens = self._tokens_for_similarity(str(combined))
            tf = Counter(tokens)
            # Keep only the top terms by frequency to bound memory
            if len(tf) > 220:
                tf = Counter(dict(tf.most_common(220)))

            tf_dict = dict(tf)
            doc_tf.append(tf_dict)
            dl = sum(tf_dict.values())
            doc_len.append(dl)
            for tok in tf_dict.keys():
                df_counts[tok] += 1

        n_docs = len(doc_tf)
        avgdl = (sum(doc_len) / n_docs) if n_docs else 0.0

        self._bm25_df = dict(df_counts)
        self._bm25_doc_tf = doc_tf
        self._bm25_doc_len = doc_len
        self._bm25_avgdl = avgdl

        # Okapi BM25 IDF (smoothed)
        idf: Dict[str, float] = {}
        for tok, df in df_counts.items():
            # log( (N - df + 0.5) / (df + 0.5) + 1)
            idf[tok] = math.log(((n_docs - df + 0.5) / (df + 0.5)) + 1.0)
        self._bm25_idf = idf

    def _semantic_match_sections(
        self,
        complaint_text: str,
        top_n: int = 7,
        min_score: float = 0.0,
        source_df: Optional[pd.DataFrame] = None,
    ) -> List[Dict[str, str]]:
        """Return multiple CSV-grounded sections by BM25 similarity to official description."""
        if self.bns_data is None or self.bns_data.empty:
            return []
        if not complaint_text or not str(complaint_text).strip():
            return []
        if not self._bm25_doc_tf or not self._bm25_idf:
            return []

        # Limit scoring to a narrowed dataframe when provided (still uses official description text)
        if source_df is None:
            indices = list(self.bns_data.index)
        else:
            indices = list(source_df.index)

        q_tokens = self._tokens_for_similarity(str(complaint_text))
        if not q_tokens:
            return []
        q_unique = list(dict.fromkeys(q_tokens))

        k1 = 1.5
        b = 0.75
        avgdl = self._bm25_avgdl or 1.0

        scored: List[tuple[float, int, List[str]]] = []
        for idx in indices:
            tf = self._bm25_doc_tf[idx]
            dl = self._bm25_doc_len[idx] or 0
            if not tf or dl <= 0:
                continue

            score = 0.0
            token_contrib: List[tuple[float, str]] = []
            for tok in q_unique:
                f = tf.get(tok)
                if not f:
                    continue
                idf = self._bm25_idf.get(tok, 0.0)
                denom = f + k1 * (1.0 - b + b * (dl / avgdl))
                contrib = idf * ((f * (k1 + 1.0)) / denom)
                score += contrib
                token_contrib.append((contrib, tok))

            if score <= min_score:
                continue
            token_contrib.sort(reverse=True)
            top_tokens = [t for _, t in token_contrib[:6]]
            scored.append((score, idx, top_tokens))

        scored.sort(key=lambda x: x[0], reverse=True)

        out: List[Dict[str, str]] = []
        for score, idx, top_tokens in scored[:top_n]:
            sid = str(self.bns_data.loc[idx, "_section_str"]).strip()
            if not sid:
                continue
            sec_name = str(self.bns_data.loc[idx, "Section _name"] or "").strip()
            keywords = ", ".join(top_tokens)
            reason = "Similarity to official BNS description"
            if sec_name:
                reason += f" (\"{sec_name}\")"
            if keywords:
                reason += f"; matched terms: {keywords}."
            out.append({"section": sid, "reason": reason, "score": f"{score:.3f}"})

        return self._validate_bns_sections_against_csv(out)

    def _enrich_sections_with_csv_details(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attach exact CSV name/chapter/description to each section dict."""
        enriched: List[Dict[str, Any]] = []
        for item in sections or []:
            if not isinstance(item, dict):
                continue
            sec_id = self._extract_section_id(item.get("section"))
            row_idx = self._section_row_by_id.get(sec_id) if sec_id else None
            if row_idx is None or self.bns_data is None:
                continue
            base = dict(item)
            base.setdefault("name", str(self.bns_data.loc[row_idx, "Section _name"] or "").strip())
            base.setdefault("chapter", str(self.bns_data.loc[row_idx, "Chapter_name"] or "").strip())
            base.setdefault("description", str(self.bns_data.loc[row_idx, "Description"] or ""))
            enriched.append(base)
        return enriched

    def _extract_section_id(self, value: Any) -> Optional[str]:
        """Extract a section number from various model/fallback outputs."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            # float can happen if parsed loosely; cast carefully
            try:
                return str(int(value))
            except Exception:
                return None
        text = str(value).strip()
        if not text:
            return None
        m = re.search(r"\b(\d{1,4})\b", text)
        return m.group(1) if m else None

    def _tokenize_for_match(self, text: str, max_tokens: int = 15) -> List[str]:
        return self._tokenize_for_match_with_hints(text=text, max_tokens=max_tokens, force_include=None)

    def _tokenize_for_match_with_hints(
        self, text: str, max_tokens: int = 15, force_include: Optional[List[str]] = None
    ) -> List[str]:
        """Tokenize text, ensuring `force_include` tokens are included first."""
        force_include = [t.lower().strip() for t in (force_include or []) if str(t).strip()]

        tokens: List[str] = []
        seen = set()

        for t in force_include:
            if t in seen:
                continue
            seen.add(t)
            tokens.append(t)
            if len(tokens) >= max_tokens:
                return tokens

        words = re.findall(r"[a-zA-Z]{4,}", (text or "").lower())
        for w in words:
            if w in self._STOPWORDS:
                continue
            if w in seen:
                continue
            seen.add(w)
            tokens.append(w)
            if len(tokens) >= max_tokens:
                break
        return tokens

    def _infer_hint_tokens(self, complaint_text: str) -> List[str]:
        """Heuristic hints to keep CSV matching stable (used for candidates + fallback)."""
        lowered = (complaint_text or "").lower()
        hints: List[str] = []
        if any(k in lowered for k in ["theft", "stolen", "stole", "missing", "robbed", "snatched"]):
            hints.extend(["theft", "stolen", "property"])
        if any(k in lowered for k in ["bike", "motorcycle", "scooter", "car", "vehicle"]):
            hints.extend(["vehicle", "motor"])
        if any(k in lowered for k in ["fracture", "fractured", "broken", "grievous", "serious injury"]):
            hints.extend(["grievous", "hurt", "fracture"])
        if any(k in lowered for k in ["knife", "rod", "stick", "weapon", "blade", "gun", "pistol"]):
            hints.extend(["dangerous", "weapons", "weapon"])
        if any(k in lowered for k in ["threat", "threatened", "intimidat", "kill you", "harm you"]):
            hints.extend(["criminal", "intimidation", "threat"])
        if any(k in lowered for k in ["fraud", "cheat", "cheated", "scam"]):
            hints.extend(["cheating", "fraud"])
        if any(k in lowered for k in ["harass", "harassment", "stalk"]):
            hints.extend(["harassment"])

        # de-dup preserve order
        out: List[str] = []
        seen = set()
        for h in hints:
            if h in seen:
                continue
            seen.add(h)
            out.append(h)
        return out

    def _get_candidate_sections(
        self,
        complaint_text: str,
        top_k: int = 40,
        force_include: Optional[List[str]] = None,
        source_df: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """Return top candidate sections from the CSV for a given complaint."""
        df = source_df if source_df is not None else self.bns_data
        if df is None or df.empty:
            return pd.DataFrame()

        tokens = self._tokenize_for_match_with_hints(
            text=complaint_text,
            max_tokens=18,
            force_include=force_include,
        )
        if not tokens:
            return df.head(top_k)

        base = df["_search_text"]
        # Simple, explainable score: count of token hits in each row.
        score = pd.Series(0, index=df.index, dtype="int64")
        for tok in tokens:
            pattern = rf"\b{re.escape(tok)}\b"
            score = score + base.str.contains(pattern, regex=True, na=False).astype("int64")

        if int(score.max()) == 0:
            # If there are no token hits at all, fall back to broad CSV keywords
            # so we don't accidentally return unrelated early sections.
            broad = ["theft", "hurt", "grievous", "assault", "intimidation", "cheating", "harassment", "robbery"]
            broad_patterns = [rf"\b{re.escape(x)}\b" for x in broad]
            broad_mask = base.str.contains("|".join(broad_patterns), regex=True, na=False)
            narrowed = df[broad_mask]
            if not narrowed.empty:
                df = narrowed
                base = df["_search_text"]
                score = pd.Series(0, index=df.index, dtype="int64")
                for tok in (force_include or broad):
                    pattern = rf"\b{re.escape(str(tok).lower())}\b"
                    score = score + base.str.contains(pattern, regex=True, na=False).astype("int64")

        ranked = df.assign(_score=score).sort_values(by=["_score", "Section"], ascending=[False, True])
        return ranked.head(top_k)

    def _validate_bns_sections_against_csv(self, bns_sections: Any) -> List[Dict[str, str]]:
        """Keep only sections that exist in bns_sections.csv."""
        if not bns_sections or not isinstance(bns_sections, list):
            return []

        cleaned: List[Dict[str, Any]] = []
        for item in bns_sections:
            if isinstance(item, dict):
                sec_id = self._extract_section_id(item.get("section"))
                reason = (item.get("reason") or "").strip()
                extra = {k: v for k, v in item.items() if k not in {"section", "reason"}}
            else:
                sec_id = self._extract_section_id(item)
                reason = ""  # unknown
                extra = {}

            if not sec_id:
                continue
            if sec_id not in self._all_section_ids:
                continue
            cleaned.append({"section": sec_id, "reason": reason, **extra})

        # De-duplicate by section id while preserving order
        deduped: List[Dict[str, Any]] = []
        seen = set()
        for x in cleaned:
            sid = x["section"]
            if sid in seen:
                continue
            seen.add(sid)
            deduped.append(x)
        return deduped
    
    def _initialize_gemini(self):
        """Configure Gemini API"""
        try:
            genai.configure(api_key=self.api_key)

            # Different API keys / regions / API versions can expose different model IDs.
            # To avoid hardcoding a model that returns 404, discover available models and
            # pick the best one that supports generateContent.
            discovered_model_ids: list[str] = []
            try:
                for m in genai.list_models():
                    supported = getattr(m, "supported_generation_methods", None) or []
                    if "generateContent" in supported:
                        model_id = getattr(m, "name", "") or ""
                        if model_id:
                            # API returns names like "models/gemini-..."; GenerativeModel
                            # expects the short ID (e.g., "gemini-1.5-flash").
                            discovered_model_ids.append(model_id.split("/")[-1])
            except Exception as e:
                print(f"⚠️ Could not list Gemini models: {e}")

            # Prefer fast/cheap models first, then any other available model.
            preferred = [
                "gemini-1.5-flash",
                "gemini-1.5-flash-latest",
                "gemini-1.5-pro",
                "gemini-1.5-pro-latest",
                "gemini-pro",
            ]

            candidate_ids = []
            if discovered_model_ids:
                # keep ordering by preference if present, then append any remaining discovered
                for p in preferred:
                    if p in discovered_model_ids and p not in candidate_ids:
                        candidate_ids.append(p)
                for mid in discovered_model_ids:
                    if mid not in candidate_ids:
                        candidate_ids.append(mid)
            else:
                candidate_ids = preferred

            last_error = None
            for candidate in candidate_ids:
                try:
                    self.model = genai.GenerativeModel(
                        model_name=candidate,
                        generation_config={
                            "temperature": 0.2,  # Low temperature for consistent, factual outputs
                            "top_p": 0.8,
                            "top_k": 40,
                            "max_output_tokens": 2048,
                        },
                    )
                    self.model_name = candidate
                    self.is_initialized = True
                    print(f"✅ Gemini API initialized successfully (model={candidate})")
                    return
                except Exception as e:
                    last_error = e

            raise RuntimeError(f"No compatible Gemini model found. Last error: {last_error}")
        except Exception as e:
            print(f"❌ Error initializing Gemini: {e}")
            self.is_initialized = False
    
    def _build_bns_context(self, complaint_text: str = "", max_sections: int = 50) -> str:
        """
        Build a condensed BNS context for the prompt
        
        Args:
            max_sections: Maximum number of sections to include (to avoid token limits)
        
        Returns:
            Formatted string with BNS sections
        """
        if self.bns_data is None or self.bns_data.empty:
            return "BNS dataset not available"

        # Build complaint-specific candidate list from CSV (keeps Gemini grounded).
        hints = self._infer_hint_tokens(complaint_text)
        filtered_data = self._get_candidate_sections(
            complaint_text,
            top_k=max_sections,
            force_include=hints,
        )
        if filtered_data is None or filtered_data.empty:
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

    def _retry_sections_only(self, complaint_text: str, candidates: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Second-pass Gemini call to ONLY select BNS sections from CSV-derived candidates."""
        if not self.model:
            return []

        candidate_ids = [c.get("section", "") for c in candidates if c.get("section")]
        retry_prompt = f"""You are selecting applicable legal sections.

COMPLAINT TEXT:
{complaint_text}

CANDIDATE SECTIONS (from bns_sections.csv) - you MUST choose ONLY from these section numbers:
{json.dumps(candidate_ids, ensure_ascii=False)}

Return ONLY JSON (no markdown, no commentary) with this exact schema:
{{
  \"bns_sections\": [{{\"section\": \"\", \"reason\": \"\"}}]
}}

Rules:
- Every section must be one of the candidate section numbers above.
- If none apply, return an empty array.
- Keep reasons short and specific.
"""
        response = self.model.generate_content(retry_prompt)
        result_text = self._extract_json_block(getattr(response, "text", "") or "")
        try:
            obj = json.loads(result_text)
        except Exception:
            return []
        return self._validate_bns_sections_against_csv(obj.get("bns_sections"))
    
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
            hints = self._infer_hint_tokens(complaint_text)
            candidates_df = self._get_candidate_sections(
                complaint_text,
                top_k=40,
                force_include=hints,
            )
            candidates: List[Dict[str, str]] = []
            if candidates_df is not None and not candidates_df.empty:
                for _, row in candidates_df.iterrows():
                    candidates.append(
                        {
                            "section": str(row.get("Section", "")).strip(),
                            "name": str(row.get("Section _name", "")).strip(),
                            "chapter": str(row.get("Chapter_name", "")).strip(),
                            "description": str(row.get("Description", ""))[:240].replace("\n", " ").strip(),
                        }
                    )
            bns_context = self._build_bns_context(complaint_text, max_sections=50)
            
            # Create structured prompt (sections MUST come from bns_sections.csv candidates)
            prompt = f"""You are an expert legal analyst specializing in Indian criminal law under the Bharatiya Nyaya Sanhita (BNS).

{bns_context}

CANDIDATE_BNS_SECTIONS (from bns_sections.csv):
{json.dumps(candidates, ensure_ascii=False)}

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
    - You MUST choose section numbers ONLY from CANDIDATE_BNS_SECTIONS above.
    - The section number must exactly match the CSV section number (string).
    - Format: [{{"section": "<CSV section>", "reason": "<short reason>"}}]
    - If none apply, return an empty list: []

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
Return ONLY a single JSON object (no markdown code fences, no commentary) with keys:
crime_type, location, date, time, persons_involved, key_event_summary, bns_sections, severity, additional_notes.

JSON SCHEMA EXAMPLE:
{{
    "crime_type": "",
    "location": "",
    "date": "",
    "time": "",
    "persons_involved": "",
    "key_event_summary": "",
    "bns_sections": [{{"section": "", "reason": ""}}],
    "severity": "",
    "additional_notes": ""
}}

IMPORTANT JSON RULES:
- Use double quotes for all keys/strings.
- Escape any quotes inside string values.
- Do not include unescaped newlines inside string values; use spaces.
"""
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            # Extract and parse JSON from response
            result_text = self._extract_json_block(getattr(response, "text", "") or "")
            try:
                classification = json.loads(result_text)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing error: {e}")
                print(f"Response text: {result_text[:400]}")
                # Attempt to repair JSON using Gemini (single extra call)
                try:
                    repaired = self._repair_json_with_gemini(result_text)
                    if repaired is None:
                        raise
                    classification = repaired
                except Exception as repair_error:
                    print(f"⚠️ JSON repair failed: {repair_error}")
                    return self._fallback_classification(complaint_text)

            # Enforce: sections must exist in bns_sections.csv
            validated_sections = self._validate_bns_sections_against_csv(classification.get("bns_sections"))
            if not validated_sections and candidates:
                # One more targeted retry to pick from CSV-derived candidates.
                validated_sections = self._retry_sections_only(complaint_text, candidates)

            # Advanced CSV-grounded semantic matching against section descriptions.
            # Merge Gemini-selected sections with similarity-ranked sections so we return
            # multiple relevant sections (not just one) while staying strictly CSV-backed.
            semantic_matches = self._semantic_match_sections(
                complaint_text=complaint_text,
                top_n=7,
                min_score=0.0,
            )

            used_gemini = bool(validated_sections)
            used_bm25 = bool(semantic_matches)
            if used_gemini and used_bm25:
                classification["bns_section_mapping_method"] = "gemini+bm25"
            elif used_gemini:
                classification["bns_section_mapping_method"] = "gemini"
            else:
                classification["bns_section_mapping_method"] = "bm25"

            merged: List[Dict[str, Any]] = []
            merged.extend(validated_sections or [])
            existing = {self._extract_section_id(x.get("section")) for x in (validated_sections or []) if isinstance(x, dict)}
            for m in semantic_matches:
                mid = self._extract_section_id(m.get("section"))
                if not mid or mid in existing:
                    continue
                merged.append(m)

            # Keep output bounded for readability.
            merged = merged[:10]

            classification["bns_sections"] = self._enrich_sections_with_csv_details(merged)
            
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
            
        except Exception as e:
            print(f"⚠️ Gemini classification error: {e}")
            return self._fallback_classification(complaint_text)
    
    def _fallback_classification(self, text: str) -> Dict:
        """
        Enhanced rule-based fallback when Gemini is unavailable
        """
        # NOTE: fallback MUST also stay grounded in bns_sections.csv (no hard-coded section IDs).
        
        lowered = text.lower()
        
        # Initialize default values
        crime_type = "Unknown"
        predicted_section = "Section not determined - requires further review"
        severity = "Low"
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
            severity = "High"
        elif has_weapon and is_attack:
            crime_type = "Grievous Hurt"
            severity = "High"
        elif "motorcycle" in lowered or "bike" in lowered or "two wheeler" in lowered:
            crime_type = "Theft"
            stolen_item = "motorcycle"
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
            severity = "Medium" if stolen_item in ["wallet", "mobile phone"] else "High"
        elif is_attack:
            crime_type = "Assault"
            severity = "Medium"
        elif "threat" in lowered or "threatened" in lowered:
            crime_type = "Threat"
            severity = "Medium"
        elif "fraud" in lowered or "cheat" in lowered or "scam" in lowered:
            crime_type = "Fraud"
            severity = "Medium"
        elif "harassment" in lowered or "harass" in lowered:
            crime_type = "Harassment"
            severity = "Medium"

        # CSV-grounded legal section selection for fallback
        matched_sections: List[Dict[str, str]] = []
        if self.bns_data is not None and not self.bns_data.empty:
            # Add a few crime-type hints to the complaint to improve matching.
            crime_hints = {
                "Theft": "theft stolen property motor vehicle",
                "Grievous Hurt": "grievous hurt fracture weapon injury",
                "Assault": "assault criminal force hit attack",
                "Threat": "criminal intimidation threat",
                "Fraud": "cheating fraud scam",
                "Harassment": "harassment",
            }.get(crime_type, "")
            match_text = f"{text} {crime_hints}".strip()
            force_include = self._infer_hint_tokens(text)
            force_include.extend([t for t in crime_hints.split() if t])

            # Crime-type specific narrowing (still strictly CSV-backed).
            source_df = self.bns_data
            try:
                if crime_type == "Theft":
                    theft_mask = (
                        source_df["Section _name"].str.contains(r"\btheft\b", case=False, na=False)
                        | source_df.get("Chapter_subtype", pd.Series([""] * len(source_df))).astype(str).str.contains(
                            r"\btheft\b", case=False, na=False
                        )
                    )
                    narrowed = source_df[theft_mask]
                    if not narrowed.empty:
                        source_df = narrowed
                        force_include.extend(["theft"])
                elif crime_type in {"Grievous Hurt", "Assault"}:
                    hurt_mask = source_df["Section _name"].str.contains(r"hurt|grievous", case=False, na=False)
                    narrowed = source_df[hurt_mask]
                    if not narrowed.empty:
                        source_df = narrowed
                        force_include.extend(["hurt", "grievous"])
                elif crime_type == "Threat":
                    thr_mask = source_df["Section _name"].str.contains(r"intimidation|threat", case=False, na=False)
                    narrowed = source_df[thr_mask]
                    if not narrowed.empty:
                        source_df = narrowed
                        force_include.extend(["intimidation", "threat"])
                elif crime_type == "Fraud":
                    fr_mask = source_df["Section _name"].str.contains(r"cheating|fraud", case=False, na=False)
                    narrowed = source_df[fr_mask]
                    if not narrowed.empty:
                        source_df = narrowed
                        force_include.extend(["cheating", "fraud"])
                elif crime_type == "Harassment":
                    h_mask = source_df["Section _name"].str.contains(r"harass", case=False, na=False)
                    narrowed = source_df[h_mask]
                    if not narrowed.empty:
                        source_df = narrowed
                        force_include.extend(["harassment"])
            except Exception:
                source_df = self.bns_data

            # Semantic-style scoring: compare complaint text against official description text.
            matched_sections = self._semantic_match_sections(
                complaint_text=match_text,
                top_n=7,
                min_score=0.0,
                source_df=source_df,
            )

        matched_sections = self._validate_bns_sections_against_csv(matched_sections)
        matched_sections = self._enrich_sections_with_csv_details(matched_sections)
        if matched_sections:
            predicted_section = "; ".join(
                [f"Section {s['section']}: {s.get('reason', '').strip()}" for s in matched_sections]
            )
        mapping_method = "bm25" if matched_sections else "bm25"
        
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
        
        # Date extraction
        date = "Not Specified"
        date_patterns = [
            r"(?:Date|date|DATE):\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
            r"on\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})",
            r"(\d{1,2}/\d{1,2}/\d{4})"
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, text, re.IGNORECASE)
            if date_match:
                date = date_match.group(1)
                break
        
        # Time extraction
        time = "Not Specified"
        time_patterns = [
            r"(?:at|around)\s+(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))",
            r"(?:at|around)\s+(\d{1,2}\s*(?:AM|PM|am|pm))",
            r"(\d{1,2}:\d{2})"
        ]
        
        for pattern in time_patterns:
            time_match = re.search(pattern, text, re.IGNORECASE)
            if time_match:
                time = time_match.group(1)
                break
        
        # Key event summary with injury details
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
        
        additional_notes = "Note: Basic rule-based extraction (Gemini AI not configured). "
        if crime_type == "Grievous Hurt":
            additional_notes += "Serious bodily injury - medical attention required. Escalate immediately. "
        additional_notes += "For more accurate extraction, configure GEMINI_API_KEY environment variable."
        
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
        
        additional_notes = "Note: Basic rule-based extraction (Gemini AI not configured). "
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
            "bns_sections": matched_sections if matched_sections else [],
            "bns_section_mapping_method": "bm25",
        }
    
    def get_section_details(self, section_number: str) -> Optional[Dict]:
        """
        Get detailed information about a specific BNS section
        
        Args:
            section_number: BNS section number
        
        Returns:
            Dictionary with section details or None if not found
        """
        section_id = str(section_number or "").strip()
        if not section_id:
            return None
        if self.bns_data is None:
            return None
        row_idx = self._section_row_by_id.get(section_id)
        if row_idx is None:
            return None
        row = self.bns_data.loc[row_idx]
        return {
            "section": str(row.get("Section", "")).strip(),
            "name": str(row.get("Section _name", "")).strip(),
            "chapter": str(row.get("Chapter_name", "")).strip(),
            "description": str(row.get("Description", "")),
        }


# Global classifier instance (initialized on first use)
_classifier_instance = None

def get_classifier() -> BNSClassifier:
    """Get or create the global BNS classifier instance"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = BNSClassifier()
    return _classifier_instance
