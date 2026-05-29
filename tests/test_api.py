import os
import shutil
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.db import Base, get_db, Lead, Scrape, Analysis, Email, Event, Job, Suppression
from src.config import settings

# Test client
client = TestClient(app)

TEST_DB_PATH = "test_api.db"
# Use a file-based database for SQLite to avoid connection-loss schema drops on memory DBs
engine = create_engine(f"sqlite:///{TEST_DB_PATH}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database session dependency override
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def backup_config():
    """
    Safely backs up config.yaml before running API tests and restores it afterwards.
    """
    config_path = "config.yaml"
    backup_path = "config.yaml.bak"
    has_config = os.path.exists(config_path)
    
    if has_config:
        shutil.copy(config_path, backup_path)
    
    yield
    
    if has_config:
        shutil.move(backup_path, config_path)
    elif os.path.exists(config_path):
        os.remove(config_path)

@pytest.fixture(autouse=True)
def setup_db_and_auth():
    # Setup test tables
    Base.metadata.create_all(bind=engine)
    
    # Store settings originals
    orig_auth_req = settings.api.auth_token_required
    orig_token = settings.api_auth_token
    
    # Enable API Token authentication for tests
    settings.api.auth_token_required = True
    settings.api_auth_token = "test-secret-token"
    
    yield
    
    # Restore original settings
    settings.api.auth_token_required = orig_auth_req
    settings.api_auth_token = orig_token
    
    # Dispose of engine to release connection locks before file deletion
    engine.dispose()
    
    # Delete temporary test database file
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

def test_api_authentication():
    # 1. No token -> 401 Unauthorized
    response = client.get("/api/leads")
    assert response.status_code == 401
    assert "Invalid API Token" in response.json()["detail"]

    # 2. Wrong token -> 401 Unauthorized
    response = client.get("/api/leads", headers={"X-API-Token": "wrong-token"})
    assert response.status_code == 401

    # 3. Valid token header -> 200 OK
    response = client.get("/api/leads", headers={"X-API-Token": "test-secret-token"})
    assert response.status_code == 200
    assert response.json() == []

    # 4. Valid token query param -> 200 OK
    response = client.get("/api/leads?token=test-secret-token")
    assert response.status_code == 200

def test_list_and_get_leads():
    # Seed db
    db = TestingSessionLocal()
    lead1 = Lead(name="Company A", website_url="https://companya.com", email="a@companya.com", status="pending")
    lead2 = Lead(name="Company B", website_url="https://companyb.com", email="b@companyb.com", status="scraped")
    db.add_all([lead1, lead2])
    db.commit()
    
    # Refresh to retrieve generated IDs before closing
    db.refresh(lead1)
    db.refresh(lead2)
    lead1_id = lead1.id
    lead2_id = lead2.id
    db.close()

    # List leads
    headers = {"X-API-Token": "test-secret-token"}
    response = client.get("/api/leads", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Company B"  # sorted descending by ID
    assert data[1]["name"] == "Company A"

    # List leads with status filter
    response = client.get("/api/leads?status=scraped", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Company B"

    # Get specific lead details
    response = client.get(f"/api/leads/{lead1_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Company A"
    assert data["email"] == "a@companya.com"
    assert data["scrape"] is None

    # Get missing lead -> 404
    response = client.get("/api/leads/9999", headers=headers)
    assert response.status_code == 404

def test_get_screenshot(tmp_path):
    headers = {"X-API-Token": "test-secret-token"}
    
    db = TestingSessionLocal()
    # 1. No scrape / no screenshot -> 404
    lead_no_scr = Lead(name="No Screen", website_url="https://noscreen.com", email="no@screen.com", status="scraped")
    db.add(lead_no_scr)
    db.commit()
    db.refresh(lead_no_scr)
    lead_no_scr_id = lead_no_scr.id
    
    response = client.get(f"/api/screenshots/{lead_no_scr_id}", headers=headers)
    assert response.status_code == 404

    # 2. Scrape has path, but file missing -> 404
    lead_missing_scr = Lead(name="Missing Screen", website_url="https://missingscreen.com", email="missing@screen.com", status="scraped")
    db.add(lead_missing_scr)
    db.commit()
    db.refresh(lead_missing_scr)
    lead_missing_scr_id = lead_missing_scr.id
    
    scrape_missing = Scrape(lead_id=lead_missing_scr_id, screenshot_path="nonexistent_file.png", reachable=True)
    db.add(scrape_missing)
    db.commit()
    
    response = client.get(f"/api/screenshots/{lead_missing_scr_id}", headers=headers)
    assert response.status_code == 404

    # 3. Screenshot exists -> 200 with FileResponse
    dummy_scr = tmp_path / "screenshot_1.png"
    dummy_scr.write_bytes(b"dummy image data")
    
    lead_has_scr = Lead(name="Has Screen", website_url="https://hasscreen.com", email="has@screen.com", status="scraped")
    db.add(lead_has_scr)
    db.commit()
    db.refresh(lead_has_scr)
    lead_has_scr_id = lead_has_scr.id
    
    scrape_has = Scrape(lead_id=lead_has_scr_id, screenshot_path=str(dummy_scr), reachable=True)
    db.add(scrape_has)
    db.commit()
    db.close()
    
    response = client.get(f"/api/screenshots/{lead_has_scr_id}", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"dummy image data"

def test_get_stats():
    headers = {"X-API-Token": "test-secret-token"}
    db = TestingSessionLocal()
    
    db.add_all([
        Lead(name="A", status="pending"),
        Lead(name="B", status="pending"),
        Lead(name="C", status="scraped"),
        Lead(name="D", status="sent"),
        Lead(name="E", status="suppressed")
    ])
    db.commit()
    db.close()

    response = client.get("/api/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["pending"] == 2
    assert data["scraped"] == 1
    assert data["sent"] == 1
    assert data["suppressed"] == 1
    assert data["analyzed"] == 0
    assert data["failed"] == 0

def test_config_read_write():
    headers = {"X-API-Token": "test-secret-token"}

    # Read config
    response = client.get("/api/config", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "scrape" in data
    assert "send" in data
    assert "daily_send_limit" in data["send"]

    # Write config
    payload = {
        "send": {
            "daily_send_limit": 45,
            "provider": "gmail"
        },
        "scrape": {
            "concurrency": 10
        }
    }
    response = client.post("/api/config", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Validate settings update
    assert settings.send.daily_send_limit == 45
    assert settings.scrape.concurrency == 10

    # Validate file persistence
    with open("config.yaml", "r", encoding="utf-8") as f:
        import yaml
        config_data = yaml.safe_load(f)
    assert config_data["send"]["daily_send_limit"] == 45
    assert config_data["scrape"]["concurrency"] == 10

def test_job_creation_and_cancellation():
    headers = {"X-API-Token": "test-secret-token"}
    
    # 1. Enqueue job (completes synchronously under TestClient)
    payload = {
        "type": "scrape",
        "params": {"limit": 5}
    }
    response = client.post("/api/jobs", json=payload, headers=headers)
    assert response.status_code == 200
    job_data = response.json()
    assert job_data["type"] == "scrape"
    assert job_data["status"] in ["queued", "running", "completed"]
    job_id = job_data["id"]

    # List jobs
    response = client.get("/api/jobs", headers=headers)
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) >= 1
    assert jobs[0]["id"] == job_id

    # Get specific job
    response = client.get(f"/api/jobs/{job_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == job_id

    # 2. Test cancellation endpoint using a mocked running task
    # Seed a dummy running job in DB
    db = TestingSessionLocal()
    running_job = Job(type="scrape", status="running", done=0, total=10, params={})
    db.add(running_job)
    db.commit()
    db.refresh(running_job)
    running_job_id = running_job.id
    db.close()

    # Register a mocked task in running_tasks
    from unittest.mock import MagicMock
    from src.api.jobs import running_tasks
    mock_task = MagicMock()
    running_tasks[running_job_id] = mock_task

    # Request cancellation
    response = client.post(f"/api/jobs/{running_job_id}/cancel", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_task.cancel.assert_called_once()

def test_job_sse_streaming():
    headers = {"X-API-Token": "test-secret-token"}
    
    # Create a completed job in DB to make the event stream finite
    db = TestingSessionLocal()
    job = Job(type="scrape", status="completed", done=5, total=5, params={})
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = job.id
    db.close()

    # Request event source
    response = client.get(f"/api/events/jobs/{job_id}?token=test-secret-token")
    assert response.status_code == 200
    
    # Check that the response contains the first SSE line
    lines = response.text.split("\n")
    assert any(line.startswith("event:") or line.startswith("data:") for line in lines)

def test_create_leads():
    headers = {"X-API-Token": "test-secret-token"}
    payload = [
        {"name": "Alice Biz", "website_url": "alice.com", "email": "alice@alice.com"},
        {"name": "Invalid Email Biz", "website_url": "invalid.com", "email": "bademail"},
    ]
    response = client.post("/api/leads", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Alice Biz"
    assert data[0]["status"] == "pending"
    assert data[0]["domain"] == "alice.com"
    assert data[1]["name"] == "Invalid Email Biz"
    assert data[1]["status"] == "failed"

def test_review_queue_endpoints():
    headers = {"X-API-Token": "test-secret-token"}
    db = TestingSessionLocal()
    
    # 1. Create a lead and a draft email
    lead = Lead(name="Review Biz", website_url="https://reviewbiz.com", email="review@reviewbiz.com", status="drafted")
    db.add(lead)
    db.commit()
    db.refresh(lead)
    lead_id = lead.id
    
    email_draft = Email(lead_id=lead_id, subject="Original Subject", body="Original Body", status="draft")
    db.add(email_draft)
    db.commit()
    db.close()
    
    # Test Approve
    response = client.post(f"/api/leads/{lead_id}/approve", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    db = TestingSessionLocal()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    email_draft = db.query(Email).filter(Email.lead_id == lead_id).first()
    assert lead.status == "approved"
    assert email_draft.status == "approved"
    assert email_draft.approved_at is not None
    
    # Reset to draft for reject test
    lead.status = "drafted"
    email_draft.status = "draft"
    db.commit()
    db.close()
    
    # Test Reject
    payload = {"reject_reason": "Out of business"}
    response = client.post(f"/api/leads/{lead_id}/reject", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    db = TestingSessionLocal()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    email_draft = db.query(Email).filter(Email.lead_id == lead_id).first()
    assert lead.status == "rejected"
    assert email_draft.status == "rejected"
    assert email_draft.reject_reason == "Out of business"
    
    # Reset to draft for edit test
    lead.status = "drafted"
    email_draft.status = "draft"
    db.commit()
    db.close()
    
    # Test Edit
    edit_payload = {"subject": "New Subject", "body": "New Body without footer"}
    response = client.post(f"/api/leads/{lead_id}/edit", json=edit_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    db = TestingSessionLocal()
    email_draft = db.query(Email).filter(Email.lead_id == lead_id).first()
    assert email_draft.subject == "New Subject"
    assert "New Body without footer" in email_draft.body
    # Verify compliance footer got appended
    assert "To unsubscribe from future audits" in email_draft.body
    db.close()

def test_suppression_list_endpoints():
    headers = {"X-API-Token": "test-secret-token"}
    db = TestingSessionLocal()
    
    # Seed a lead to verify suppression cascade
    lead = Lead(name="Supp Biz", website_url="https://suppbiz.com", email="supp@suppbiz.com", status="pending")
    db.add(lead)
    db.commit()
    db.refresh(lead)
    lead_id = lead.id
    db.close()
    
    # Add to suppression
    supp_payload = {"email": "supp@suppbiz.com", "reason": "manual"}
    response = client.post("/api/suppression", json=supp_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "supp@suppbiz.com"
    
    # Check lead status updated
    db = TestingSessionLocal()
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    assert lead.status == "suppressed"
    
    # List suppressions
    response = client.get("/api/suppression", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["email"] == "supp@suppbiz.com"
    db.close()
    
    # Delete suppression
    response = client.delete("/api/suppression/supp@suppbiz.com", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify suppression row deleted
    db = TestingSessionLocal()
    supp = db.query(Suppression).filter(Suppression.email == "supp@suppbiz.com").first()
    assert supp is None
    db.close()

def test_bakeoff_api_endpoint():
    headers = {"X-API-Token": "test-secret-token"}
    db = TestingSessionLocal()
    
    # Seed an analyzed lead so it is eligible for bake-off
    lead = Lead(name="Bake Biz", website_url="https://bakebiz.com", email="bake@bakebiz.com", status="analyzed")
    db.add(lead)
    db.commit()
    db.refresh(lead)
    
    # Add mapped findings
    analysis = Analysis(
        lead_id=lead.id,
        perf_score=90,
        seo_score=85,
        accessibility_score=80,
        best_practices_score=95,
        has_ssl=True,
        broken_links_count=0,
        service_map={
            "Design": {"service": "Design", "evidence": "PSI score is 90"}
        }
    )
    db.add(analysis)
    db.commit()
    db.close()
    
    # Request bake-off
    payload = {
        "sample_size": 1,
        "models": ["claude-sonnet-4-6:anthropic"]
    }
    response = client.post("/api/bakeoff", json=payload, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 1
    assert data[0]["runs"][0]["model"] == "claude-sonnet-4-6"
    assert "Custom Subject Line" in data[0]["runs"][0]["subject"]



