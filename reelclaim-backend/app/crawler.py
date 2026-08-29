import os
import re
import json
import time
import threading
from pathlib import Path

PLAYWRIGHT_LOCK = threading.Lock()
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse, urljoin
import urllib.robotparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

from app.models import SiteFact, CrawlResponse

# Load environment variables
load_dotenv()

PROMPT_FILE = Path(__file__).parent / "prompts" / "fact_extraction.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ReelClaimBot/1.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
}

TARGET_PAGE_TYPES = ["home", "pricing", "terms", "faq", "registration", "refund_policy"]

# Keyword patterns for page type matching
PAGE_PATTERNS = {
    "pricing": [r"pric", r"plan", r"cost", r"fee", r"tarif"],
    "terms": [r"term", r"tos", r"condition", r"legal"],
    "faq": [r"faq", r"help", r"question", r"support"],
    "registration": [r"register", r"signup", r"sign-up", r"join", r"enroll", r"apply"],
    "refund_policy": [r"refund", r"cancellation", r"return-policy", r"cancel"]
}

def load_prompt_template() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Fact extraction prompt not found at {PROMPT_FILE}")
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()

def clean_json_response(raw_text: str) -> str:
    text = raw_text.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return text

def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url.rstrip("/")

def is_same_domain(url1: str, url2: str) -> bool:
    parsed1 = urlparse(url1)
    parsed2 = urlparse(url2)
    domain1 = parsed1.netloc.replace("www.", "")
    domain2 = parsed2.netloc.replace("www.", "")
    return domain1 == domain2

def is_allowed_by_robots(url: str, user_agent: str = "*") -> bool:
    """Checks robots.txt for permission using requests with custom User-Agent."""
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        resp = requests.get(robots_url, headers=HEADERS, timeout=5, allow_redirects=True)
        if resp.status_code == 404:
            return True  # No robots.txt means allowed
        if resp.status_code != 200:
            return True  # If robots.txt cannot be fetched, default to allowed
            
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(resp.text.splitlines())
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True

def extract_clean_text_from_html(html_content: str) -> str:
    """Strips tags, scripts, and styles, returning clean body text."""
    soup = BeautifulSoup(html_content, "html.parser")
    for element in soup(["script", "style", "noscript", "header", "footer", "svg"]):
        element.decompose()
    text = soup.get_text(separator=" ")
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return " ".join(chunk for chunk in chunks if chunk)

def fetch_page_content(url: str, allow_playwright: bool = True) -> Tuple[Optional[str], str, str]:
    """
    Fetches web page content.
    Returns: (clean_text, strategy_used, status)
    strategy_used: 'requests' | 'playwright'
    status: 'success' | 'blocked' | 'failed'
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        
        # Explicit Anti-Bot / WAF Challenge Detection:
        # 1. HTTP 403 Forbidden or 429 Rate Limited / Bot Challenge
        # 2. WAF Headers (CF-Ray, Cloudflare server, Akamai, Incapsula)
        # 3. HTML challenge signatures ("Just a moment...", "Attention Required!", "Access Denied")
        server_header = resp.headers.get("Server", "").lower()
        has_waf_header = any(k in resp.headers for k in ["CF-RAY", "cf-ray", "x-akamai-transformed", "incap-ses"]) or "cloudflare" in server_header
        has_challenge_body = any(sig in resp.text.lower() for sig in ["just a moment...", "attention required!", "cf-browser-verification", "bot challenge", "access denied"])

        if resp.status_code in [403, 429] or (resp.status_code in [401, 503] and (has_waf_header or has_challenge_body)):
            return None, "requests", "blocked"
        if resp.status_code >= 400:
            return None, "requests", "failed"

        html = resp.text
        clean_text = extract_clean_text_from_html(html)

        # Check if page is a JS shell (very little readable text content)
        if len(clean_text) < 200 and allow_playwright:
            # Fallback to Playwright for JS rendering (atomic non-blocking acquire inside)
            clean_text_pw, pw_status = fetch_page_with_playwright(url)
            if pw_status in ["success", "degraded"] and clean_text_pw and len(clean_text_pw) > len(clean_text):
                return clean_text_pw, "playwright", pw_status
            elif pw_status == "blocked":
                return None, "playwright", "blocked"
            elif pw_status == "busy":
                return None, "playwright", "busy"

        return clean_text, "requests", "success"

    except requests.exceptions.RequestException as e:
        if "403" in str(e) or "429" in str(e):
            return None, "requests", "blocked"
        return None, "requests", "failed"

def fetch_page_with_playwright(url: str) -> Tuple[Optional[str], str]:
    """Fallback fetch strategy using Playwright headless browser."""
    acquired = PLAYWRIGHT_LOCK.acquire(blocking=False)
    if not acquired:
        # Playwright browser is busy processing another request; return busy status immediately (0ms wait)
        return None, "busy"

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-zygote",
                    "--single-process",
                    "--no-first-run",
                    "--disable-extensions"
                ]
            )
            try:
                context = browser.new_context(user_agent=HEADERS["User-Agent"])
                page = context.new_page()
                is_degraded = False
                try:
                    response = page.goto(url, timeout=6000, wait_until="domcontentloaded")
                    if response and response.status in [403, 401, 429]:
                        return None, "blocked"
                except Exception as pe:
                    if "403" in str(pe) or "401" in str(pe):
                        return None, "blocked"
                    # On timeout or partial load, mark as degraded
                    is_degraded = True

                page.wait_for_timeout(500)
                content = page.content()
                clean_text = extract_clean_text_from_html(content)
                if clean_text and len(clean_text.strip()) >= 50:
                    return clean_text, "degraded" if is_degraded else "success"
                return None, "failed"
            finally:
                browser.close()
    except Exception:
        return None, "failed"
    finally:
        PLAYWRIGHT_LOCK.release()

def discover_pages(base_url: str, homepage_html: Optional[str]) -> Dict[str, str]:
    """
    Discovers URLs for target page types using common URL patterns & homepage link text parsing.
    Returns dict mapping page_type -> url.
    """
    discovered = {"home": base_url}
    
    # 1. Look for links inside homepage HTML if available
    if homepage_html:
        soup = BeautifulSoup(homepage_html, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            link_text = a_tag.get_text().strip().lower()
            full_url = urljoin(base_url, href)

            if not is_same_domain(base_url, full_url):
                continue

            for ptype, patterns in PAGE_PATTERNS.items():
                if ptype in discovered:
                    continue
                # Check link text or href path against patterns
                for pat in patterns:
                    if re.search(pat, link_text, re.IGNORECASE) or re.search(pat, href.lower(), re.IGNORECASE):
                        discovered[ptype] = full_url
                        break

    # 2. Check standard fallback URL paths for any missing page types
    standard_paths = {
        "pricing": ["/pricing", "/plans", "/cost"],
        "terms": ["/terms", "/terms-of-service", "/tos"],
        "faq": ["/faq", "/help"],
        "registration": ["/register", "/signup", "/join"],
        "refund_policy": ["/refund-policy", "/cancellation-policy", "/refund"]
    }

    for ptype, paths in standard_paths.items():
        if ptype not in discovered:
            # We assign the primary guessed path for probing
            discovered[ptype] = urljoin(base_url, paths[0])

    return discovered

def extract_facts_from_page(page_text: str, page_type: str, source_url: str) -> List[SiteFact]:
    """Uses Gemini LLM to extract structured facts from a single page's text."""
    if not page_text or len(page_text.strip()) < 50:
        return []

    # Limit text length sent to LLM per page to 6000 chars for efficiency
    truncated_text = page_text[:6000]

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable missing.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config={"response_mime_type": "application/json"}
    )

    template = load_prompt_template()
    prompt = (
        template
        .replace("{page_type}", page_type)
        .replace("{source_url}", source_url)
        .replace("{page_text}", truncated_text)
    )

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text or "{}"
            clean_json = clean_json_response(raw_text)
            data = json.loads(clean_json)

            from app.models import sanitize_category
            facts = []
            raw_facts = data.get("facts", [])
            for item in raw_facts:
                facts.append(
                    SiteFact(
                        category=sanitize_category(item.get("category")),
                        text=item.get("text", ""),
                        source_page=page_type,
                        source_url=source_url
                    )
                )
            return facts

        except Exception as e:
            if "429" in str(e) or "Quota" in str(e) or "ResourceExhausted" in str(e):
                time.sleep(6 * (attempt + 1))
                continue
            return []
    return []

def crawl_site(target_url: str) -> CrawlResponse:
    """
    Crawls a target website, discovers key pages, extracts facts per page,
    and returns a structured CrawlResponse.
    """
    base_url = normalize_url(target_url)

    # 1. Robots.txt disallow check
    if not is_allowed_by_robots(base_url):
        return CrawlResponse(
            site_url=base_url,
            pages_found=[],
            pages_missing=TARGET_PAGE_TYPES,
            facts=[],
            crawl_status="blocked"
        )

    # 2. Fetch homepage first
    homepage_html = None
    try:
        r = requests.get(base_url, headers=HEADERS, timeout=8)
        if r.status_code in [403, 401, 429] or ("Cloudflare" in r.text and "Access denied" in r.text):
            return CrawlResponse(
                site_url=base_url,
                pages_found=[],
                pages_missing=TARGET_PAGE_TYPES,
                facts=[],
                crawl_status="blocked"
            )
        if r.status_code < 400:
            homepage_html = r.text
    except requests.exceptions.RequestException as e:
        # Check if exception was an explicit HTTP 403/429 block
        if "403" in str(e) or "429" in str(e):
            return CrawlResponse(
                site_url=base_url,
                pages_found=[],
                pages_missing=TARGET_PAGE_TYPES,
                facts=[],
                crawl_status="blocked"
            )
        # Connection refused / DNS error / timeout -> failed
        return CrawlResponse(
            site_url=base_url,
            pages_found=[],
            pages_missing=TARGET_PAGE_TYPES,
            facts=[],
            crawl_status="failed"
        )

    # 3. Discover target pages
    discovered_map = discover_pages(base_url, homepage_html)

    pages_found: List[str] = []
    pages_missing: List[str] = []
    all_facts: List[SiteFact] = []
    has_blocked = False
    has_degraded = False
    has_busy = False

    # Crawl discovered pages (sequential with small delay)
    crawled_count = 0
    pw_used = False
    for ptype, page_url in discovered_map.items():
        if crawled_count >= 5:  # Limit max pages per site crawl
            break

        clean_text, strategy, status = fetch_page_content(page_url, allow_playwright=not pw_used)
        if strategy == "playwright":
            pw_used = True
        time.sleep(0.3)  # Gentle rate limit delay

        if status == "blocked":
            has_blocked = True
            continue
        elif status == "busy":
            has_busy = True
            break  # Lock is busy; stop attempting subsequent pages in this request to avoid stacking timeouts
        elif status in ["success", "degraded"] and clean_text and len(clean_text.strip()) >= 50:
            if status == "degraded":
                has_degraded = True
            pages_found.append(ptype)
            page_facts = extract_facts_from_page(clean_text, ptype, page_url)
            all_facts.extend(page_facts)
            crawled_count += 1
            time.sleep(2.5)  # Respect Gemini free-tier rate limit (max 20 RPM)

    # Determine pages missing
    for t in TARGET_PAGE_TYPES:
        if t not in pages_found:
            pages_missing.append(t)

    # Determine crawl status
    if not pages_found and has_blocked:
        crawl_status = "blocked"
    elif not pages_found and has_busy:
        crawl_status = "busy"
    elif not pages_found:
        crawl_status = "failed"
    elif has_degraded or has_busy:
        crawl_status = "degraded"
    else:
        crawl_status = "success"

    return CrawlResponse(
        site_url=base_url,
        pages_found=pages_found,
        pages_missing=pages_missing,
        facts=all_facts,
        crawl_status=crawl_status
    )
