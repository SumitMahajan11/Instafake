import os
import re
import json
import time
import logging
import threading
import psutil
from pathlib import Path

PLAYWRIGHT_LOCK = threading.Lock()
# Configurable timeouts for the lock
LOCK_WAIT_TIMEOUT = float(os.getenv("PW_LOCK_WAIT_TIMEOUT", "3"))     # seconds to wait before returning "busy"
LOCK_HOLD_TIMEOUT = float(os.getenv("PW_LOCK_HOLD_TIMEOUT", "45"))    # hard kill if a single PW job exceeds this
PW_MEMORY_LIMIT_MB = float(os.getenv("PW_MEMORY_LIMIT_MB", "400"))    # Memory threshold in MB for circuit breaker
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse, urljoin
import urllib.robotparser
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger("reelclaim.crawler")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

from app.models import SiteFact, CrawlResponse, is_transient_error

# Load environment variables
load_dotenv()

PROMPT_FILE = Path(__file__).parent / "prompts" / "fact_extraction.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 (compatible; ReelClaimBot/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
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

def is_allowed_by_robots(url: str, user_agent: str = "ReelClaimBot") -> bool:
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

def _flatten_json_strings(data) -> List[str]:
    """Recursively flattens dicts/lists to extract human-readable string values."""
    strings = []
    if isinstance(data, dict):
        for k, v in data.items():
            # Skip internal framework / build noise keys
            if k in ["buildId", "assetPrefix", "runtimeConfig", "page", "query", "@context", "pageProps_ssgManifest"]:
                continue
            strings.extend(_flatten_json_strings(v))
    elif isinstance(data, list):
        for item in data:
            strings.extend(_flatten_json_strings(item))
    elif isinstance(data, str):
        val = data.strip()
        # Filter out URLs, static asset paths, base64 strings, CSS/JS files, hashes/UUIDs
        if len(val) >= 3 and not val.startswith(("http://", "https://", "/", "data:", "blob:")):
            if not re.search(r"\.(png|jpg|jpeg|svg|webp|gif|css|js|ico|woff|woff2|ttf|eot)$", val, re.I):
                if not re.match(r"^[0-9a-fA-F\-]{16,}$", val):  # ignore hex hashes & UUIDs
                    strings.append(val)
    return strings

def extract_embedded_json_text(html_content: str) -> str:
    """
    Extracts clean human-readable text from embedded JSON scripts
    specifically targeting Next.js (__NEXT_DATA__), Nuxt (__NUXT_DATA__),
    and JSON-LD schema (application/ld+json) blocks.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    extracted_chunks: List[str] = []

    # Target specific embedded data scripts: Next.js __NEXT_DATA__, Nuxt __NUXT_DATA__, and application/ld+json
    next_data_scripts = soup.find_all("script", id="__NEXT_DATA__")
    nuxt_data_scripts = soup.find_all("script", id="__NUXT_DATA__")
    ld_json_scripts = soup.find_all("script", type=re.compile(r"application/ld\+json", re.IGNORECASE))

    seen_elements = set()
    scripts_to_process = []
    for s in next_data_scripts + nuxt_data_scripts + ld_json_scripts:
        if id(s) not in seen_elements:
            seen_elements.add(id(s))
            scripts_to_process.append(s)

    for script in scripts_to_process:
        raw_js = script.string or script.get_text()
        if not raw_js or not raw_js.strip():
            continue

        try:
            data = json.loads(raw_js.strip())
            strings = _flatten_json_strings(data)
            extracted_chunks.extend(strings)
        except Exception:
            continue

    # Deduplicate extracted phrases while preserving order
    seen_phrases = set()
    unique_phrases = []
    for phrase in extracted_chunks:
        if phrase not in seen_phrases:
            seen_phrases.add(phrase)
            unique_phrases.append(phrase)

    return " ".join(unique_phrases)

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
        
        # 1. Extract JSON embedded text before script tags are stripped
        json_text = extract_embedded_json_text(html)

        # 2. Extract clean DOM text (which strips script tags)
        dom_text = extract_clean_text_from_html(html)

        # Combine DOM text and JSON text
        if dom_text and json_text:
            clean_text = f"{dom_text} {json_text}".strip()
        elif json_text:
            clean_text = json_text
        else:
            clean_text = dom_text

        # Check if page is a JS shell (very little readable text content)
        if len(clean_text) < 200 and allow_playwright:
            # Fallback to Playwright for JS rendering (atomic non-blocking acquire inside)
            clean_text_pw, pw_status = fetch_page_with_playwright(url)
            if pw_status in ["success", "degraded"] and clean_text_pw and len(clean_text_pw) >= len(clean_text):
                return clean_text_pw, "playwright", pw_status
            elif pw_status == "blocked":
                return None, "playwright", "blocked"
            elif pw_status == "busy":
                return None, "playwright", "busy"
            else:
                return clean_text, "playwright", pw_status if pw_status in ["failed", "overloaded"] else "failed"

        return clean_text, "requests", "success"

    except requests.exceptions.RequestException as e:
        if "403" in str(e) or "429" in str(e):
            return None, "requests", "blocked"
        return None, "requests", "failed"

import queue

class _PlaywrightBrowserManager:
    """
    Singleton manager for the shared Playwright Chromium browser instance.
    
    Lifecycle:
        - Launched lazily on first request (on call to execute()).
        - Kept alive as a module-level singleton process across requests.
        - Each request creates and closes its own isolated browser context (browser.new_context()).
        - If the browser dies or crashes (or is killed on hard hold timeout), the manager detects
          the dead browser state, closes stale driver handles, and relaunches a fresh Chromium
          browser process on the subsequent request.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._work_q: Optional[queue.Queue] = None
        self._thread: Optional[threading.Thread] = None
        self.browser = None
        self.pw = None

    def _ensure_started(self):
        if self._thread and self._thread.is_alive() and self.browser:
            try:
                if self.browser.is_connected():
                    return
            except Exception:
                pass
        self.close()
        self._work_q = queue.Queue()
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        # Wait for initial launch signal
        res_q = queue.Queue()
        self._work_q.put((lambda b: True, res_q))
        res_q.get(timeout=15)

    def _worker_loop(self):
        try:
            from playwright.sync_api import sync_playwright
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-first-run",
                    "--disable-extensions",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            while True:
                item = self._work_q.get()
                if item is None:
                    break
                fn, res_q = item
                try:
                    res = fn(self.browser)
                    res_q.put((res, None))
                except Exception as e:
                    res_q.put((None, e))
        except Exception as e:
            logger.error(f"Playwright browser manager loop error: {e}")
        finally:
            self._cleanup()

    def _cleanup(self):
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self.pw:
            try:
                self.pw.stop()
            except Exception:
                pass
            self.pw = None

    def close(self):
        """Forces immediate shutdown and cleanup of the shared browser instance."""
        q = self._work_q
        t = self._thread
        self._work_q = None
        self._thread = None
        self.browser = None
        self.pw = None

        if q:
            try:
                q.put(None)
            except Exception:
                pass
        if t and t.is_alive() and threading.current_thread() != t:
            try:
                t.join(timeout=3)
            except Exception:
                pass

    def execute(self, fn, timeout: float = 30.0):
        with self._lock:
            self._ensure_started()
            res_q = queue.Queue()
            self._work_q.put((fn, res_q))
            try:
                res, err = res_q.get(timeout=timeout)
                if err:
                    err_msg = str(err)
                    if "Target" in err_msg or "closed" in err_msg or "connection" in err_msg or not (self.browser and self.browser.is_connected()):
                        logger.warning("Detected dead/closed browser instance in manager. Relaunching...")
                        self.close()
                        self._ensure_started()
                        res_q2 = queue.Queue()
                        self._work_q.put((fn, res_q2))
                        res, err2 = res_q2.get(timeout=timeout)
                        if err2:
                            raise err2
                        return res
                    raise err
                return res
            except Exception as e:
                self.close()
                raise e

_BROWSER_MANAGER = _PlaywrightBrowserManager()

def _run_playwright_inner(url: str) -> Tuple[Optional[str], str]:
    """Inner Playwright work — runs on the dedicated browser manager thread with per-request context creation."""
    def _fetch_page(browser):
        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            extra_http_headers={
                "Accept-Language": HEADERS["Accept-Language"]
            }
        )
        try:
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
            context.close()

    try:
        return _BROWSER_MANAGER.execute(_fetch_page, timeout=LOCK_HOLD_TIMEOUT)
    except Exception as e:
        logger.error(f"Playwright fetch error: {e}")
        return None, "failed"


def fetch_page_with_playwright(url: str) -> Tuple[Optional[str], str]:
    """
    Fallback fetch strategy using Playwright headless browser.

    Lock behaviour:
        - Bounded wait: blocks up to LOCK_WAIT_TIMEOUT (default 3 s) before
          returning "busy".  This eliminates false negatives for requests that
          miss the lock by milliseconds.
        - Hard hold timeout: if the Playwright job exceeds LOCK_HOLD_TIMEOUT
          (default 45 s), the worker thread is abandoned and the lock is
          released so the next request can proceed.
    """
    # Circuit Breaker: Check memory usage before proceeding
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_mb = mem_info.rss / (1024 * 1024)
    if mem_mb > PW_MEMORY_LIMIT_MB:
        logger.warning(
            "playwright_circuit_breaker | url=%s | mem_mb=%.1f (limit=%.1f) — returning overloaded",
            url, mem_mb, PW_MEMORY_LIMIT_MB
        )
        return None, "overloaded"

    wait_start = time.monotonic()
    acquired = PLAYWRIGHT_LOCK.acquire(timeout=LOCK_WAIT_TIMEOUT)
    lock_wait = time.monotonic() - wait_start

    if not acquired:
        logger.warning(
            "playwright_lock_busy | url=%s | waited=%.3fs (timeout=%.1fs) — returning busy",
            url, lock_wait, LOCK_WAIT_TIMEOUT,
        )
        return None, "busy"

    logger.info(
        "playwright_lock_acquired | url=%s | waited=%.3fs",
        url, lock_wait,
    )

    hold_start = time.monotonic()
    # Container for the result from the worker thread
    result_box: List[Tuple[Optional[str], str]] = []

    def _worker():
        try:
            result_box.append(_run_playwright_inner(url))
        except Exception:
            result_box.append((None, "failed"))

    worker = threading.Thread(target=_worker, daemon=True)
    worker.start()
    worker.join(timeout=LOCK_HOLD_TIMEOUT)
    hold_time = time.monotonic() - hold_start

    if worker.is_alive():
        # Hard timeout: the worker is still running past the limit.
        # We log a critical warning and release the lock so the queue
        # isn't permanently starved.  The daemon thread will eventually
        # be cleaned up when the browser process dies.
        logger.critical(
            "playwright_lock_timeout_killed | url=%s | held=%.1fs (limit=%.1fs) — releasing lock and resetting browser singleton",
            url, hold_time, LOCK_HOLD_TIMEOUT,
        )
        _BROWSER_MANAGER.close()
        PLAYWRIGHT_LOCK.release()
        return None, "failed"

    PLAYWRIGHT_LOCK.release()
    logger.info(
        "playwright_lock_released | url=%s | held=%.3fs",
        url, hold_time,
    )

    if result_box:
        return result_box[0]
    return None, "failed"

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

def extract_facts_from_page(page_text: str, page_type: str, source_url: str, api_key: Optional[str] = None) -> List[SiteFact]:
    """
    Extracts structured facts from a web page text using Gemini LLM.
    Supports per-request BYOK api_key with fallback to GEMINI_API_KEY env var.
    """
    if not page_text or len(page_text.strip()) < 50:
        return []

    # Limit text length sent to LLM per page to 6000 chars for efficiency
    truncated_text = page_text[:6000]

    effective_api_key = (api_key.strip() if api_key and api_key.strip() else None) or os.getenv("GEMINI_API_KEY")
    if not effective_api_key:
        raise ValueError("GEMINI_API_KEY environment variable missing.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    genai.configure(api_key=effective_api_key)

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
            if is_transient_error(e) and attempt < max_attempts - 1:
                time.sleep(2 ** (attempt + 1))  # Exponential backoff: 2s, 4s
                continue
            return []
    return []


def crawl_site(target_url: str, api_key: Optional[str] = None) -> CrawlResponse:
    """
    Crawls a target website, discovers key pages, extracts facts per page,
    and returns a structured CrawlResponse.
    Supports BYOK per-request api_key.
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
            page_facts = extract_facts_from_page(clean_text, ptype, page_url, api_key=api_key)
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
