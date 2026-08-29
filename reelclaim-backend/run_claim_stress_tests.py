import sys
import json
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.models import Claim, SiteFact
from app.checker import (
    verify_single_claim,
    get_candidate_facts_for_claim,
    is_valid_evidence_text,
    load_verification_prompt_template,
    clean_json_response,
    is_transient_error
)
import google.generativeai as genai

load_dotenv()

def inspect_claim_verification(claim: Claim, facts: list[SiteFact]):
    relevant_facts = get_candidate_facts_for_claim(claim, facts)
    
    # 1. Direct call to LLM to capture raw un-filtered output
    api_key = os.getenv("GEMINI_API_KEY")
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
    
    template = load_verification_prompt_template()
    prompt = template.replace("{claim_text}", claim.text)\
                     .replace("{category}", claim.category)\
                     .replace("{filtered_facts}", facts_formatted)
    
    llm_raw = {}
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            clean_json = clean_json_response(response.text or "{}")
            llm_raw = json.loads(clean_json)
            break
        except Exception as e:
            if is_transient_error(e) and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            llm_raw = {"error": str(e)}

    llm_evidence = llm_raw.get("evidence_text")
    pass3_accepted = None
    if llm_raw.get("verdict") != "not_found" and llm_evidence:
        pass3_accepted = is_valid_evidence_text(llm_evidence, relevant_facts)

    # 2. Call the full pipeline function (which runs Pass 1, Pass 2, and Pass 3)
    final_verdict = verify_single_claim(claim, facts)

    return {
        "claim_text": claim.text,
        "claim_category": claim.category,
        "facts_passed_to_llm": [{"category": f.category, "text": f.text} for f in relevant_facts],
        "total_facts_in_site": len(facts),
        "facts_surfaced_count": len(relevant_facts),
        "llm_raw_verdict": llm_raw.get("verdict"),
        "llm_raw_evidence": llm_evidence,
        "llm_raw_reasoning": llm_raw.get("reasoning"),
        "pass3_accepted": pass3_accepted,
        "final_verdict": final_verdict.verdict,
        "final_evidence_text": final_verdict.evidence_text,
        "final_reasoning": final_verdict.reasoning
    }

def main():
    print("================================================================================", flush=True)
    print("REELCLAIM CLAIM ANALYSIS STRESS TEST RESULTS", flush=True)
    print("================================================================================", flush=True)

    # Stress Case 1: CONDITIONAL/SCOPED CLAIM
    case1_fact = SiteFact(category="price", text="Free forever for personal, non-commercial projects.", source_page="pricing", source_url="https://example.com/pricing")
    case1_claim = Claim(category="price", text="100% free forever for everyone.", confidence="high", source_type="caption")

    # Stress Case 2: NUMERIC PRECISION MISMATCH
    case2_fact = SiteFact(category="price", text="Plans start at $19/month.", source_page="pricing", source_url="https://example.com/pricing")
    case2_claim = Claim(category="price", text="Starts at just $9/month!", confidence="high", source_type="caption")

    # Stress Case 3: STALE/AMBIGUOUS TIME-BOUND CLAIM
    case3_fact = SiteFact(category="discount", text="Limited-time offer: 50% off, ends March 2025", source_page="promotions", source_url="https://example.com/promo")
    case3_claim = Claim(category="discount", text="Get 50% off!", confidence="high", source_type="caption")

    # Stress Case 4: NEAR-MISS EVIDENCE (Pass 3 stress test)
    case4_fact = SiteFact(category="other", text="Cancel anytime, no questions asked.", source_page="terms", source_url="https://example.com/terms")
    case4_claim = Claim(category="other", text="Cancel anytime, no fees, no questions asked, guaranteed.", confidence="high", source_type="caption")

    # Stress Case 5: CATEGORY MISMATCH (Salary claim vs Price site fact)
    case5_fact = SiteFact(category="price", text="Monthly internship stipend of $1000/month provided.", source_page="pricing", source_url="https://example.com/pricing")
    case5_fact_other = SiteFact(category="other", text="Other site info.", source_page="home", source_url="https://example.com/")
    case5_claim = Claim(category="salary", text="Earn $1000/month stipend", confidence="high", source_type="caption")

    cases = [
        ("CASE 1: CONDITIONAL/SCOPED CLAIM", case1_claim, [case1_fact]),
        ("CASE 2: NUMERIC PRECISION MISMATCH", case2_claim, [case2_fact]),
        ("CASE 3: STALE/AMBIGUOUS TIME-BOUND CLAIM", case3_claim, [case3_fact]),
        ("CASE 4: NEAR-MISS EVIDENCE (Pass 3 Stress Test)", case4_claim, [case4_fact]),
        ("CASE 5: CATEGORY MISMATCH (Salary claim vs Price site fact)", case5_claim, [case5_fact, case5_fact_other])
    ]

    for title, claim, facts in cases:
        print(f"\n--- {title} ---", flush=True)
        result = inspect_claim_verification(claim, facts)
        print(json.dumps(result, indent=2), flush=True)
        time.sleep(1.0)

if __name__ == "__main__":
    main()
