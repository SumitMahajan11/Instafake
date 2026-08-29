from typing import List, Optional, Literal
from pydantic import BaseModel, Field

ClaimCategory = Literal[
    "price",
    "certificate",
    "partnership",
    "eligibility",
    "deadline",
    "salary",
    "discount",
    "refund",
    "other"
]

VALID_CLAIM_CATEGORIES = {
    "price", "certificate", "partnership", "eligibility",
    "deadline", "salary", "discount", "refund", "other"
}

CATEGORY_SYNONYMS = {
    "pricing": "price",
    "cost": "price",
    "fee": "price",
    "fees": "price",
    "discounts": "discount",
    "refunds": "refund",
    "certification": "certificate",
    "credentials": "certificate",
    "endorsed": "partnership",
    "partner": "partnership",
    "prerequisites": "eligibility",
    "qualification": "eligibility",
    "stipend": "salary",
    "compensation": "salary",
    "pay": "salary"
}

def sanitize_category(val: Optional[str]) -> str:
    if not val:
        return "other"
    cat = str(val).strip().lower()
    if cat in VALID_CLAIM_CATEGORIES:
        return cat
    return CATEGORY_SYNONYMS.get(cat, "other")

def is_transient_error(e: Exception) -> bool:
    """
    Determines if an exception is a transient error suitable for retry:
    - 429 Rate Limit / Quota / ResourceExhausted / TooManyRequests
    - Transient 5xx server errors (500, 502, 503, 504)
    Returns False for non-transient errors (400 Bad Request, 401 Unauthorized, 403 Forbidden, safety/content filters).
    """
    err_str = f"{type(e).__name__}: {str(e)}".lower()

    # Non-retryable error signatures (400, 401, 403, client invalid input, content policy/safety blocks)
    non_retryable = [
        "400", "bad request", "invalid_argument", "invalidargument",
        "401", "unauthorized",
        "403", "forbidden", "permission_denied", "permissiondenied",
        "safety", "blocked", "content_filter", "recitation"
    ]
    if any(sig in err_str for sig in non_retryable):
        return False

    # Retryable error signatures (429 rate limit/quota and 5xx server errors)
    retryable = [
        "429", "resourceexhausted", "resource_exhausted", "toomanyrequests", "quota", "too many requests", "rate limit",
        "500", "502", "503", "504", "internalservererror", "internal server error", "serviceunavailable", "service unavailable",
        "badgateway", "bad gateway", "gatewaytimeout", "gateway timeout", "overloaded", "transient"
    ]
    if any(sig in err_str for sig in retryable):
        return True

    return False


ConfidenceLevel = Literal["high", "medium", "low"]

# Phase 1 Models

class Claim(BaseModel):
    category: ClaimCategory = Field(..., description="Category of the claim")
    text: str = Field(..., description="Specific text description of the extracted claim")
    confidence: ConfidenceLevel = Field(..., description="Confidence level: high, medium, or low")
    source_type: Literal["caption", "comment"] = Field("caption", description="Origin of the claim: caption or comment")

class ExtractionRequest(BaseModel):
    caption: str = Field(..., description="Raw promotional social media caption text")

class ExtractionResponse(BaseModel):
    promoted_site: Optional[str] = Field(None, description="Promoted website URL, domain, or handle mentioned in caption; null if none mentioned")
    claims: List[Claim] = Field(default_factory=list, description="List of extracted claims")


# Phase 2 Models
PageType = Literal["home", "pricing", "terms", "faq", "registration", "refund_policy"]

class SiteFact(BaseModel):
    category: ClaimCategory = Field(..., description="Category of the extracted fact")
    text: str = Field(..., description="Extracted fact statement from website page")
    source_page: str = Field(..., description="Standardized page type where fact was found (e.g. home, pricing, faq)")
    source_url: str = Field(..., description="Exact URL of the source page")

class CrawlRequest(BaseModel):
    url: str = Field(..., description="Target website URL to crawl")

class CrawlResponse(BaseModel):
    site_url: str = Field(..., description="Base target site URL")
    pages_found: List[str] = Field(default_factory=list, description="List of standardized page types successfully discovered and crawled")
    pages_missing: List[str] = Field(default_factory=list, description="List of standardized page types not found or uncrawled")
    facts: List[SiteFact] = Field(default_factory=list, description="All extracted facts from crawled pages")
    crawl_status: Literal["success", "blocked", "failed", "degraded", "busy", "overloaded"] = Field(..., description="Overall crawl execution status")


# Phase 3 Models (Cross-Check Engine)
VerdictType = Literal["confirmed", "contradicted", "partial", "not_found"]

class ClaimVerdict(BaseModel):
    claim_text: str = Field(..., description="Text of the evaluated claim")
    category: ClaimCategory = Field(..., description="Category of the claim")
    source_type: Literal["caption", "comment"] = Field("caption", description="Origin of the claim")
    verdict: VerdictType = Field(..., description="Cross-check verdict: confirmed, contradicted, partial, or not_found")
    evidence_text: Optional[str] = Field(None, description="Exact quoted text from site fact used as evidence, or null if not_found")
    source_url: Optional[str] = Field(None, description="Source page URL where evidence was found, or null")
    reasoning: str = Field(..., description="One sentence explanation of the verdict")

class ScoreBreakdown(BaseModel):
    confirmed_count: int = Field(0, description="Number of confirmed claims")
    partial_count: int = Field(0, description="Number of partially supported claims")
    contradicted_count: int = Field(0, description="Number of contradicted claims")
    not_found_count: int = Field(0, description="Number of claims with no supporting/contradicting evidence found")
    addressed_claims: int = Field(0, description="Number of claims addressed by site facts (confirmed + partial + contradicted)")
    total_claims: int = Field(0, description="Total number of evaluated claims")

class CheckRequest(BaseModel):
    claims: List[Claim] = Field(..., description="List of extracted claims from Phase 1")
    site_facts: List[SiteFact] = Field(..., description="List of extracted site facts from Phase 2")

class CheckResponse(BaseModel):
    trust_score: Optional[float] = Field(None, description="Calculated trust score (0.0 - 100.0%) for addressed claims, or null if unverified/no data")
    coverage_status: Literal["verified", "partially_verified", "unverified_no_data"] = Field(..., description="Overall evidence coverage status")
    summary_label: str = Field(..., description="Explainable, non-defamatory summary of claims vs evidence")
    score_breakdown: ScoreBreakdown = Field(..., description="Detailed breakdown of verdict counts")
    verdicts: List[ClaimVerdict] = Field(..., description="List of verdicts per claim")

class FullAuditRequest(BaseModel):
    caption: str = Field(..., description="Social media post caption")
    override_url: Optional[str] = Field(None, description="Optional target URL to crawl if not extracted from caption")

class FullAuditResponse(BaseModel):
    caption: str = Field(..., description="Input caption")
    promoted_site: Optional[str] = Field(None, description="Promoted website URL")
    claims: List[Claim] = Field(default_factory=list, description="Extracted claims")
    crawl_status: Optional[str] = Field(None, description="Crawl status")
    check_result: Optional[CheckResponse] = Field(None, description="Cross-check verification response")

