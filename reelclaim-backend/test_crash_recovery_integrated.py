import time
import os
import psutil
import logging
from app.crawler import fetch_page_with_playwright, _BROWSER_MANAGER

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")

print("--- Request 1: Warm up the singleton browser ---")
text1, status1 = fetch_page_with_playwright("https://todomvc.com/examples/react/dist/")
print(f"Request 1 Status: {status1}, Text length: {len(text1) if text1 else 0}")
initial_pid = _BROWSER_MANAGER.browser._impl_obj._connection._transport._proc.pid
print(f"Browser PID: {initial_pid}")

print("\n--- Simulating Hard Crash: Terminating Chromium PID ---")
proc = psutil.Process(initial_pid)
proc.kill()
proc.wait()
print("Chromium process killed.")

print("\n--- Request 2: Relaunching transparently on crash detection ---")
text2, status2 = fetch_page_with_playwright("https://todomvc.com/examples/react/dist/")
print(f"Request 2 Status: {status2}, Text length: {len(text2) if text2 else 0}")
new_pid = _BROWSER_MANAGER.browser._impl_obj._connection._transport._proc.pid if _BROWSER_MANAGER.browser else None
print(f"New Browser PID: {new_pid}")

assert status1 == "success"
assert status2 == "success"
assert text2 is not None
assert new_pid != initial_pid
print("\n[OK] INTEGRATED CRASH & RELAUNCH TEST PASSED!")
