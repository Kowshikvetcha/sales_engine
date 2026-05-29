import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    create_engine,
    ForeignKey,
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    JSON,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
    scoped_session,
)

# SQLite database file path
DATABASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
DATABASE_PATH = os.path.join(DATABASE_DIR, "leads.db")

# Ensure database directory exists
os.makedirs(DATABASE_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session for thread safety (especially in background jobs / APIs)
db_session = scoped_session(SessionLocal)


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    country: Mapped[str] = mapped_column(String(50), default="US")
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | scraped | analyzed | drafted | skipped_no_findings | approved | rejected | sent | failed | suppressed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    scrape: Mapped[Optional["Scrape"]] = relationship("Scrape", back_populates="lead", cascade="all, delete-orphan", uselist=False)
    analysis: Mapped[Optional["Analysis"]] = relationship("Analysis", back_populates="lead", cascade="all, delete-orphan", uselist=False)
    emails: Mapped[List["Email"]] = relationship("Email", back_populates="lead", cascade="all, delete-orphan")
    events: Mapped[List["Event"]] = relationship("Event", back_populates="lead", cascade="all, delete-orphan")


class Scrape(Base):
    __tablename__ = "scrapes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"), unique=True)
    rendered_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pages_scraped: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSON field supported by SQLite natively in newer versions
    http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reachable: Mapped[bool] = mapped_column(Boolean, default=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="scrape")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"), unique=True)
    perf_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    seo_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    accessibility_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    best_practices_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mobile_friendly: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_ssl: Mapped[bool] = mapped_column(Boolean, default=True)
    load_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meta_title_present: Mapped[bool] = mapped_column(Boolean, default=True)
    meta_description_present: Mapped[bool] = mapped_column(Boolean, default=True)
    broken_links_count: Mapped[int] = mapped_column(Integer, default=0)
    signals: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    service_map: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="analysis")


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(Integer, ForeignKey("leads.id"))
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    findings_cited: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft | approved | rejected | sent | failed
    reject_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    gmail_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="emails")
    events: Mapped[List["Event"]] = relationship("Event", back_populates="email", cascade="all, delete-orphan")


class Suppression(Base):
    __tablename__ = "suppression"

    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    reason: Mapped[str] = mapped_column(String(100), default="unsubscribe")  # unsubscribe | bounce | manual
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("leads.id"), nullable=True)
    email_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("emails.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50))  # sent | bounce | open | reply | unsubscribe
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSON metadata

    # Relationships
    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="events")
    email: Mapped[Optional["Email"]] = relationship("Email", back_populates="events")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(50))  # scrape | analyze | generate | send | bakeoff
    status: Mapped[str] = mapped_column(String(50), default="queued")  # queued | running | completed | failed | cancelled
    done: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()
