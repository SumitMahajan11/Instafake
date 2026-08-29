import sys
import json
import time
import requests
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch, MagicMock
from app.crawler import crawl_site, fetch_page_content, extract_embedded_json_text, extract_clean_text_from_html, HEADERS

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

NEXTJS_FIXTURE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>NextJS Online Academy</title>
    <script id="__NEXT_DATA__" type="application/json">
    {
        "props": {
            "pageProps": {
                "courseName": "Full-Stack Web Engineering Bootcamp",
                "pricing": {
                    "monthlyFee": "$999 per month",
                    "pppDiscount": "Automatic PPP discount applied for eligible international students",
                    "currency": "USD"
                },
                "policy": {
                    "refundDays": 30,
                    "refundPolicy": "Full 100% money-back refund guarantee within 30 calendar days of subscription activation."
                },
                "faq": [
                    {
                        "question": "Is there a certificate of completion?",
                        "answer": "Yes, verified digital certificates are issued upon passing all module capstone projects."
                    }
                ]
            }
        },
        "page": "/pricing",
        "query": {},
        "buildId": "PROD_BUILD_99218"
    }
    </script>
</head>
<body>
    <div id="__next"></div>
</body>
</html>
"""

def test_nextjs_json_extraction_fixture():
    print("\n--- [UNIT TEST] Next.js __NEXT_DATA__ Embedded JSON Extraction ---")
    dom_text = extract_clean_text_from_html(NEXTJS_FIXTURE_HTML)
    json_text = extract_embedded_json_text(NEXTJS_FIXTURE_HTML)
    
    print(f"DOM text length: {len(dom_text)} (Content: '{dom_text}')")
    print(f"JSON text length: {len(json_text)}")
    print(f"JSON text sample: '{json_text[:120]}...'")

    assert len(dom_text) < 200, "DOM text alone should be < 200 chars for this sparse Next.js shell fixture"
    assert len(json_text) >= 200, "Extracted JSON text should be >= 200 chars"
    assert "Full 100% money-back refund guarantee" in json_text
    assert "verified digital certificates are issued" in json_text
    assert "PROD_BUILD_99218" not in json_text, "Internal buildId noise should be filtered out"

    # Mock requests.get returning the Next.js fixture
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.text = NEXTJS_FIXTURE_HTML

    with patch("requests.get", return_value=mock_resp):
        clean_text, strategy_used, status = fetch_page_content("https://nextjs-demo-site.com")
        print(f"Fetch strategy for sparse Next.js shell: {strategy_used} (Status: {status})")
        assert strategy_used == "requests", "Must resolve via 'requests' without escalating to Playwright!"
        assert status == "success"
        assert len(clean_text) >= 200
    print("✓ Next.js __NEXT_DATA__ JSON Extraction Test Passed!")

def run_crawler_tests():
    print("=" * 80)
    print("REELCLAIM PHASE 2 - VERIFIED SITE CRAWLER TEST SUITE")
    print("=" * 80)

    # 0. Run fixture test first
    test_nextjs_json_extraction_fixture()

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
        clean_text, strategy_used, fetch_status = fetch_page_content(test["url"], allow_playwright=True)
        print(f"FETCH STRATEGY EXECUTED: {strategy_used} (Result Status: {fetch_status})")
        if text_len := len(clean_text or ""):
            print(f"  - Extracted Text Characters: {text_len}")

        if test["id"] == 4:
            # Confirm app.netlify.com (genuinely no embedded JSON, true SPA shell) still correctly escalates to Playwright
            assert strategy_used == "playwright", "Netlify app shell must still escalate to Playwright!"

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

