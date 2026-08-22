import sys
import json
import time
import requests
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.crawler import crawl_site, fetch_page_content, HEADERS

CRAWL_TEST_CASES = [
    {
        "id": 1,
        "name": "Real Course Landing Platform (Boot.dev)",
        "url": "https://boot.dev",
        "description": "Real online learning platform with pricing, refund policy, FAQ, and terms."
    },
    {
        "id": 2,
        "name": "Real Tech Platform with Full Nav (Vercel)",
        "url": "https://vercel.com",
        "description": "Platform with pricing (/pricing), registration (/signup), terms (/legal), and FAQ (/help)."
    },
    {
        "id": 3,
        "name": "Online Learning Platform (Codecademy)",
        "url": "https://codecademy.com",
        "description": "Course platform with pricing, membership terms, and FAQ pages."
    },
    {
        "id": 4,
        "name": "Genuine JS-Only SPA (Netlify App)",
        "url": "https://app.netlify.com",
        "description": "Client-rendered React SPA where raw HTML is empty (<div id='app'></div>, 26 chars), FORCING Playwright fallback."
    },
    {
        "id": 5,
        "name": "Genuine Anti-Bot Site (Quora - Cloudflare Block)",
        "url": "https://www.quora.com",
        "description": "Site protected by Cloudflare WAF bot challenges returning HTTP 403."
    }
]

def run_crawler_tests():
    print("=" * 80)
    print("REELCLAIM PHASE 2 - VERIFIED SITE CRAWLER TEST SUITE")
    print("=" * 80)

    for test in CRAWL_TEST_CASES:
        print(f"\n--- [TEST {test['id']}] {test['name']} ---")
        print(f"Target URL: {test['url']}")
        print(f"Goal: {test['description']}")

        # 1. Raw HTTP Inspection prior to crawl
        try:
            raw_resp = requests.get(test['url'], headers=HEADERS, timeout=6, allow_redirects=True)
            print(f"RAW HTTP INSPECTION:")
            print(f"  - Status Code: {raw_resp.status_code}")
            print(f"  - Server Header: {raw_resp.headers.get('Server', 'N/A')}")
            print(f"  - CF-Ray Header: {raw_resp.headers.get('CF-RAY', 'None')}")
            print(f"  - Content-Type: {raw_resp.headers.get('Content-Type', 'N/A')}")
            print(f"  - Initial Raw Text Length: {len(raw_resp.text)}")
        except Exception as err:
            print(f"RAW HTTP INSPECTION ERROR: {err}")

        # 2. Page fetch strategy test on target homepage
        clean_text, strategy_used, fetch_status = fetch_page_content(test["url"])
        print(f"FETCH STRATEGY EXECUTED: {strategy_used} (Result Status: {fetch_status})")
        if text_len := len(clean_text or ""):
            print(f"  - Extracted Text Characters: {text_len}")

        # 3. Full Site Crawl Execution
        start_time = time.time()
        crawl_res = crawl_site(test["url"])
        elapsed = round(time.time() - start_time, 2)

        res_json = crawl_res.model_dump()
        print(f"CRAWL ELAPSED TIME: {elapsed}s")
        print("REAL CRAWL RESPONSE JSON:")
        print(json.dumps(res_json, indent=2))
        print("-" * 80)

if __name__ == "__main__":
    run_crawler_tests()
