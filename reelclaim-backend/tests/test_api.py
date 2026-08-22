import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root directory to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "ReelClaim Backend"

def test_extract_claims_endpoint():
    payload = {
        "caption": "🔥 FREE AI Internship with verified certificate on google.com/careers"
    }
    response = client.post("/extract-claims", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "promoted_site" in data
    assert "claims" in data
    assert data["promoted_site"] == "google.com/careers"
