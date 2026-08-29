import os
import json
import re
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv
from app.models import ExtractionResponse, is_transient_error

# Load environment variables
load_dotenv()

PROMPT_FILE = Path(__file__).parent / "prompts" / "claim_extraction.txt"

def load_prompt_template() -> str:
    """Reads the prompt template file at runtime."""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt template file not found at: {PROMPT_FILE}")
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()

def clean_json_response(raw_text: str) -> str:
    """Extracts valid JSON string from potential markdown code block."""
    text = raw_text.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return text

def extract_claims(caption: str) -> ExtractionResponse:
    """
    Extracts promotional claims and promoted site from caption text using Gemini LLM.
    Includes exponential backoff retry for transient 429/5xx errors.
    Fails gracefully on retry exhaustion without crashing the caller.
    """
    if not caption or not caption.strip():
        return ExtractionResponse(promoted_site=None, claims=[])

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={"response_mime_type": "application/json"}
    )

    template = load_prompt_template()
    prompt = template.replace("{caption}", caption)

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text or "{}"
            clean_json = clean_json_response(raw_text)
            data = json.loads(clean_json)

            if data.get("promoted_site") in ["", "null", "none", None]:
                data["promoted_site"] = None

            if "claims" in data and isinstance(data["claims"], list):
                from app.models import sanitize_category
                for item in data["claims"]:
                    if isinstance(item, dict):
                        item["category"] = sanitize_category(item.get("category"))

            return ExtractionResponse.model_validate(data)

        except Exception as e:
            if is_transient_error(e) and attempt < max_attempts - 1:
                time.sleep(2 ** (attempt + 1))  # Exponential backoff: 2s, 4s
                continue
            raise RuntimeError(f"Extraction service unavailable: {str(e)}")


