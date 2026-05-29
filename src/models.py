from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl, Field

class ScrapeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    lead_id: int
    rendered_text: Optional[str] = None
    screenshot_path: Optional[str] = None
    pages_scraped: Optional[Dict[str, Any]] = None
    http_status: Optional[int] = None
    reachable: bool
    scraped_at: datetime
    error: Optional[str] = None

class Signal(BaseModel):
    key: str
    value: Any
    severity: str  # high | medium | low | info
    threshold: Optional[Any] = None

class ServiceMapEntry(BaseModel):
    service: str
    evidence: str

class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    lead_id: int
    perf_score: Optional[int] = None
    seo_score: Optional[int] = None
    accessibility_score: Optional[int] = None
    best_practices_score: Optional[int] = None
    mobile_friendly: Optional[bool] = None
    has_ssl: bool
    load_time_ms: Optional[int] = None
    meta_title_present: bool
    meta_description_present: bool
    broken_links_count: int
    signals: Optional[List[Signal]] = None
    service_map: Optional[Dict[str, ServiceMapEntry]] = None
    analyzed_at: datetime

class EmailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    lead_id: int
    model_used: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    findings_cited: Optional[List[str]] = None
    status: str
    reject_reason: Optional[str] = None
    generated_at: datetime
    approved_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    gmail_message_id: Optional[str] = None

class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    lead_id: Optional[int] = None
    email_id: Optional[int] = None
    event_type: str
    occurred_at: datetime
    metadata_json: Optional[Dict[str, Any]] = None

class LeadBase(BaseModel):
    name: Optional[str] = None
    website_url: Optional[str] = None
    email: Optional[str] = None
    country: str = "US"

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    website_url: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None

class LeadOut(LeadBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    domain: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class LeadDetailOut(LeadOut):
    model_config = ConfigDict(from_attributes=True)
    
    scrape: Optional[ScrapeOut] = None
    analysis: Optional[AnalysisOut] = None
    emails: List[EmailOut] = []
    events: List[EventOut] = []

class SuppressionCreate(BaseModel):
    email: EmailStr
    reason: str = "manual"  # unsubscribe | bounce | manual

class SuppressionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    email: str
    reason: str
    added_at: datetime

class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    type: str
    status: str
    done: int
    total: int
    params: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

class EmailDraft(BaseModel):
    subject: str
    body: str
