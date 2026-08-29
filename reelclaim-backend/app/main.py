from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import (
    ExtractionRequest,
    ExtractionResponse,
    CrawlRequest,
    CrawlResponse,
    CheckRequest,
    CheckResponse,
    FullAuditRequest,
    FullAuditResponse
)
from app.extraction import extract_claims
from app.crawler import crawl_site
from app.checker import cross_check_claims

app = FastAPI(
    title="ReelClaim Backend Service",
    description="Phase 1, 2, 3 & 4: Claim Extraction, Site Crawler, Cross-Check Engine & Web UI API",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "ReelClaim Backend",
        "phase": 3,
        "endpoints": ["POST /extract-claims", "POST /crawl-site", "POST /check-claims", "POST /audit-reel"]
    }

@app.post("/extract-claims", response_model=ExtractionResponse)
def extract_claims_endpoint(request: ExtractionRequest):
    """
    Phase 1: Extracts promotional claims and promoted site from a given social media reel caption.
    """
    try:
        result = extract_claims(request.caption)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction error: {str(e)}")

@app.post("/crawl-site", response_model=CrawlResponse)
def crawl_site_endpoint(request: CrawlRequest):
    """
    Phase 2: Crawls target website, discovers key pages, and extracts verifiable facts per page.
    """
    try:
        result = crawl_site(request.url)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crawl error: {str(e)}")

@app.post("/check-claims", response_model=CheckResponse)
def check_claims_endpoint(request: CheckRequest):
    """
    Phase 3: Compares extracted claims against site facts to generate verdicts and a trust score.
    """
    try:
        result = cross_check_claims(request.claims, request.site_facts)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cross-check error: {str(e)}")

@app.post("/audit-reel", response_model=FullAuditResponse)
def audit_reel_endpoint(request: FullAuditRequest):
    """
    End-to-End Pipeline:
    1. Extracts claims from social caption (Phase 1)
    2. Crawls promoted website (Phase 2)
    3. Cross-checks claims against site facts (Phase 3)
    """
    try:
        # Step 1: Extract claims
        extraction = extract_claims(request.caption)
        target_url = request.override_url or extraction.promoted_site

        if not target_url:
            return FullAuditResponse(
                caption=request.caption,
                promoted_site=None,
                claims=extraction.claims,
                crawl_status="no_url_found",
                check_result=None
            )

        # Step 2: Crawl site
        crawl = crawl_site(target_url)
        if crawl.crawl_status in ["blocked", "failed", "busy", "overloaded", "no_url_found"]:
            return FullAuditResponse(
                caption=request.caption,
                promoted_site=target_url,
                claims=extraction.claims,
                crawl_status=crawl.crawl_status,
                check_result=None
            )

        # Step 3: Cross check
        check = cross_check_claims(extraction.claims, crawl.facts)

        return FullAuditResponse(
            caption=request.caption,
            promoted_site=target_url,
            claims=extraction.claims,
            crawl_status=crawl.crawl_status,
            check_result=check
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit reel error: {str(e)}")

