import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add project root directory to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.models import is_plausible_gemini_key

client = TestClient(app)

def test_is_plausible_gemini_key():
    valid_key = "AIzaSy" + "A" * 33
    assert is_plausible_gemini_key(valid_key) is True
    assert is_plausible_gemini_key("invalid_key_prefix") is False
    assert is_plausible_gemini_key("AIzaShort") is False
    assert is_plausible_gemini_key("AIza" + "!" * 35) is False
    assert is_plausible_gemini_key(None) is False
    assert is_plausible_gemini_key("") is False

def test_byok_malformed_key_rejection():
    # Test extract-claims with invalid key
    resp = client.post("/extract-claims", json={
        "caption": "Test caption http://example.com",
        "gemini_api_key": "invalid-key-123"
    })
    assert resp.status_code == 400
    assert "Invalid Gemini API key format" in resp.json()["detail"]
    assert "invalid-key-123" not in resp.json()["detail"]

    # Test audit-reel with invalid key
    resp = client.post("/audit-reel", json={
        "caption": "Test caption http://example.com",
        "gemini_api_key": "AIzaTooShort"
    })
    assert resp.status_code == 400
    assert "Invalid Gemini API key format" in resp.json()["detail"]

@patch("app.main.extract_claims")
def test_byok_valid_key_passed_to_backend(mock_extract):
    mock_extract.return_value = MagicMock(promoted_site=None, claims=[])
    valid_key = "AIzaSy" + "B" * 35

    resp = client.post("/extract-claims", json={
        "caption": "Test caption",
        "gemini_api_key": valid_key
    })

    assert resp.status_code == 200
    mock_extract.assert_called_once_with("Test caption", api_key=valid_key)

@patch("app.main.extract_claims")
def test_byok_fallback_to_env_when_no_key(mock_extract):
    mock_extract.return_value = MagicMock(promoted_site=None, claims=[])

    resp = client.post("/extract-claims", json={
        "caption": "Test caption without key"
    })

    assert resp.status_code == 200
    mock_extract.assert_called_once_with("Test caption without key", api_key=None)
