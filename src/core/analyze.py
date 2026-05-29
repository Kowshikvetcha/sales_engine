import asyncio
from datetime import datetime
import time
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import httpx
from sqlalchemy.orm import Session

from src.db import Lead, Scrape, Analysis
from src.config import settings
from src.integrations.pagespeed import run_pagespeed_audit
from src.core.service_map import map_signals_to_services
from src.utils.logging import logger

async def check_link_is_broken(url: str) -> bool:
    """
    Performs a non-blocking HEAD check (falling back to GET) to verify if a link is broken.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.head(url, follow_redirects=True)
            if resp.status_code >= 400:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code >= 400:
                    return True
            return False
    except Exception:
        return True  # Any connection error is classified as broken for audit purposes

def extract_sample_links(html: str, base_url: str, limit: int = 10) -> List[str]:
    """
    Extracts up to 'limit' unique hyperlinks from the homepage to check for broken links.
    """
    soup = BeautifulSoup(html, "lxml")
    links = set()
    
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
            
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        
        # Only check http/https links
        if parsed.scheme in ["http", "https"]:
            links.add(full_url)
            if len(links) >= limit:
                break
                
    return list(links)

def check_analytics_tags(html: str) -> bool:
    """
    Inspects homepage source code for common analytics tools (Google Analytics, GTM, Plausible, etc.).
    """
    patterns = [
        "googletagmanager.com",
        "google-analytics.com",
        "_ga",
        "gtag",
        "amplitude.com",
        "mixpanel.com",
        "plausible.io",
        "fathom"
    ]
    html_lower = html.lower()
    return any(p in html_lower for p in patterns)

def check_contact_form(html: str) -> bool:
    """
    Checks if a lead-capture input form exists on the home page.
    Returns False if inquiries rely strictly on raw mailto links.
    """
    soup = BeautifulSoup(html, "lxml")
    
    for form in soup.find_all("form"):
        # Check if form has input or textarea
        inputs = form.find_all(["input", "textarea"])
        if inputs:
            # Skip search forms
            action = form.get("action", "").lower()
            role = form.get("role", "").lower()
            if "search" not in action and "search" not in role:
                return True
                
    return False

async def analyze_single_lead(db: Session, lead_id: int) -> Dict[str, Any]:
    """
    Performs local HTML checks, head checks a sample of links, queries PageSpeed,
    runs service mapping, and saves findings in the database.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return {"success": False, "error": "Lead not found"}
        
    scrape = lead.scrape
    if not scrape or not scrape.reachable:
        lead.status = "failed"
        lead.error_message = "No successful scrape data found for analysis"
        db.commit()
        return {"success": False, "error": "No scrape data"}

    html = scrape.html_content or ""
    
    # 1. Local HTML Checks
    soup = BeautifulSoup(html, "lxml")
    
    meta_title = bool(soup.find("title"))
    
    # Check meta description or open-graph description
    meta_desc = bool(
        soup.find("meta", attrs={"name": "description"}) or 
        soup.find("meta", attrs={"property": "og:description"})
    )
    
    # Viewport check
    has_viewport = bool(soup.find("meta", attrs={"name": "viewport"}))
    
    # SSL check (based on URL scheme of successfully scraped lead)
    has_ssl = lead.website_url.startswith("https")
    
    # Analytics check
    has_analytics = check_analytics_tags(html)
    
    # Contact form check
    has_contact_form = check_contact_form(html)
    
    # 2. Broken Links Sampler
    sample_links = extract_sample_links(html, lead.website_url, settings.analysis.broken_link_sample)
    broken_count = 0
    if sample_links:
        link_checks = [check_link_is_broken(link) for link in sample_links]
        link_results = await asyncio.gather(*link_checks)
        broken_count = sum(1 for res in link_results if res)

    # 3. Google PageSpeed insights client
    psi_results = await run_pagespeed_audit(lead.website_url)
    if psi_results is None:
        # If PageSpeed fails entirely and we have no API key, use fallback
        logger.warning("PageSpeed Insight failed or returned empty. Using conservative defaults.")
        psi_results = {
            "perf_score": 50,
            "seo_score": 70,
            "accessibility_score": 70,
            "best_practices_score": 70,
            "mobile_friendly": has_viewport,
            "load_time_ms": 3000,
        }

    # 4. Compile signals dictionary
    signals = {
        "perf_score": psi_results["perf_score"],
        "seo_score": psi_results["seo_score"],
        "accessibility_score": psi_results["accessibility_score"],
        "best_practices_score": psi_results["best_practices_score"],
        "mobile_friendly": psi_results["mobile_friendly"],
        "load_time_ms": psi_results["load_time_ms"],
        "has_ssl": has_ssl,
        "meta_title_present": meta_title,
        "meta_description_present": meta_desc,
        "has_analytics": has_analytics,
        "has_contact_form": has_contact_form,
        "broken_links_count": broken_count,
    }

    # Convert dictionary to structured list format for DB saving if needed
    structured_signals_list = [
        {"key": k, "value": v, "severity": "high" if k in ["perf_score", "seo_score"] and v < 50 else "medium"}
        for k, v in signals.items()
    ]

    # 5. Service Mapping Rules Engine
    service_map = map_signals_to_services(signals, settings.service_map.max_findings)
    
    # 6. Save Analysis to DB
    analysis_row = db.query(Analysis).filter(Analysis.lead_id == lead.id).first()
    if not analysis_row:
        analysis_row = Analysis(lead_id=lead.id)
        db.add(analysis_row)
        
    analysis_row.perf_score = psi_results["perf_score"]
    analysis_row.seo_score = psi_results["seo_score"]
    analysis_row.accessibility_score = psi_results["accessibility_score"]
    analysis_row.best_practices_score = psi_results["best_practices_score"]
    analysis_row.mobile_friendly = psi_results["mobile_friendly"]
    analysis_row.has_ssl = has_ssl
    analysis_row.load_time_ms = psi_results["load_time_ms"]
    analysis_row.meta_title_present = meta_title
    analysis_row.meta_description_present = meta_desc
    analysis_row.broken_links_count = broken_count
    analysis_row.signals = structured_signals_list
    analysis_row.service_map = service_map
    analysis_row.analyzed_at = datetime.utcnow() if hasattr(datetime, "utcnow") else time.time()
    
    # 7. Update status
    if not service_map:
        lead.status = "skipped_no_findings"
        lead.error_message = "Analysis generated zero grounded weaknesses"
    else:
        lead.status = "analyzed"
        lead.error_message = None
        
    db.commit()
    return {"success": True, "lead_id": lead.id, "status": lead.status, "findings": len(service_map)}

async def run_analysis(db: Session, limit: Optional[int] = None, progress_callback = None) -> Dict[str, int]:
    """
    Processes all scraped leads, runs analysis and service mapping.
    """
    query = db.query(Lead).filter(Lead.status == "scraped")
    if limit is not None:
        query = query.limit(limit)
        
    scraped_leads = query.all()
    if not scraped_leads:
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0}
        
    total = len(scraped_leads)
    done = 0

    async def wrapped_analyze(lead_id):
        nonlocal done
        res = await analyze_single_lead(db, lead_id)
        done += 1
        if progress_callback:
            await progress_callback(done, total)
        return res

    tasks = [wrapped_analyze(lead.id) for lead in scraped_leads]
    results = await asyncio.gather(*tasks)
    
    stats = {"total": len(results), "success": 0, "failed": 0, "skipped": 0}
    for res in results:
        if res.get("success"):
            if res.get("status") == "skipped_no_findings":
                stats["skipped"] += 1
            else:
                stats["success"] += 1
        else:
            stats["failed"] += 1
            
    return stats
