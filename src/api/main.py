import os
import yaml
from typing import List, Optional, Dict, Any
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, Header, HTTPException, Query, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

import asyncio
import json
from datetime import datetime
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.db import get_db, init_db, Lead, Scrape, Analysis, Email, Event, Job, Suppression
from src.models import LeadOut, LeadDetailOut, JobOut, LeadCreate, SuppressionCreate, SuppressionOut, EmailDraft
from src.config import settings
from src.api.jobs import enqueue_job, running_tasks, job_listeners
from src.core.ingest import is_valid_email
from src.utils.url import normalize_url, extract_domain

# Initialize database schema at web server start
init_db()

# Initialize FastAPI application
app = FastAPI(
    title="Website-Audit Sales Automation API",
    description="Backend services for B2B cold outreach automation",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
def verify_api_token(
    x_api_token: Optional[str] = Header(None, alias="X-API-Token"),
    token: Optional[str] = Query(None)
):
    """
    Enforces header or query parameter API token verification.
    """
    if settings.api.auth_token_required and settings.api_auth_token:
        provided_token = x_api_token or token
        if not provided_token or provided_token != settings.api_auth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized: Invalid API Token"
            )

# Apply authentication to all API endpoints by default
# For routing flexibility, we can include it in the endpoints or globally.
# Let's apply it globally or selectively. Enforcing it globally via Depends in endpoints is clean.

def save_settings_to_yaml(config_path: str = "config.yaml"):
    """
    Helper to save updated configuration submodels back to config.yaml.
    """
    data = {
        "csv": settings.csv.model_dump(),
        "scrape": settings.scrape.model_dump(),
        "analysis": settings.analysis.model_dump(),
        "service_map": settings.service_map.model_dump(),
        "email": settings.email.model_dump(),
        "send": settings.send.model_dump(),
        "api": settings.api.model_dump(),
        "jobs": settings.jobs.model_dump()
    }
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False)

@app.post("/api/leads", response_model=List[LeadOut], dependencies=[Depends(verify_api_token)])
def create_leads(payload: List[LeadCreate], db: Session = Depends(get_db)):
    """
    Import new leads from JSON payload. Normalizes URLs, validates fields,
    filters duplicates, and checks suppression list.
    """
    imported_leads = []
    for item in payload:
        email = item.email.strip() if item.email else None
        website_url = item.website_url.strip() if item.website_url else None
        name = item.name.strip() if item.name else None
        
        lead = Lead(
            name=name,
            email=email,
            website_url=website_url,
            country=item.country or "US"
        )
        
        if not email or not is_valid_email(email):
            lead.status = "failed"
            lead.error_message = f"Invalid email format: {email}"
        elif not website_url:
            lead.status = "failed"
            lead.error_message = "Invalid or missing website URL"
        else:
            normalized = normalize_url(website_url)
            if not normalized:
                lead.status = "failed"
                lead.error_message = f"Invalid website URL: {website_url}"
            else:
                lead.website_url = normalized
                lead.domain = extract_domain(normalized)
                
                # Suppression list check
                is_suppressed = db.query(Suppression).filter(Suppression.email == email).first() is not None
                if is_suppressed:
                    lead.status = "suppressed"
                    lead.error_message = "Email found on suppression list"
                else:
                    # Deduplication check
                    existing_email = db.query(Lead).filter(Lead.email == email).first()
                    existing_domain = db.query(Lead).filter(Lead.domain == lead.domain).first() if lead.domain else None
                    if existing_email or existing_domain:
                        # Duplicate skip
                        continue
                        
        db.add(lead)
        db.commit()
        db.refresh(lead)
        imported_leads.append(lead)
        
    return imported_leads

@app.get("/api/leads", response_model=List[LeadOut], dependencies=[Depends(verify_api_token)])
def list_leads(
    status: Optional[str] = Query(None, description="Filter leads by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get a list of leads, optionally filtered by status, with pagination support.
    """
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    
    leads = query.order_by(Lead.id.desc()).offset(offset).limit(limit).all()
    return leads

@app.get("/api/leads/{lead_id}", response_model=LeadDetailOut, dependencies=[Depends(verify_api_token)])
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information for a specific lead by its ID.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lead with ID {lead_id} not found"
        )
    return lead

@app.get("/api/screenshots/{lead_id}", dependencies=[Depends(verify_api_token)])
def get_screenshot(lead_id: int, db: Session = Depends(get_db)):
    """
    Serves the screenshot file for the given lead scrape.
    """
    scrape = db.query(Scrape).filter(Scrape.lead_id == lead_id).first()
    if not scrape or not scrape.screenshot_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No scrape or screenshot available for lead ID {lead_id}"
        )
        
    path = scrape.screenshot_path
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Screenshot file not found on disk: {path}"
        )
        
    # Return file response with image type
    return FileResponse(path, media_type="image/png")

@app.get("/api/stats", response_model=Dict[str, int], dependencies=[Depends(verify_api_token)])
def get_stats(db: Session = Depends(get_db)):
    """
    Returns counts of leads grouped by their pipeline statuses.
    """
    counts = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
    
    # Initialize dictionary with all possible statuses set to 0
    statuses = [
        "pending", "scraped", "analyzed", "drafted", 
        "skipped_no_findings", "approved", "rejected", 
        "sent", "failed", "suppressed"
    ]
    result = {s: 0 for s in statuses}
    
    for status_name, count in counts:
        if status_name in result:
            result[status_name] = count
        else:
            result[status_name] = count # support dynamic statuses if any
            
    return result

@app.get("/api/config", dependencies=[Depends(verify_api_token)])
def get_config():
    """
    Get the non-secret configuration variables.
    """
    return {
        "csv": settings.csv.model_dump(),
        "scrape": settings.scrape.model_dump(),
        "analysis": settings.analysis.model_dump(),
        "service_map": settings.service_map.model_dump(),
        "email": settings.email.model_dump(),
        "send": settings.send.model_dump(),
        "api": settings.api.model_dump(),
        "jobs": settings.jobs.model_dump()
    }

@app.post("/api/config", dependencies=[Depends(verify_api_token)])
def update_config(payload: Dict[str, Any]):
    """
    Update configuration settings dynamically and save to config.yaml.
    """
    try:
        if "csv" in payload:
            settings.csv = settings.csv.__class__(**payload["csv"])
        if "scrape" in payload:
            settings.scrape = settings.scrape.__class__(**payload["scrape"])
        if "analysis" in payload:
            settings.analysis = settings.analysis.__class__(**payload["analysis"])
        if "service_map" in payload:
            settings.service_map = settings.service_map.__class__(**payload["service_map"])
        if "email" in payload:
            settings.email = settings.email.__class__(**payload["email"])
        if "send" in payload:
            settings.send = settings.send.__class__(**payload["send"])
        if "api" in payload:
            settings.api = settings.api.__class__(**payload["api"])
        if "jobs" in payload:
            settings.jobs = settings.jobs.__class__(**payload["jobs"])
            
        save_settings_to_yaml()
        return {"success": True, "message": "Configuration updated and saved successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update configuration: {str(e)}"
        )

# Pydantic schema for creating a Job
class JobCreate(BaseModel):
    type: str  # scrape | analyze | generate | send | bakeoff
    params: Optional[Dict[str, Any]] = None

@app.post("/api/jobs", response_model=JobOut, dependencies=[Depends(verify_api_token)])
def create_job(payload: JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Enqueue a background job for a pipeline stage.
    """
    if payload.type not in ["scrape", "analyze", "generate", "send", "bakeoff"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job type '{payload.type}'. Supported types: scrape, analyze, generate, send, bakeoff"
        )
    job = enqueue_job(payload.type, payload.params or {}, db, background_tasks)
    return job

@app.get("/api/jobs", response_model=List[JobOut], dependencies=[Depends(verify_api_token)])
def list_jobs(limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    """
    List history of background pipeline jobs.
    """
    jobs = db.query(Job).order_by(Job.id.desc()).limit(limit).all()
    return jobs

@app.get("/api/jobs/{job_id}", response_model=JobOut, dependencies=[Depends(verify_api_token)])
def get_job(job_id: int, db: Session = Depends(get_db)):
    """
    Retrieve specific job status details by ID.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
    return job

@app.post("/api/jobs/{job_id}/cancel", dependencies=[Depends(verify_api_token)])
def cancel_job(job_id: int, db: Session = Depends(get_db)):
    """
    Triggers cooperative task cancellation on a running or queued job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
        
    if job.status not in ["queued", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job {job_id} is in status '{job.status}' and cannot be cancelled"
        )
        
    task = running_tasks.get(job_id)
    if task:
        task.cancel()
        return {"success": True, "message": "Job cancellation requested"}
    else:
        # Fallback in case of stray db state
        job.status = "cancelled"
        job.finished_at = datetime.utcnow()
        db.commit()
        return {"success": True, "message": "Job marked as cancelled in database"}

@app.get("/api/events/jobs/{job_id}", dependencies=[Depends(verify_api_token)])
async def stream_job_events(job_id: int, db: Session = Depends(get_db)):
    """
    Exposes Server-Sent Events (SSE) streaming progress and status updates for a background job.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
        
    async def event_generator():
        queue = asyncio.Queue()
        job_listeners.setdefault(job_id, []).append(queue)
        
        # Stream initial status immediately
        yield {
            "event": "message",
            "data": json.dumps({
                "id": job.id,
                "type": job.type,
                "status": job.status,
                "done": job.done,
                "total": job.total,
                "error": job.error
            })
        }
        
        if job.status in ["completed", "failed", "cancelled"]:
            return

        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": "message",
                        "data": json.dumps(msg)
                    }
                    if msg.get("status") in ["completed", "failed", "cancelled"]:
                        break
                except asyncio.TimeoutError:
                    # Keep-alive comment ping
                    yield {
                        "comment": "keep-alive"
                    }
        finally:
            if job_id in job_listeners:
                if queue in job_listeners[job_id]:
                    job_listeners[job_id].remove(queue)
                if not job_listeners[job_id]:
                    del job_listeners[job_id]
                    
    return EventSourceResponse(event_generator())

# ----------------------------------------------------
# REVIEW QUEUE & LEADS DRAFT MANAGEMENT API
# ----------------------------------------------------

class RejectionPayload(BaseModel):
    reject_reason: Optional[str] = None

@app.post("/api/leads/{lead_id}/approve", dependencies=[Depends(verify_api_token)])
def approve_lead_email(lead_id: int, db: Session = Depends(get_db)):
    """
    Approve the lead's email draft, setting lead and email status to approved.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
        
    email_row = db.query(Email).filter(Email.lead_id == lead.id, Email.status == "draft").first()
    if not email_row:
        # Check if already approved
        already_approved = db.query(Email).filter(Email.lead_id == lead.id, Email.status == "approved").first()
        if already_approved:
            return {"success": True, "message": "Email is already approved"}
        raise HTTPException(status_code=404, detail=f"Draft email for lead {lead_id} not found")
        
    email_row.status = "approved"
    email_row.approved_at = datetime.utcnow()
    lead.status = "approved"
    lead.error_message = None
    db.commit()
    return {"success": True, "message": f"Lead {lead_id} email approved successfully"}

@app.post("/api/leads/{lead_id}/reject", dependencies=[Depends(verify_api_token)])
def reject_lead_email(lead_id: int, payload: RejectionPayload, db: Session = Depends(get_db)):
    """
    Reject the lead's email draft, setting status to rejected with optional reason.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
        
    email_row = db.query(Email).filter(Email.lead_id == lead.id, Email.status == "draft").first()
    if not email_row:
        # Check if already rejected
        already_rejected = db.query(Email).filter(Email.lead_id == lead.id, Email.status == "rejected").first()
        if already_rejected:
            return {"success": True, "message": "Email is already rejected"}
        raise HTTPException(status_code=404, detail=f"Draft email for lead {lead_id} not found")
        
    email_row.status = "rejected"
    email_row.reject_reason = payload.reject_reason
    lead.status = "rejected"
    db.commit()
    return {"success": True, "message": f"Lead {lead_id} email rejected successfully"}

@app.post("/api/leads/{lead_id}/edit", dependencies=[Depends(verify_api_token)])
def edit_lead_email(lead_id: int, payload: EmailDraft, db: Session = Depends(get_db)):
    """
    Edit the lead's email draft subject and body. Appends the compliance footer.
    """
    from src.core.generate import append_compliance_footer
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")
        
    email_row = db.query(Email).filter(Email.lead_id == lead.id, Email.status == "draft").first()
    if not email_row:
        raise HTTPException(status_code=404, detail=f"Draft email for lead {lead_id} not found")
        
    email_row.subject = payload.subject
    # Append the compliance footer using the lead's email address
    email_row.body = append_compliance_footer(payload.body, lead.email)
    db.commit()
    return {"success": True, "message": f"Draft email for lead {lead_id} updated successfully"}

# ----------------------------------------------------
# SUPPRESSION LIST MANAGEMENT API
# ----------------------------------------------------

@app.get("/api/suppression", response_model=List[SuppressionOut], dependencies=[Depends(verify_api_token)])
def list_suppressions(db: Session = Depends(get_db)):
    """
    Get a list of all emails in the suppression list.
    """
    return db.query(Suppression).order_by(Suppression.added_at.desc()).all()

@app.post("/api/suppression", response_model=SuppressionOut, dependencies=[Depends(verify_api_token)])
def add_suppression(payload: SuppressionCreate, db: Session = Depends(get_db)):
    """
    Add an email to the suppression list and mark matching leads as suppressed.
    """
    email_clean = payload.email.strip().lower()
    
    # Check if already suppressed
    existing = db.query(Suppression).filter(Suppression.email == email_clean).first()
    if existing:
        return existing
        
    supp = Suppression(
        email=email_clean,
        reason=payload.reason,
        added_at=datetime.utcnow()
    )
    db.add(supp)
    
    # Update matching leads
    leads = db.query(Lead).filter(Lead.email == email_clean).all()
    for lead in leads:
        lead.status = "suppressed"
        lead.error_message = "Email added to suppression list manually"
        
    db.commit()
    db.refresh(supp)
    return supp

@app.delete("/api/suppression/{email}", dependencies=[Depends(verify_api_token)])
def delete_suppression(email: str, db: Session = Depends(get_db)):
    """
    Remove an email from the suppression list.
    """
    email_clean = email.strip().lower()
    supp = db.query(Suppression).filter(Suppression.email == email_clean).first()
    if not supp:
        raise HTTPException(status_code=404, detail=f"Email '{email}' not found on suppression list")
        
    db.delete(supp)
    db.commit()
    return {"success": True, "message": f"Email '{email}' removed from suppression list"}

# ----------------------------------------------------
# MODEL BAKEOFF COMPARISON API
# ----------------------------------------------------

class BakeoffRequest(BaseModel):
    sample_size: int = 3
    models: Optional[List[str]] = None

@app.post("/api/bakeoff", dependencies=[Depends(verify_api_token)])
async def get_bakeoff_comparison(payload: BakeoffRequest, db: Session = Depends(get_db)):
    """
    Run model comparison bake-off synchronously and return the side-by-side results.
    """
    from src.llm.bakeoff import run_model_comparison
    results = await run_model_comparison(db, sample_size=payload.sample_size, models=payload.models)
    return results
