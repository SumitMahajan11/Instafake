import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.main import audit_reel_endpoint
from app.models import FullAuditRequest

print("Executing live end-to-end audit against a real product website (https://boot.dev)...")

request = FullAuditRequest(
    caption="🔥 Become a backend developer on boot.dev with monthly membership, 30-day money-back guarantee, and completion certificates!",
    override_url="https://boot.dev"
)

try:
    result = audit_reel_endpoint(request)
    print("\n--- FINAL LIVE /audit-reel RESULT ---")
    print(json.dumps(result.model_dump(), indent=2))
except Exception as e:
    print(f"Error during live audit test: {e}")
