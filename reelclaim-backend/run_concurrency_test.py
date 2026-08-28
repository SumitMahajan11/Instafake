import sys
import time
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# Ensure UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

CONCURRENT_TEST_REQUESTS = [
    {
        "id": 1,
        "label": "Request 1 (TodoMVC SPA - Playwright Contender 1)",
        "payload": {
            "caption": "Check out todo MVC react app at https://todomvc.com/examples/react/dist/",
            "override_url": "https://todomvc.com/examples/react/dist/"
        }
    },
    {
        "id": 2,
        "label": "Request 2 (TodoMVC SPA - Playwright Contender 2)",
        "payload": {
            "caption": "Check out todo MVC react app at https://todomvc.com/examples/react/dist/",
            "override_url": "https://todomvc.com/examples/react/dist/"
        }
    },
    {
        "id": 3,
        "label": "Request 3 (TodoMVC SPA - Playwright Contender 3)",
        "payload": {
            "caption": "Check out todo MVC react app at https://todomvc.com/examples/react/dist/",
            "override_url": "https://todomvc.com/examples/react/dist/"
        }
    }
]

def send_audit_request(backend_url: str, req_info: dict):
    req_id = req_info["id"]
    label = req_info["label"]
    payload = req_info["payload"]

    endpoint = f"{backend_url.rstrip('/')}/audit-reel"
    start_time = time.time()
    print(f"🚀 [T0 + 0.0s] Fired {label}...")

    try:
        response = requests.post(endpoint, json=payload, timeout=90)
        elapsed = round(time.time() - start_time, 2)
        if response.status_code == 200:
            data = response.json()
            crawl_status = data.get("crawl_status")
            claims_count = len(data.get("claims", []))
            has_check = data.get("check_result") is not None
            return {
                "id": req_id,
                "label": label,
                "elapsed": elapsed,
                "http_status": 200,
                "crawl_status": crawl_status,
                "claims_count": claims_count,
                "has_check": has_check,
                "error": None
            }
        else:
            return {
                "id": req_id,
                "label": label,
                "elapsed": elapsed,
                "http_status": response.status_code,
                "crawl_status": None,
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except Exception as e:
        elapsed = round(time.time() - start_time, 2)
        return {
            "id": req_id,
            "label": label,
            "elapsed": elapsed,
            "http_status": None,
            "crawl_status": None,
            "error": str(e)
        }

def run_concurrency_test():
    parser = argparse.ArgumentParser(description="ReelClaim Concurrency Test Suite")
    parser.add_argument("--url", type=str, default="https://reelclaim-api.onrender.com", help="Target backend base URL")
    args = parser.parse_args()

    backend_url = args.url
    print("=" * 80)
    print("REELCLAIM — CONCURRENCY & LOCK QUEUING TEST SUITE")
    print(f"Targeting: {backend_url}")
    print(f"Firing {len(CONCURRENT_TEST_REQUESTS)} SIMULTANEOUS Audit Requests...")
    print("=" * 80)

    start_wall = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(send_audit_request, backend_url, req)
            for req in CONCURRENT_TEST_REQUESTS
        ]
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            print(f"✅ Completed {res['label']} in {res['elapsed']}s | HTTP {res['http_status']} | Crawl: {res['crawl_status']}")

    total_wall_time = round(time.time() - start_wall, 2)
    results.sort(key=lambda x: x["id"])

    print("\n" + "=" * 80)
    print("CONCURRENCY TEST SUMMARY REPORT")
    print(f"Total Wall Clock Duration: {total_wall_time}s")
    print("=" * 80)

    for r in results:
        err_str = f" | Error: {r['error']}" if r['error'] else ""
        print(f"Req #{r['id']}: {r['label']:<42} | Time: {r['elapsed']:>6.2f}s | HTTP: {r['http_status']} | Crawl Status: {r['crawl_status']}{err_str}")

    print("=" * 80)

if __name__ == "__main__":
    run_concurrency_test()
