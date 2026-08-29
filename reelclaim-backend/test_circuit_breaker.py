"""
ReelClaim — Playwright Circuit Breaker Test
=============================================
Demonstrates the memory circuit breaker triggering when memory usage
exceeds the configured threshold.

Usage:
    python test_circuit_breaker.py
"""
import sys, os, time, logging, psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Force the circuit breaker to trip by setting an impossibly low threshold (5MB)
os.environ["PW_MEMORY_LIMIT_MB"] = "5"

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

from app.crawler import fetch_page_with_playwright, PW_MEMORY_LIMIT_MB

SPA_URL = "https://todomvc.com/examples/react/dist/"

print("=" * 80)
print("PLAYWRIGHT CIRCUIT BREAKER TEST")
print(f"  Target SPA URL     : {SPA_URL}")
print(f"  Configured limit   : {PW_MEMORY_LIMIT_MB} MB")
print("=" * 80)

# Artificially consume some memory just in case 5MB isn't low enough, though 5MB is almost certainly lower than a running python process
dummy_memory = bytearray(10 * 1024 * 1024) # 10MB chunk

text, status = fetch_page_with_playwright(SPA_URL)

print("=" * 80)
print("RESULT")
print(f"  Status returned : {status}")
print("=" * 80)
