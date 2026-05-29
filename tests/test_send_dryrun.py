import pytest
import asyncio
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db import Base, Lead, Email, Suppression, Event
from src.config import settings
from src.core.send import send_emails, verify_compliance_config

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(autouse=True)
def configure_test_settings():
    # Store originals
    orig_address = settings.email.physical_address
    orig_unsub = settings.email.unsubscribe_base_url
    orig_cap = settings.send.daily_send_limit
    orig_dry_run = settings.send.dry_run
    orig_review = settings.send.require_human_review
    orig_delay = settings.send.per_message_delay_s

    # Assign test values
    settings.email.physical_address = "123 Valid Street, San Francisco, CA 94105"
    settings.email.unsubscribe_base_url = "https://mydomain.com/unsubscribe"
    settings.send.daily_send_limit = 5
    settings.send.dry_run = True
    settings.send.require_human_review = True
    settings.send.per_message_delay_s = 0.01  # keep tests fast

    yield settings

    # Restore originals
    settings.email.physical_address = orig_address
    settings.email.unsubscribe_base_url = orig_unsub
    settings.send.daily_send_limit = orig_cap
    settings.send.dry_run = orig_dry_run
    settings.send.require_human_review = orig_review
    settings.send.per_message_delay_s = orig_delay

def test_compliance_config_validation():
    # If using default placeholder, it should raise ValueError
    settings.email.physical_address = "123 Main St, Anytown, USA"
    with pytest.raises(ValueError) as exc:
        verify_compliance_config()
    assert "A valid physical_address must be configured" in str(exc.value)

    settings.email.physical_address = "Valid Address"
    settings.email.unsubscribe_base_url = "http://localhost:8000/unsubscribe"
    with pytest.raises(ValueError) as exc:
        verify_compliance_config()
    assert "A valid unsubscribe_base_url must be configured" in str(exc.value)

    # Valid values should not raise anything
    settings.email.physical_address = "Valid Address"
    settings.email.unsubscribe_base_url = "https://mywebsite.com/unsubscribe"
    verify_compliance_config()  # Should run without error

@pytest.mark.asyncio
async def test_send_dry_run_success(db_session):
    # Setup test data
    lead = Lead(name="Test Biz", website_url="https://testbiz.com", email="info@testbiz.com", status="approved")
    db_session.add(lead)
    db_session.commit()

    email = Email(
        lead_id=lead.id,
        subject="Personalized Audit Report",
        body="Here is your report. Acme Agency | 123 Valid Street, San Francisco, CA 94105\nTo unsubscribe: https://mydomain.com/unsubscribe?email=info@testbiz.com",
        status="approved"
    )
    db_session.add(email)
    db_session.commit()

    stats = await send_emails(db_session, dry_run=True)

    assert stats["sent"] == 1
    assert stats["failed"] == 0
    assert stats["suppressed"] == 0
    assert stats["cap_hit"] is False

    # Check updated database records
    db_session.refresh(lead)
    db_session.refresh(email)
    assert lead.status == "sent"
    assert email.status == "sent"
    assert email.sent_at is not None
    assert email.gmail_message_id.startswith("dryrun-msg-")

    # Check events
    event = db_session.query(Event).filter(Event.lead_id == lead.id).first()
    assert event is not None
    assert event.event_type == "sent"
    assert event.metadata_json["dry_run"] is True

@pytest.mark.asyncio
async def test_send_suppression_blocking(db_session):
    # Setup suppressed lead
    lead = Lead(name="Opted Out", website_url="https://optout.com", email="stop@optout.com", status="approved")
    db_session.add(lead)
    db_session.add(Suppression(email="stop@optout.com", reason="unsubscribe"))
    db_session.commit()

    email = Email(
        lead_id=lead.id,
        subject="Audit findings",
        body="Body content...",
        status="approved"
    )
    db_session.add(email)
    db_session.commit()

    stats = await send_emails(db_session, dry_run=True)

    assert stats["sent"] == 0
    assert stats["suppressed"] == 1
    assert stats["failed"] == 0

    # Ensure status changed to suppressed
    db_session.refresh(lead)
    db_session.refresh(email)
    assert lead.status == "suppressed"
    assert email.status == "failed"
    assert "Suppressed" in email.reject_reason

@pytest.mark.asyncio
async def test_daily_send_limit_cap(db_session):
    # Set limit to 2
    settings.send.daily_send_limit = 2

    # Create 3 approved leads & emails
    for i in range(3):
        lead = Lead(name=f"Biz {i}", website_url=f"https://biz{i}.com", email=f"info@biz{i}.com", status="approved")
        db_session.add(lead)
        db_session.commit()

        email = Email(
            lead_id=lead.id,
            subject=f"Audit {i}",
            body="Body...",
            status="approved"
        )
        db_session.add(email)
        db_session.commit()

    stats = await send_emails(db_session, dry_run=True)

    # Only 2 should go out since the cap is 2
    assert stats["sent"] == 2
    assert stats["cap_hit"] is True

    # Double check sent statuses in database
    sent_emails = db_session.query(Email).filter(Email.status == "sent").all()
    assert len(sent_emails) == 2

    approved_emails = db_session.query(Email).filter(Email.status == "approved").all()
    assert len(approved_emails) == 1
