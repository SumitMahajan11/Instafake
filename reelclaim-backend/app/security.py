import re
import logging
from typing import Optional

logger = logging.getLogger("reelclaim.security")

SUSPICIOUS_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|directives|prompts|rules)",
    r"override\s+(system\s+)?(instructions|prompt|directives|rules)",
    r"system\s+(prompt|instruction|directive)\s*:",
    r"mark\s+(all\s+)?claims\s+as\s+(confirmed|verified|true)",
    r"you\s+are\s+now\s+a",
    r"disregard\s+(all\s+)?(prior|previous)\s+rules",
    r"new\s+instruction\s*:",
    r"<system_instruction>",
    r"\[system_instruction\]",
    r"forget\s+all\s+prior\s+instructions"
]


def check_for_prompt_injection(text: Optional[str], source_identifier: str = "untrusted_content") -> bool:
    """
    Sanity check for prompt injection patterns in untrusted inputs (crawled web facts, captions).
    Logs a security warning if suspicious instruction-like patterns are detected.
    Returns True if a suspicious pattern is detected, False otherwise.
    """
    if not text:
        return False

    text_lower = text.lower()
    for pattern in SUSPICIOUS_INJECTION_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            start_idx = max(0, match.start() - 20)
            end_idx = min(len(text), match.end() + 20)
            snippet = text[start_idx:end_idx].replace("\n", " ")
            logging.warning(
                f"SECURITY WARNING: Potential prompt injection pattern '{match.group(0)}' detected in {source_identifier}. "
                f"Snippet: '{snippet}'"
            )
            return True

    return False
