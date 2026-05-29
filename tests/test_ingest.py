import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db import Base, Lead, Suppression
from src.utils.url import normalize_url, extract_domain
from src.core.ingest import ingest_csv, is_valid_email

# In-memory database setup for testing
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

def test_is_valid_email():
    assert is_valid_email("test@example.com") is True
    assert is_valid_email("test.name+alex@sub.domain.co.uk") is True
    assert is_valid_email("invalid-email") is False
    assert is_valid_email("@no-username.com") is False
    assert is_valid_email("username@.com") is False
    assert is_valid_email("") is False

def test_url_normalization():
    assert normalize_url("example.com") == "https://example.com/"
    assert normalize_url("http://WWW.EXAMPLE.COM/index.html?ref=123#about") == "http://www.example.com/index.html"
    assert normalize_url("https://sub.domain.com/path/to/page/") == "https://sub.domain.com/path/to/page/"
    assert normalize_url("") is None
    assert normalize_url("   ") is None

def test_extract_domain():
    assert extract_domain("https://www.example.com/about") == "example.com"
    assert extract_domain("http://example.com") == "example.com"
    assert extract_domain("sub.domain.com/path") == "sub.domain.com"
    assert extract_domain("") is None

def test_ingest_csv_success(db_session):
    csv_content = (
        "name,website,email\n"
        "Alice,example.com,alice@example.com\n"
        "Bob,http://bobsite.com/home,bob@bobsite.com\n"
    )
    
    stats = ingest_csv(db_session, csv_content)
    
    assert stats["total"] == 2
    assert stats["imported"] == 2
    assert stats["failed"] == 0
    assert stats["duplicates"] == 0
    assert stats["suppressed"] == 0
    
    leads = db_session.query(Lead).all()
    assert len(leads) == 2
    assert leads[0].name == "Alice"
    assert leads[0].website_url == "https://example.com/"
    assert leads[0].domain == "example.com"
    assert leads[0].email == "alice@example.com"
    assert leads[0].status == "pending"

def test_ingest_csv_validation_failure(db_session):
    csv_content = (
        "name,website,email\n"
        "Alice,example.com,invalid-email\n"
        "Bob,,bob@bobsite.com\n"
    )
    
    stats = ingest_csv(db_session, csv_content)
    
    assert stats["total"] == 2
    assert stats["imported"] == 0
    assert stats["failed"] == 2
    
    leads = db_session.query(Lead).all()
    assert len(leads) == 2
    assert leads[0].status == "failed"
    assert "Invalid email" in leads[0].error_message
    assert leads[1].status == "failed"
    assert "Invalid or missing website URL" in leads[1].error_message

def test_ingest_csv_deduplication(db_session):
    # Ingest initial records
    csv_content_1 = (
        "name,website,email\n"
        "Alice,example.com,alice@example.com\n"
    )
    ingest_csv(db_session, csv_content_1)
    
    # Ingest duplicate email and duplicate domain
    csv_content_2 = (
        "name,website,email\n"
        "Alice Duplicate Email,othersite.com,alice@example.com\n"
        "Alice Duplicate Domain,example.com,other@example.com\n"
        "Unique Lead,unique.com,unique@unique.com\n"
    )
    
    stats = ingest_csv(db_session, csv_content_2)
    
    assert stats["total"] == 3
    assert stats["imported"] == 1
    assert stats["duplicates"] == 2
    
    leads = db_session.query(Lead).all()
    # 1 from first import + 1 from second import
    assert len(leads) == 2
    assert leads[1].name == "Unique Lead"

def test_ingest_csv_suppression(db_session):
    # Setup suppression list
    suppressed_email = "optout@example.com"
    db_session.add(Suppression(email=suppressed_email, reason="unsubscribe"))
    db_session.commit()
    
    csv_content = (
        "name,website,email\n"
        "Suppressed Lead,example.com,optout@example.com\n"
        "Normal Lead,other.com,normal@other.com\n"
    )
    
    stats = ingest_csv(db_session, csv_content)
    
    assert stats["total"] == 2
    assert stats["imported"] == 1
    assert stats["suppressed"] == 1
    
    suppressed_lead = db_session.query(Lead).filter_by(email=suppressed_email).first()
    assert suppressed_lead is not None
    assert suppressed_lead.status == "suppressed"
    assert suppressed_lead.error_message == "Email found on suppression list"
