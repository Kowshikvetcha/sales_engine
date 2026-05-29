import csv
import io
import re
from typing import Dict, Any, List, Union, Optional
from sqlalchemy.orm import Session
from src.db import Lead, Suppression
from src.utils.url import normalize_url, extract_domain
from src.config import settings

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def is_valid_email(email: str) -> bool:
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))

def parse_headers(headers: List[str], config_map: Dict[str, str]) -> Dict[str, str]:
    """
    Tries to map CSV headers to standard fields (name, website, email).
    Uses the provided config_map first, then falls back to common header variants.
    """
    result = {}
    lower_headers = [h.strip().lower() for h in headers]
    
    # Try direct mapping from config
    for key, val in config_map.items():
        val_lower = val.strip().lower()
        if val_lower in lower_headers:
            idx = lower_headers.index(val_lower)
            result[key] = headers[idx]
            
    # Standard fallback variants
    variants = {
        "name": ["name", "business name", "company", "company name", "contact name", "business"],
        "website": ["website", "site", "url", "website url", "web", "domain"],
        "email": ["email", "e-mail", "mail", "email address"]
    }
    
    for key in ["name", "website", "email"]:
        if key not in result:
            for variant in variants[key]:
                if variant in lower_headers:
                    idx = lower_headers.index(variant)
                    result[key] = headers[idx]
                    break
                    
    # Substring matching if still not found
    for key in ["name", "website", "email"]:
        if key not in result:
            for h, lh in zip(headers, lower_headers):
                if lh.startswith(key) or key in lh:
                    result[key] = h
                    break
                    
    return result

def ingest_csv(
    db: Session,
    csv_data: Union[str, bytes, io.StringIO, io.BytesIO],
    column_map: Optional[Dict[str, str]] = None
) -> Dict[str, int]:
    """
    Ingests leads from a CSV source, validates emails and URLs, performs deduplication,
    checks the suppression list, and stores them in the database.
    
    Returns a summary dictionary of the ingestion results.
    """
    if column_map is None:
        column_map = settings.csv.column_map

    # Resolve input into a text stream
    if isinstance(csv_data, bytes):
        text_stream = io.StringIO(csv_data.decode("utf-8-sig"))
    elif isinstance(csv_data, str):
        text_stream = io.StringIO(csv_data)
    elif isinstance(csv_data, io.BytesIO):
        text_stream = io.StringIO(csv_data.read().decode("utf-8-sig"))
    else:
        text_stream = csv_data

    reader = csv.reader(text_stream)
    
    # Read headers
    try:
        headers = next(reader)
    except StopIteration:
        return {"total": 0, "imported": 0, "duplicates": 0, "suppressed": 0, "failed": 0}

    mapped_headers = parse_headers(headers, column_map)
    
    name_col = mapped_headers.get("name")
    web_col = mapped_headers.get("website")
    email_col = mapped_headers.get("email")

    # Map header name to list index
    name_idx = headers.index(name_col) if name_col in headers else -1
    web_idx = headers.index(web_col) if web_col in headers else -1
    email_idx = headers.index(email_col) if email_col in headers else -1

    stats = {"total": 0, "imported": 0, "duplicates": 0, "suppressed": 0, "failed": 0}
    
    # Cache existing emails and domains from the database to speed up deduplication
    existing_emails = set(row[0] for row in db.query(Lead.email).filter(Lead.email.isnot(None)).all())
    existing_domains = set(row[0] for row in db.query(Lead.domain).filter(Lead.domain.isnot(None)).all())
    
    # Also fetch suppression list
    suppression_list = set(row[0] for row in db.query(Suppression.email).all())

    # Keep track of duplicate entries encountered during *this* batch run
    seen_emails_batch = set()
    seen_domains_batch = set()

    for row in reader:
        if not row or all(cell.strip() == "" for cell in row):
            continue  # Skip empty rows
            
        stats["total"] += 1
        
        # Extract row fields
        name = row[name_idx].strip() if 0 <= name_idx < len(row) else ""
        raw_web = row[web_idx].strip() if 0 <= web_idx < len(row) else ""
        raw_email = row[email_idx].strip() if 0 <= email_idx < len(row) else ""
        
        # Email validation and cleanup
        email = raw_email.lower() if raw_email else ""
        
        # URL normalization and domain extraction
        normalized_url = normalize_url(raw_web)
        domain = extract_domain(raw_web)
        
        # 1. Deduplication Checks (Email & Domain)
        is_duplicate = (
            (email and (email in existing_emails or email in seen_emails_batch)) or 
            (domain and (domain in existing_domains or domain in seen_domains_batch))
        )
        
        if is_duplicate:
            stats["duplicates"] += 1
            continue  # Skip duplicates without writing to DB
            
        # 2. Validation Checks
        if not email:
            stats["failed"] += 1
            lead = Lead(
                name=name,
                website_url=raw_web,
                domain=domain,
                email=None,
                status="failed",
                error_message="Missing email address",
                country="US"
            )
            db.add(lead)
            if domain:
                seen_domains_batch.add(domain)
            continue
            
        if not is_valid_email(email):
            stats["failed"] += 1
            lead = Lead(
                name=name,
                website_url=raw_web,
                domain=domain,
                email=email,
                status="failed",
                error_message="Invalid email syntax",
                country="US"
            )
            db.add(lead)
            seen_emails_batch.add(email)
            if domain:
                seen_domains_batch.add(domain)
            continue
            
        if not normalized_url or not domain:
            stats["failed"] += 1
            lead = Lead(
                name=name,
                website_url=raw_web,
                domain=domain,
                email=email,
                status="failed",
                error_message="Invalid or missing website URL",
                country="US"
            )
            db.add(lead)
            seen_emails_batch.add(email)
            continue

        # 3. Suppression check
        if email in suppression_list:
            stats["suppressed"] += 1
            lead = Lead(
                name=name,
                website_url=normalized_url,
                domain=domain,
                email=email,
                status="suppressed",
                error_message="Email found on suppression list",
                country="US"
            )
            db.add(lead)
            seen_emails_batch.add(email)
            if domain:
                seen_domains_batch.add(domain)
            continue

        # 4. Successful Ingest
        lead = Lead(
            name=name,
            website_url=normalized_url,
            domain=domain,
            email=email,
            status="pending",
            country="US"
        )
        db.add(lead)
        
        # Track in batch caches
        seen_emails_batch.add(email)
        if domain:
            seen_domains_batch.add(domain)
        stats["imported"] += 1

    db.commit()
    return stats
