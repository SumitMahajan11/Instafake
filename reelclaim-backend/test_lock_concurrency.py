"""
ReelClaim — Playwright Lock Concurrency Test
=============================================
Fires N simultaneous calls to fetch_page_with_playwright() against a
confirmed Playwright-required SPA URL and prints lock timing telemetry.

Usage:
    python test_lock_concurrency.py            # 3 concurrent requests
    python test_lock_concurrency.py --workers 5
"""
import sys, os, time, argparse, logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root so app.crawler is importable
sys.path.insert(0, os.path.dirname(__file__))

# Ensure lock-related logs go to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

from app.crawler import (
    fetch_page_with_playwright,
    LOCK_WAIT_TIMEOUT,
    LOCK_HOLD_TIMEOUT,
)

# ── Confirmed SPA URL that *requires* Playwright (JS shell, <200 chars plain text via requests) ──
SPA_URL = "https://todomvc.com/examples/react/dist/"


def _timed_call(worker_id: int, url: str):
    """Call fetch_page_with_playwright and return timing + result."""
    t0 = time.monotonic()
    text, status = fetch_page_with_playwright(url)
    elapsed = time.monotonic() - t0
    chars = len(text) if text else 0
    return {
        "worker": worker_id,
        "status": status,
        "chars": chars,
        "elapsed_s": round(elapsed, 3),
    }


def main():
    parser = argparse.ArgumentParser(description="Playwright lock concurrency test")
    parser.add_argument("--workers", type=int, default=3, help="Number of simultaneous workers")
    args = parser.parse_args()
    n = args.workers

    print("=" * 80)
    print("PLAYWRIGHT LOCK CONCURRENCY TEST")
    print(f"  Target SPA URL : {SPA_URL}")
    print(f"  Workers        : {n}")
    print(f"  Lock wait limit: {LOCK_WAIT_TIMEOUT}s")
    print(f"  Lock hold limit: {LOCK_HOLD_TIMEOUT}s")
    print("=" * 80)

    wall_start = time.monotonic()

    results = []
    with ThreadPoolExecutor(max_workers=n) as pool:
        futures = {
            pool.submit(_timed_call, i + 1, SPA_URL): i + 1
            for i in range(n)
        }
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            tag = "✅" if r["status"] in ("success", "degraded") else "⏳" if r["status"] == "busy" else "❌"
            print(f"  {tag} Worker #{r['worker']}  status={r['status']:<10}  chars={r['chars']:>5}  elapsed={r['elapsed_s']:.3f}s")

    wall = round(time.monotonic() - wall_start, 3)
    results.sort(key=lambda r: r["worker"])

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    success_count  = sum(1 for r in results if r["status"] in ("success", "degraded"))
    busy_count     = sum(1 for r in results if r["status"] == "busy")
    failed_count   = sum(1 for r in results if r["status"] == "failed")
    print(f"  Wall clock      : {wall}s")
    print(f"  Success/degraded: {success_count}/{n}")
    print(f"  Busy (queued-out): {busy_count}/{n}")
    print(f"  Failed          : {failed_count}/{n}")
    print()
    for r in results:
        print(f"  Worker #{r['worker']}  status={r['status']:<10}  chars={r['chars']:>5}  time={r['elapsed_s']:.3f}s")
    print("=" * 80)


if __name__ == "__main__":
    main()
