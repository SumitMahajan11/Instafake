import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.db import (
    init_db,
    save_audit_record,
    get_audit_record_by_id,
    list_recent_audit_records,
    AuditRecord,
    Base
)
from app.models import Claim, ClaimVerdict, CheckResponse, ScoreBreakdown
from app.main import app

def test_db_init_unset_url_degrades_gracefully(monkeypatch, caplog):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with caplog.at_level("WARNING"):
        res = init_db()
    assert res is False
    assert "DATABASE_URL environment variable is unset. Audit persistence is disabled." in caplog.text

def test_db_persistence_and_crud(tmp_path):
    db_file = tmp_path / "test_audit.db"
    db_url = f"sqlite:///{db_file}"
    
    with patch.dict(os.environ, {"DATABASE_URL": db_url}):
        assert init_db() is True

        claims = [
            Claim(text="Plan is $10/mo", category="price", source_type="caption", confidence="high")
        ]
        check_result = CheckResponse(
            trust_score=100.0,
            coverage_status="verified",
            summary_label="Claim is confirmed by site pricing page.",
            score_breakdown=ScoreBreakdown(
                confirmed_count=1, partial_count=0, contradicted_count=0, not_found_count=0, addressed_claims=1, total_claims=1
            ),
            verdicts=[
                ClaimVerdict(
                    claim_text="Plan is $10/mo",
                    category="price",
                    source_type="caption",
                    verdict="confirmed",
                    evidence_text="Hobby plan costs $10 per month",
                    source_url="https://example.com/pricing",
                    reasoning="Price matches."
                )
            ]
        )

        audit_id = save_audit_record(
            caption="Check our $10/mo plan on example.com/pricing",
            promoted_site="example.com/pricing",
            override_url=None,
            claims=claims,
            crawl_status="success",
            check_result=check_result
        )

        assert audit_id is not None

        # Fetch record by ID
        record = get_audit_record_by_id(audit_id)
        assert record is not None
        assert record["id"] == audit_id
        assert record["caption"] == "Check our $10/mo plan on example.com/pricing"
        assert record["trust_score"] == 100.0
        assert len(record["claims"]) == 1
        assert len(record["verdicts"]) == 1
        assert record["verdicts"][0]["verdict"] == "confirmed"

        # List recent audits
        audit_list = list_recent_audit_records(limit=10, offset=0)
        assert audit_list["total"] == 1
        assert len(audit_list["audits"]) == 1
        assert audit_list["audits"][0]["id"] == audit_id

def test_api_audit_persistence_endpoints(tmp_path):
    db_file = tmp_path / "test_api.db"
    db_url = f"sqlite:///{db_file}"

    with patch.dict(os.environ, {"DATABASE_URL": db_url}):
        init_db()
        client = TestClient(app)

        # Mock phase 1, 2, 3 calls inside audit-reel endpoint
        with patch("app.main.extract_claims") as mock_extract, \
             patch("app.main.crawl_site") as mock_crawl, \
             patch("app.main.cross_check_claims") as mock_check:
            
            mock_extract.return_value.promoted_site = "https://example.com"
            mock_extract.return_value.claims = [Claim(text="Free trial", category="discount", source_type="caption", confidence="high")]

            
            mock_crawl.return_value.crawl_status = "success"
            mock_crawl.return_value.facts = []
            
            mock_check.return_value = CheckResponse(
                trust_score=80.0,
                coverage_status="partially_verified",
                summary_label="Trial exists",
                score_breakdown=ScoreBreakdown(confirmed_count=1, total_claims=1, addressed_claims=1),
                verdicts=[]
            )

            response = client.post("/audit-reel", json={"caption": "Get a free trial at example.com"})
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["id"] is not None
            audit_id = data["id"]

            # GET audit by ID
            get_res = client.get(f"/audits/{audit_id}")
            assert get_res.status_code == 200
            audit_data = get_res.json()
            assert audit_data["id"] == audit_id
            assert audit_data["caption"] == "Get a free trial at example.com"
            assert audit_data["trust_score"] == 80.0

            # GET audits list
            list_res = client.get("/audits?limit=10&offset=0")
            assert list_res.status_code == 200
            list_data = list_res.json()
            assert list_data["total"] >= 1
            assert any(a["id"] == audit_id for a in list_data["audits"])

            # GET non-existent audit ID returns 404
            missing_res = client.get("/audits/non_existent_id_12345")
            assert missing_res.status_code == 404
