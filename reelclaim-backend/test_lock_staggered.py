"""
ReelClaim — Staggered Lock Concurrency Test (Rescue scenario)
==============================================================
Demonstrates that the 3s bounded wait ACTUALLY rescues requests:
  - Worker A fires at T+0  (gets lock immediately, holds ~5-10s)
  - Worker B fires at T+8  (after A likely finished → B waits <1s and succeeds)
  - Worker C fires at T+0  (contends with A → waits 3s, gets busy)

Before this change, ALL of B & C would have instantly gotten "busy".
Now Worker B waits briefly and successfully acquires the lock.
"""
import sys, os, time, logging, threading

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)

from app.crawler import fetch_page_with_playwright, LOCK_WAIT_TIMEOUT, LOCK_HOLD_TIMEOUT

SPA_URL = "https://todomvc.com/examples/react/dist/"
GLOBAL_T0 = None


def _worker(worker_id: int, delay: float):
    global GLOBAL_T0
    if delay > 0:
        print(f"  Worker #{worker_id} waiting {delay}s before firing...")
        time.sleep(delay)
    t0 = time.monotonic()
    print(f"  🚀 Worker #{worker_id} FIRING at T+{time.monotonic() - GLOBAL_T0:.1f}s")
    text, status = fetch_page_with_playwright(SPA_URL)
    elapsed = time.monotonic() - t0
    chars = len(text) if text else 0
    emoji = '✅' if status in ('success','degraded') else '⏳' if status == 'busy' else '❌'
    print(f"  {emoji} Worker #{worker_id} DONE  status={status:<10} chars={chars:>5}  elapsed={elapsed:.3f}s  "
          f"(wall T+{time.monotonic() - GLOBAL_T0:.1f}s)")
    return {"worker": worker_id, "status": status, "chars": chars, "elapsed": elapsed}


print("=" * 80)
print("STAGGERED LOCK TEST — 3 workers with staggered delays")
print(f"  Lock wait timeout: {LOCK_WAIT_TIMEOUT}s")
print(f"  Lock hold timeout: {LOCK_HOLD_TIMEOUT}s")
print(f"  Worker A: fires at T+0   (gets lock)")
print(f"  Worker B: fires at T+0   (contends, waits 3s)")
print(f"  Worker C: fires at T+12  (A finished, gets lock quickly)")
print("=" * 80)

GLOBAL_T0 = time.monotonic()

# Worker A at T=0, Worker B at T=0 (contends), Worker C at T=12 (A finished by then)
workers = [(1, 0), (2, 0), (3, 12)]
threads = []
for wid, delay in workers:
    t = threading.Thread(target=_worker, args=(wid, delay))
    t.start()
    threads.append(t)

for t in threads:
    t.join()

total = time.monotonic() - GLOBAL_T0
print(f"\n  Total wall time: {total:.3f}s")
print("=" * 80)
