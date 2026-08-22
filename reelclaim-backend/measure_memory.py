import os
import psutil
import time
from app.crawler import crawl_site

def get_process_memory_mb():
    current_process = psutil.Process(os.getpid())
    mem = current_process.memory_info().rss
    # Include child processes (Playwright Chromium)
    for child in current_process.children(recursive=True):
        try:
            mem += child.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return mem / (1024 * 1024)

print("=== MEASURING RAM USAGE DURING LIVE CRAWL ===")
initial_mem = get_process_memory_mb()
print(f"Baseline Process Memory: {initial_mem:.2f} MB")

start_time = time.time()

# Run a real crawl against boot.dev
crawl_res = crawl_site("https://boot.dev/pricing")

peak_mem = get_process_memory_mb()
duration = time.time() - start_time

print(f"Crawl Status: {crawl_res.crawl_status}")
print(f"Pages Crawled: {crawl_res.pages_found}")
print(f"Facts Extracted: {len(crawl_res.facts)}")
print(f"Peak Memory Usage (Python + Chromium Children): {peak_mem:.2f} MB")
print(f"Memory Delta: {peak_mem - initial_mem:.2f} MB")
print(f"Execution Time: {duration:.2f} seconds")
