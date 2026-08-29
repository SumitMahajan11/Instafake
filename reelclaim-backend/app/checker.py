import os
import re
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional
from difflib import SequenceMatcher
import google.generativeai as genai
from dotenv import load_dotenv

from app.models import (
    Claim,
    SiteFact,
    ClaimVerdict,
    ScoreBreakdown,
    CheckResponse,
    VerdictType,
    ClaimCategory,
    is_transient_error
)

load_dotenv()


PROMPT_FILE = Path(__file__).parent / "prompts" / "claim_verification.txt"

CATEGORY_ALIASES = {
    "price": ["price", "discount", "refund", "terms", "other"],
    "discount": ["discount", "price", "terms", "other"],
    "refund": ["refund", "terms", "price", "other"],
    "certificate": ["certificate", "terms", "faq", "other"],
    "eligibility": ["eligibility", "terms", "faq", "other"],
    "deadline": ["deadline", "terms", "faq", "other"],
    "partnership": ["partnership", "faq", "other"],
    "salary": ["salary", "faq", "other"],
    "other": ["other"]
}

def load_verification_prompt_template() -> str:
    """Reads the prompt template file at runtime."""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Verification prompt template not found at {PROMPT_FILE}")
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()

def clean_json_response(raw_text: str) -> str:
    """Strips markdown code blocks from JSON string."""
    text = raw_text.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return text

def normalize_text_for_comparison(text: str) -> str:
    """Normalizes text by removing non-alphanumeric chars and lowercasing."""
    return re.sub(r"[^\w\s]", "", text).lower().strip()

CRITICAL_QUALIFIERS = [
    "no questions asked",
    "unconditional",
    "free forever",
    "instant refund",
    "guaranteed job",
    "no degree required",
    "no fees ever",
    "without condition"
]

def is_valid_evidence_text(evidence_text: Optional[str], available_facts: List[SiteFact]) -> bool:
    """
    Calibrated Anti-Hallucination & Embellishment Guardrail:
    Accepts exact substring, normalized substring, or slight paraphrases.
    REJECTS complete fabrications and embellished quotes with unsupported key clauses.
    """
    if not evidence_text or not evidence_text.strip():
        return False

    norm_evidence = normalize_text_for_comparison(evidence_text)
    tokens_ev = set(norm_evidence.split())
    if len(tokens_ev) == 0:
        return False

    # Embellishment check: reject if evidence contains a critical qualifier missing from ALL site facts
    evidence_lower = evidence_text.lower()
    for qualifier in CRITICAL_QUALIFIERS:
        if qualifier in evidence_lower:
            if not any(qualifier in fact.text.lower() for fact in available_facts):
                # Critical embellishment detected and missing from source facts!
                return False

    for fact in available_facts:
        raw_fact_lower = fact.text.lower()
        norm_fact = normalize_text_for_comparison(fact.text)
        tokens_fact = set(norm_fact.split())

        # 1. Exact raw or normalized substring
        if evidence_text.strip().lower() in raw_fact_lower or norm_evidence in norm_fact or norm_fact in norm_evidence:
            return True

        # 2. High sequence similarity (ratio > 0.65)
        if SequenceMatcher(None, norm_evidence, norm_fact).ratio() > 0.65:
            return True

        # 3. High token overlap check (>= 75% of evidence words exist in fact)
        if len(tokens_ev) >= 2:
            overlap = len(tokens_ev.intersection(tokens_fact)) / len(tokens_ev)
            if overlap >= 0.70:
                return True

    return False

def get_candidate_facts_for_claim(claim: Claim, all_site_facts: List[SiteFact]) -> List[SiteFact]:
    """
    Pass 1 (Prioritized Category Filter):
    Gather facts prioritized by category relevance:
    1. Exact category matches
    2. Category alias matches
    3. Remaining site facts (prevents category-mismatch shadowing when facts are misclassified)
    """
    if not all_site_facts:
        return []

    exact_matches = [f for f in all_site_facts if f.category == claim.category]
    aliases = CATEGORY_ALIASES.get(claim.category, ["other"])

    seen_ids = {id(f) for f in exact_matches}
    alias_matches = []
    for f in all_site_facts:
        if f.category in aliases and id(f) not in seen_ids:
            alias_matches.append(f)
            seen_ids.add(id(f))

    remaining_facts = [f for f in all_site_facts if id(f) not in seen_ids]

    return exact_matches + alias_matches + remaining_facts

def verify_single_claim(claim: Claim, all_site_facts: List[SiteFact]) -> ClaimVerdict:
    """
    Two-pass claim verification:
    Pass 1: Gather facts via category + alias matching.
    Pass 2: LLM reasoning for verdict generation.
    Pass 3: Calibrated programmatic evidence verification.
    """
    relevant_facts = get_candidate_facts_for_claim(claim, all_site_facts)

    if not relevant_facts:
        return ClaimVerdict(
            claim_text=claim.text,
            category=claim.category,
            source_type=claim.source_type,
            verdict="not_found",
            evidence_text=None,
            source_url=None,
            reasoning=f"No site facts found under category '{claim.category}' or its aliases."
        )

    # Pass 2: LLM Reasoning
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={"response_mime_type": "application/json"}
    )

    facts_formatted = json.dumps([
        {"text": f.text, "source_page": f.source_page, "source_url": f.source_url, "category": f.category}
        for f in relevant_facts
    ], indent=2)

    current_date_str = datetime.now().strftime("%B %d, %Y")
    template = load_verification_prompt_template()
    prompt = template.replace("{claim_text}", claim.text)\
                     .replace("{category}", claim.category)\
                     .replace("{current_date}", current_date_str)\
                     .replace("{filtered_facts}", facts_formatted)

    max_attempts = 3
    raw_data = None
    for attempt in range(max_attempts):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text or "{}"
            clean_json = clean_json_response(raw_text)
            raw_data = json.loads(clean_json)
            break
        except Exception as e:
            if is_transient_error(e) and attempt < max_attempts - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            return ClaimVerdict(
                claim_text=claim.text,
                category=claim.category,
                source_type=claim.source_type,
                verdict="not_found",
                evidence_text=None,
                source_url=None,
                reasoning=f"Verification service unavailable: {str(e)}"
            )


    if not raw_data:
        return ClaimVerdict(
            claim_text=claim.text,
            category=claim.category,
            source_type=claim.source_type,
            verdict="not_found",
            evidence_text=None,
            source_url=None,
            reasoning="Empty response from verification model."
        )

    verdict_val: VerdictType = raw_data.get("verdict", "not_found")
    evidence_text: Optional[str] = raw_data.get("evidence_text")
    source_url: Optional[str] = raw_data.get("source_url")
    reasoning: str = raw_data.get("reasoning", "Evaluated based on site facts.")

    # Pass 3: Calibrated Evidence Verification (Anti-Hallucination & Embellishment Filter)
    if verdict_val != "not_found" and evidence_text:
        valid = is_valid_evidence_text(evidence_text, relevant_facts)
        if not valid:
            verdict_val = "not_found"
            evidence_text = None
            source_url = None
            reasoning = "Evidence quotation provided by verification model was rejected (hallucinated or embellished with unsupported clauses)."

    if verdict_val == "not_found":
        evidence_text = None
        source_url = None

    return ClaimVerdict(
        claim_text=claim.text,
        category=claim.category,
        source_type=claim.source_type,
        verdict=verdict_val,
        evidence_text=evidence_text,
        source_url=source_url,
        reasoning=reasoning
    )

def calculate_trust_score(verdicts: List[ClaimVerdict]) -> Tuple[Optional[float], str, str, ScoreBreakdown]:
    """
    Calculates trust score over ADDRESSED claims (confirmed, partial, contradicted).
    If 0 claims are addressed by site facts, returns trust_score = None and summary 'Unverified'.
    Produces distinct, alarming labels for contradicted claims.
    """
    total_claims = len(verdicts)
    confirmed_count = sum(1 for v in verdicts if v.verdict == "confirmed")
    partial_count = sum(1 for v in verdicts if v.verdict == "partial")
    contradicted_count = sum(1 for v in verdicts if v.verdict == "contradicted")
    not_found_count = sum(1 for v in verdicts if v.verdict == "not_found")
    addressed_claims = confirmed_count + partial_count + contradicted_count

    breakdown = ScoreBreakdown(
        confirmed_count=confirmed_count,
        partial_count=partial_count,
        contradicted_count=contradicted_count,
        not_found_count=not_found_count,
        addressed_claims=addressed_claims,
        total_claims=total_claims
    )

    if total_claims == 0 or addressed_claims == 0:
        return None, "unverified_no_data", f"Unverified: Site facts do not address any of the {total_claims} reel claims.", breakdown

    raw_score = (confirmed_count * 1.0 + partial_count * 0.5 - contradicted_count * 1.0) / addressed_claims
    trust_score = round(max(0.0, min(100.0, raw_score * 100.0)), 1)

    parts = []
    parts.append(f"{confirmed_count} confirmed")
    if contradicted_count > 0:
        parts.append(f"{contradicted_count} contradicted")
    if partial_count > 0:
        parts.append(f"{partial_count} partial")
    if not_found_count > 0:
        parts.append(f"{not_found_count} unaddressed")

    summary_label = f"Audit summary: {', '.join(parts)} out of {total_claims} claims evaluated."

    if addressed_claims < total_claims:
        coverage_status = "partially_verified"
    else:
        coverage_status = "verified"

    return trust_score, coverage_status, summary_label, breakdown

def cross_check_claims(claims: List[Claim], site_facts: List[SiteFact]) -> CheckResponse:
    """
    Executes cross-checking for a list of claims against site facts.
    Returns CheckResponse with verdicts, trust score, and coverage status.
    """
    verdicts: List[ClaimVerdict] = []

    for claim in claims:
        verdict = verify_single_claim(claim, site_facts)
        verdicts.append(verdict)
        time.sleep(1.0)

    trust_score, coverage_status, summary_label, breakdown = calculate_trust_score(verdicts)

    return CheckResponse(
        trust_score=trust_score,
        coverage_status=coverage_status,
        summary_label=summary_label,
        score_breakdown=breakdown,
        verdicts=verdicts
    )

