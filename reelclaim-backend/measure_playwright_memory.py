import os
import psutil
import time
from playwright.sync_api import sync_playwright

def get_process_tree_memory():
    current_process = psutil.Process(os.getpid())
    procs = [current_process] + current_process.children(recursive=True)
    
    breakdown = []
    total_rss = 0
    
    for p in procs:
        try:
            name = p.name()
            rss_mb = p.memory_info().rss / (1024 * 1024)
            total_rss += rss_mb
            breakdown.append(f"PID {p.pid:6d} | {name:25s} | {rss_mb:6.2f} MB")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    return total_rss, breakdown

print("=== MEASURING REAL PLAYWRIGHT CHROMIUM RAM FOOTPRINT ===")
baseline_rss, baseline_tree = get_process_tree_memory()
print(f"Baseline Process RAM: {baseline_rss:.2f} MB")

with sync_playwright() as p:
    print("Launching Chromium headless browser...")
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("Navigating to https://boot.dev/pricing...")
    page.goto("https://boot.dev/pricing")
    time.sleep(2)
    
    peak_rss, tree = get_process_tree_memory()
    print("\n--- PROCESS TREE BREAKDOWN AT PEAK ---")
    for line in tree:
        print(line)
        
    print(f"\nTOTAL REAL RSS (Python + Chromium Processes): {peak_rss:.2f} MB")
    print(f"DELTA RAM FOR CHROMIUM: {peak_rss - baseline_rss:.2f} MB")
    
    browser.close()
