import os
import time
import asyncio
import urllib.robotparser
from urllib.parse import urlparse, urljoin, urlunparse
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, BrowserContext
from datetime import datetime
from sqlalchemy.orm import Session
from src.db import Lead, Scrape
from src.config import settings
from src.utils.url import extract_domain, normalize_url
from src.utils.logging import logger  # We will create this simple logging helper or use structlog

# Initialize screenshots directory
SCREENSHOTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "screenshots"))
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Domain politeness registry
class PolitenessCoordinator:
    def __init__(self, delay_ms: int):
        self.delay_s = delay_ms / 1000.0
        self.last_fetch_times: Dict[str, float] = {}
        self.lock = asyncio.Lock()

    async def wait_for_politeness(self, domain: str):
        if self.delay_s <= 0 or not domain:
            return
        async with self.lock:
            now = time.time()
            last_time = self.last_fetch_times.get(domain, 0.0)
            elapsed = now - last_time
            if elapsed < self.delay_s:
                sleep_time = self.delay_s - elapsed
                await asyncio.sleep(sleep_time)
            self.last_fetch_times[domain] = time.time()

politeness_coordinator = PolitenessCoordinator(settings.scrape.politeness_delay_ms)
scrape_semaphore = asyncio.Semaphore(settings.scrape.concurrency)

# Helper: check robots.txt
async def check_robots_allowed(url: str, user_agent: str = "*") -> bool:
    """
    Checks if a URL is allowed to be scraped based on robots.txt.
    Fetches robots.txt using httpx to prevent blocking.
    """
    if not settings.scrape.respect_robots:
        return True
    try:
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        # import httpx dynamically to avoid overhead if not used
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(robots_url)
            if resp.status_code == 404:
                return True
            elif resp.status_code >= 400:
                return True
            
            rp = urllib.robotparser.RobotFileParser()
            lines = resp.text.splitlines()
            rp.parse(lines)
            return rp.can_fetch(user_agent, url)
    except Exception:
        # Default to allowed on any error retrieving robots.txt
        return True

def discover_internal_links(base_url: str, html: str, max_pages: int = 3) -> List[str]:
    """
    Discovers key subpages from homepage HTML matching B2B keywords (about, services, contact, pricing).
    """
    soup = BeautifulSoup(html, "lxml")
    links: List[str] = []
    seen = {normalize_url(base_url)}
    
    keywords = ["about", "service", "contact", "pricing", "team", "product", "offer", "portfolio", "solution"]
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc
    
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.lower().startswith("javascript:"):
            continue
            
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)
        
        # Verify same domain and standard scheme
        if parsed_url.netloc == base_domain and parsed_url.scheme in ["http", "https"]:
            clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", ""))
            normalized = normalize_url(clean_url)
            if not normalized or normalized in seen:
                continue
                
            path_lower = parsed_url.path.lower()
            text_lower = a.get_text().lower()
            
            if any(k in path_lower or k in text_lower for k in keywords):
                links.append(normalized)
                seen.add(normalized)
                if len(links) >= max_pages:
                    break
                    
    return links

async def scrape_page_content(page: Page, url: str, timeout_ms: int) -> Tuple[int, str]:
    """
    Navigates to a URL, waits for load state, and returns HTTP status code and text content.
    """
    response = await page.goto(url, wait_until="load", timeout=timeout_ms)
    status = response.status if response else 200
    
    # Extract visible text content
    text_content = await page.evaluate("() => document.body.innerText")
    return status, text_content or ""

async def scrape_single_lead(db: Session, lead_id: int) -> Dict[str, Any]:
    """
    Orchestrates the scraping pipeline for a single lead:
    1. Check robots.txt and wait for politeness delay
    2. Render homepage with Playwright, capture full-page screenshot
    3. Crawl subpages
    4. Store results in SQLite DB
    """
    # Fetch lead inside session
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return {"success": False, "error": "Lead not found"}
        
    url = lead.website_url
    domain = lead.domain
    
    if not url:
        lead.status = "failed"
        lead.error_message = "No website URL provided"
        db.commit()
        return {"success": False, "error": "No website URL"}

    # 1. Robots.txt pre-check
    allowed = await check_robots_allowed(url)
    if not allowed:
        lead.status = "failed"
        lead.error_message = "Blocked by robots.txt"
        db.commit()
        return {"success": False, "error": "Blocked by robots.txt"}

    # 2. Rate limiting & Politeness
    await politeness_coordinator.wait_for_politeness(domain)
    
    screenshot_filename = f"{lead.id}.png"
    screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_filename)
    
    # Track details for DB Scrapes row
    scraped_pages = {}
    rendered_text_parts = []
    
    async with scrape_semaphore:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                # Scrape Homepage
                timeout = settings.scrape.timeout_ms
                homepage_response = await page.goto(url, wait_until="networkidle", timeout=timeout)
                http_status = homepage_response.status if homepage_response else 200
                
                # Check for error status codes (e.g. 4xx, 5xx)
                if http_status >= 400:
                    raise Exception(f"HTTP error status: {http_status}")
                    
                # Take screenshot
                await page.screenshot(path=screenshot_path, full_page=True, timeout=10000)
                
                # Extract text
                html = await page.content()
                homepage_text = await page.evaluate("() => document.body.innerText")
                rendered_text_parts.append(homepage_text or "")
                scraped_pages[url] = {"status": http_status, "type": "homepage"}
                
                # Discover subpages
                subpages = discover_internal_links(url, html, settings.scrape.max_pages)
                
                # Scrape subpages sequentially to avoid overloading the site
                for sub_url in subpages:
                    await asyncio.sleep(0.5) # short buffer
                    try:
                        sub_status, sub_text = await scrape_page_content(page, sub_url, timeout)
                        rendered_text_parts.append(sub_text)
                        scraped_pages[sub_url] = {"status": sub_status, "type": "subpage"}
                    except Exception as e:
                        scraped_pages[sub_url] = {"status": None, "error": str(e), "type": "subpage"}
                
                # Combine and truncate text
                combined_text = "\n\n".join(rendered_text_parts)
                truncated_text = combined_text[:settings.scrape.max_text_chars]
                
                # Save Scrape record to DB
                scrape_row = db.query(Scrape).filter(Scrape.lead_id == lead.id).first()
                if not scrape_row:
                    scrape_row = Scrape(lead_id=lead.id)
                    db.add(scrape_row)
                    
                scrape_row.rendered_text = truncated_text
                scrape_row.html_content = html
                scrape_row.screenshot_path = screenshot_path
                scrape_row.pages_scraped = scraped_pages
                scrape_row.http_status = http_status
                scrape_row.reachable = True
                scrape_row.scraped_at = datetime.utcnow() if hasattr(datetime, "utcnow") else time.time()
                scrape_row.error = None
                
                # Update Lead status
                lead.status = "scraped"
                lead.error_message = None
                db.commit()
                
                return {"success": True, "lead_id": lead.id, "pages": len(scraped_pages)}
                
            except Exception as e:
                # Capture failure
                scrape_row = db.query(Scrape).filter(Scrape.lead_id == lead.id).first()
                if not scrape_row:
                    scrape_row = Scrape(lead_id=lead.id)
                    db.add(scrape_row)
                    
                scrape_row.rendered_text = None
                scrape_row.html_content = None
                scrape_row.screenshot_path = None
                scrape_row.pages_scraped = scraped_pages
                scrape_row.http_status = None
                scrape_row.reachable = False
                scrape_row.scraped_at = datetime.utcnow() if hasattr(datetime, "utcnow") else time.time()
                scrape_row.error = str(e)
                
                lead.status = "failed"
                lead.error_message = f"Scrape error: {str(e)}"
                db.commit()
                
                return {"success": False, "lead_id": lead.id, "error": str(e)}
            finally:
                await context.close()
                await browser.close()

async def run_scraper(db: Session, limit: Optional[int] = None, progress_callback = None) -> Dict[str, int]:
    """
    Iterates over pending leads and processes them in parallel up to configured limits.
    """
    # Fetch pending leads
    query = db.query(Lead).filter(Lead.status == "pending")
    if limit is not None:
        query = query.limit(limit)
        
    pending_leads = query.all()
    if not pending_leads:
        return {"total": 0, "success": 0, "failed": 0}
        
    total = len(pending_leads)
    done = 0

    async def wrapped_scrape(lead_id):
        nonlocal done
        res = await scrape_single_lead(db, lead_id)
        done += 1
        if progress_callback:
            await progress_callback(done, total)
        return res

    tasks = [wrapped_scrape(lead.id) for lead in pending_leads]
    results = await asyncio.gather(*tasks)
    
    stats = {"total": len(results), "success": 0, "failed": 0}
    for res in results:
        if res.get("success"):
            stats["success"] += 1
        else:
            stats["failed"] += 1
            
    return stats
