import re
from typing import Optional
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.models import (
    ExtractionRequest,
    ExtractionResponse,
    CrawlRequest,
    CrawlResponse,
    CheckRequest,
    CheckResponse,
    FullAuditRequest,
    FullAuditResponse,
    is_plausible_gemini_key
)
from app.extraction import extract_claims
from app.crawler import crawl_site
from app.checker import cross_check_claims
from app.db import (
    init_db,
    save_audit_record,
    get_audit_record_by_id,
    list_recent_audit_records
)
from app.auth import verify_api_key, register_new_api_key


# Initialize DB on module import (degrades to persistence disabled if DATABASE_URL unset)
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="ReelClaim Backend Service",
    description="Phase 1, 2, 3 & 4: Claim Extraction, Site Crawler, Cross-Check Engine & Web UI API",
    version="4.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def validate_and_get_api_key(request_key: Optional[str]) -> Optional[str]:
    """
    Validates per-request BYOK Gemini API key format if provided.
    Returns stripped key or None. Raises HTTP 400 if malformed.
    """
    if request_key and request_key.strip():
        k = request_key.strip()
        if not is_plausible_gemini_key(k):
            raise HTTPException(
                status_code=400,
                detail="Invalid Gemini API key format. Key must start with 'AIza' and be 30-60 characters long."
            )
        return k
    return None

def handle_api_exception(e: Exception, context_msg: str):
    """
    Sanitizes exception messages to ensure API keys are never logged or echoed back.
    Maps invalid key or client errors to HTTP 400 cleanly.
    """
    err_str = str(e)
    clean_err = re.sub(r'AIza[A-Za-z0-9_\-]{30,60}', '[REDACTED]', err_str)
    err_lower = clean_err.lower()

    if any(term in err_lower for term in ["invalid_argument", "api_key", "apikey", "invalid api key", "unauthorized", "permission_denied", "api key not valid"]):
        raise HTTPException(status_code=400, detail=f"Gemini API key rejected: {clean_err}")
    raise HTTPException(status_code=500, detail=f"{context_msg}: {clean_err}")

class RegisterKeyRequest(BaseModel):
    name: str = Field(..., description="User or application name for this API key")
    rate_limit_per_hour: int = Field(10, ge=1, le=1000, description="Allowed requests per hour")

@app.post("/auth/register-key")
def register_key_endpoint(request: RegisterKeyRequest):
    """
    Registers a new API key for authenticating with ReelClaim service.
    Returns the plaintext API key once. Store it securely.
    """
    return register_new_api_key(name=request.name, rate_limit_per_hour=request.rate_limit_per_hour)

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "ReelClaim Backend",
        "phase": 4,
        "endpoints": [
            "POST /auth/register-key",
            "POST /extract-claims",
            "POST /crawl-site",
            "POST /check-claims",
            "POST /audit-reel",
            "GET /audits/{audit_id}",
            "GET /audits"
        ]
    }

@app.post("/extract-claims", response_model=ExtractionResponse)
def extract_claims_endpoint(request: ExtractionRequest, auth: Optional[dict] = Depends(verify_api_key)):
    """
    Phase 1: Extracts promotional claims and promoted site from a given social media reel caption.
    Supports optional BYOK per-request gemini_api_key.
    """
    api_key = validate_and_get_api_key(request.gemini_api_key)
    try:
        result = extract_claims(request.caption, api_key=api_key)
        return result
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        handle_api_exception(e, "Extraction error")

@app.post("/crawl-site", response_model=CrawlResponse)
def crawl_site_endpoint(request: CrawlRequest, auth: Optional[dict] = Depends(verify_api_key)):
    """
    Phase 2: Crawls target website, discovers key pages, and extracts verifiable facts per page.
    Supports optional BYOK per-request gemini_api_key.
    """
    api_key = validate_and_get_api_key(request.gemini_api_key)
    try:
        result = crawl_site(request.url, api_key=api_key)
        return result
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        handle_api_exception(e, "Crawl error")

@app.post("/check-claims", response_model=CheckResponse)
def check_claims_endpoint(request: CheckRequest, auth: Optional[dict] = Depends(verify_api_key)):
    """
    Phase 3: Compares extracted claims against site facts to generate verdicts and a trust score.
    Supports optional BYOK per-request gemini_api_key.
    """
    api_key = validate_and_get_api_key(request.gemini_api_key)
    try:
        result = cross_check_claims(request.claims, request.site_facts, api_key=api_key)
        return result
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        handle_api_exception(e, "Cross-check error")

@app.post("/audit-reel", response_model=FullAuditResponse)
def audit_reel_endpoint(request: FullAuditRequest, auth: Optional[dict] = Depends(verify_api_key)):
    """
    End-to-End Pipeline:
    1. Extracts claims from social caption (Phase 1)
    2. Crawls promoted website (Phase 2)
    3. Cross-checks claims against site facts (Phase 3)
    4. Persists audit result to database if DATABASE_URL is configured.
    """
    api_key = validate_and_get_api_key(request.gemini_api_key)
    try:

        # Step 1: Extract claims
        extraction = extract_claims(request.caption, api_key=api_key)
        target_url = request.override_url or extraction.promoted_site

        response = None
        if not target_url:
            response = FullAuditResponse(
                caption=request.caption,
                promoted_site=None,
                claims=extraction.claims,
                crawl_status="no_url_found",
                check_result=None
            )
        else:
            # Step 2: Crawl site
            crawl = crawl_site(target_url, api_key=api_key)
            if crawl.crawl_status in ["blocked", "failed", "busy", "overloaded", "no_url_found"]:
                response = FullAuditResponse(
                    caption=request.caption,
                    promoted_site=target_url,
                    claims=extraction.claims,
                    crawl_status=crawl.crawl_status,
                    check_result=None
                )
            else:
                # Step 3: Cross check
                check = cross_check_claims(extraction.claims, crawl.facts, api_key=api_key)
                response = FullAuditResponse(
                    caption=request.caption,
                    promoted_site=target_url,
                    claims=extraction.claims,
                    crawl_status=crawl.crawl_status,
                    check_result=check
                )

        # Step 4: Persist result to database if DB is configured
        audit_id = save_audit_record(
            caption=response.caption,
            promoted_site=response.promoted_site,
            override_url=request.override_url,
            claims=response.claims,
            crawl_status=response.crawl_status,
            check_result=response.check_result
        )

        if audit_id:
            response.id = audit_id
            response.created_at = datetime.now(timezone.utc).isoformat()

        return response
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        handle_api_exception(e, "Audit reel error")

@app.get("/audits/{audit_id}")
def get_audit_endpoint(audit_id: str):
    """
    Fetches a persisted audit record by unique ID.
    """
    record = get_audit_record_by_id(audit_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Audit record '{audit_id}' not found.")
    return record

@app.get("/audits")
def list_audits_endpoint(
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Lists recent audit records paginated, ordered by creation date descending.
    """
    return list_recent_audit_records(limit=limit, offset=offset)
