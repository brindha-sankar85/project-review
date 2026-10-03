import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.database_init import init_db
from backend.app.models.schema import User, Document, SharingRequest, AuditLog
from backend.app.services.sharing_service import SharingService
from backend.app.events.processor import EventStreamProcessor

@pytest.fixture(scope="module")
def client():
    init_db(seed_data=True, force_reset=True)
    with TestClient(app) as c:
        yield c

def test_01_authentication_and_user_roles(client):
    response = client.get("/api/auth/users")
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 10
    roles = set(u["role"] for u in users)
    assert {"Admin", "Hospital Manager", "Doctor", "Nurse", "Receptionist", "Intern"}.issubset(roles)

def test_02_role_access_to_documents(client):
    # Nurse requesting documents
    resp_nurse = client.get("/api/documents/?user_id=USR-NRS-01")
    assert resp_nurse.status_code == 200
    docs = resp_nurse.json()
    
    # Check that confidential audit document is marked non-accessible for nurse
    audit_doc = next(d for d in docs if d["document_id"] == "DOC-AUD-008")
    assert audit_doc["is_accessible"] == False

    # Doctor requesting document
    resp_doc = client.get("/api/documents/?user_id=USR-DOC-01")
    assert resp_doc.status_code == 200

def test_03_backend_enforced_sensitive_redaction(client):
    # Nurse requests details of DOC-MED-002 which contains sensitive vault codes
    res = client.get("/api/documents/DOC-MED-002?user_id=USR-NRS-01")
    assert res.status_code == 200
    data = res.json()
    sections = data["sections"]
    
    sensitive_sec = next(s for s in sections if s["section_title"] == "2. High-Alert Medication Security Codes")
    assert sensitive_sec.get("is_redacted") == True
    assert "[REDACTED" in sensitive_sec["content"]
    assert "8842" not in sensitive_sec["content"]  # Pin code MUST NOT leak!

def test_04_summary_generation_and_rule_explanation(client):
    # Nurse requests summary for ICU protocol DOC-ICU-006 (Nurse is allowed, but sections may be redacted)
    res = client.post("/api/documents/DOC-ICU-006/summarize?user_id=USR-NRS-01")
    assert res.status_code == 200
    summary_data = res.json()
    assert summary_data["success"] == True
    assert "why_explanation" in summary_data
    assert "rule" in summary_data["why_explanation"]
    assert "evidence" in summary_data["why_explanation"]
    assert "RESTRICTED_TEST_002" not in summary_data["summary"]

def test_05_sharing_request_creation_and_human_confirmation(client):
    # Nurse shares Confidential doc with Intern (High risk -> Requires Human confirmation)
    payload = {
        "requester_id": "USR-NRS-01",
        "recipient_id": "USR-INT-01",
        "document_id": "DOC-HND-005",
        "reason": "Test internship orientation"
    }
    res = client.post("/api/sharing/request", json=payload)
    assert res.status_code == 200
    req_data = res.json()
    assert req_data["status"] == "PENDING"
    req_id = req_data["request_id"]

    # Attempt human approval WITHOUT override reason -> MUST FAIL!
    res_fail = client.post(f"/api/sharing/requests/{req_id}/decision", json={
        "reviewer_id": "USR-ADM-01",
        "decision": "APPROVE",
        "override_reason": ""  # Empty!
    })
    assert res_fail.status_code == 400
    assert "MANDATORY" in res_fail.json()["detail"]

    # Attempt human approval WITH valid override reason -> MUST SUCCEED!
    res_pass = client.post(f"/api/sharing/requests/{req_id}/decision", json={
        "reviewer_id": "USR-ADM-01",
        "decision": "APPROVE",
        "override_reason": "Approved under clinical supervisor direct instruction for urgent patient triage training."
    })
    assert res_pass.status_code == 200
    assert res_pass.json()["new_status"] == "OVERRIDDEN"

def test_06_audit_log_recordings(client):
    res = client.get("/api/audit/logs")
    assert res.status_code == 200
    logs = res.json()
    actions = set(l["action"] for l in logs)
    assert len(logs) > 0
    assert "OVERRIDE_RESTRICTION" in actions or "GENERATE_SUMMARY" in actions

def test_07_event_resilience_handling(client):
    import uuid
    unique_evt_id = f"EVT-TEST-UNIT-DUP-{uuid.uuid4().hex[:6]}"
    # Inject In-Sequence Event (v2 when last version was v1)
    payload = {
        "event_id": unique_evt_id,
        "event_type": "PERMISSION_CHANGED",
        "entity_id": "DOC-MED-002",
        "event_version": 2,
        "sequence_number": 50,
        "payload": {"confidentiality_level": "INTERNAL"}
    }
    res1 = client.post("/api/events/inject", json=payload)
    res2 = client.post("/api/events/inject", json=payload)  # Duplicate call with same event_id

    assert res1.json()["processing_status"] == "PROCESSED"
    assert res2.json()["processing_status"] == "IGNORED_DUPLICATE"

    # Inject Delayed Event (stale version 1 when version is now 2)
    payload_stale = {
        "event_id": "EVT-TEST-UNIT-STALE",
        "event_type": "PERMISSION_CHANGED",
        "entity_id": "DOC-MED-002",
        "event_version": 1,
        "sequence_number": 5,
        "payload": {"confidentiality_level": "PUBLIC"}
    }
    res_stale = client.post("/api/events/inject", json=payload_stale)
    assert res_stale.json()["processing_status"] == "DISCARDED_STALE"

def test_08_superseded_protocol_versioning(client):
    res = client.get("/api/documents/DOC-INF-000?user_id=USR-DOC-01")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUPERSEDED"
    assert "version_warning" in data
    assert data["version_warning"]["recommended_active_version"] == "2.1"
