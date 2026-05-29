import os
import threading
import http.server
import socketserver
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.db import Base, Lead, Scrape
from src.core.scrape import scrape_single_lead, check_robots_allowed

class MockB2BServer:
    def __init__(self):
        self.port = 0
        self.httpd = None
        self.thread = None

    def start(self):
        class B2BHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress logs to keep test output clean
                
            def do_GET(self):
                if self.path == "/robots.txt":
                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"User-agent: *\nDisallow: /private\n")
                elif self.path == "/":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        b"<html><body>"
                        b"<h1>Acme B2B Services</h1>"
                        b"<p>We build full-stack solutions.</p>"
                        b"<a href='/about'>About Acme</a>\n"
                        b"<a href='/services'>Our Services</a>\n"
                        b"<a href='/private'>Private Stuff</a>\n"
                        b"</body></html>"
                    )
                elif self.path == "/about":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>About Acme</h1><p>Founded in 2020.</p></body></html>")
                elif self.path == "/services":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>Our Services</h1><p>We do data solutions.</p></body></html>")
                elif self.path == "/private":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>Private Area</h1></body></html>")
                else:
                    self.send_response(404)
                    self.end_headers()

        # Bind to port 0 to dynamically select an open port
        self.httpd = socketserver.TCPServer(("127.0.0.1", 0), B2BHandler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()

@pytest.fixture(scope="module")
def mock_server():
    server = MockB2BServer()
    server.start()
    yield server
    server.stop()

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

@pytest.mark.asyncio
async def test_robots_txt_checks(mock_server):
    base_url = f"http://127.0.0.1:{mock_server.port}"
    
    # Check allowed page
    allowed = await check_robots_allowed(f"{base_url}/about")
    assert allowed is True
    
    # Check disallowed page (note: we check robots on the lead home page only in our main code,
    # but check_robots_allowed should evaluate specific paths correctly if respect_robots is True)
    disallowed = await check_robots_allowed(f"{base_url}/private")
    assert disallowed is False

@pytest.mark.asyncio
async def test_scrape_success(mock_server, db_session):
    base_url = f"http://127.0.0.1:{mock_server.port}"
    
    # Insert pending lead
    lead = Lead(
        name="Acme Corp",
        website_url=base_url,
        domain=f"127.0.0.1",
        email="info@acme.com",
        status="pending"
    )
    db_session.add(lead)
    db_session.commit()
    
    # Run scraping process for the single lead
    res = await scrape_single_lead(db_session, lead.id)
    
    assert res["success"] is True
    
    # Verify DB lead status updated
    db_session.refresh(lead)
    assert lead.status == "scraped"
    assert lead.error_message is None
    
    # Verify scrape details
    scrape = db_session.query(Scrape).filter_by(lead_id=lead.id).first()
    assert scrape is not None
    assert scrape.reachable is True
    assert scrape.http_status == 200
    assert "Acme B2B Services" in scrape.rendered_text
    assert "About Acme" in scrape.rendered_text
    assert "Our Services" in scrape.rendered_text
    # Verify private area was not scraped (disallowed in robots.txt and not matches B2B keywords)
    assert "Private Area" not in scrape.rendered_text
    
    # Verify pages scraped details
    assert f"{base_url}/about" in scrape.pages_scraped
    assert f"{base_url}/services" in scrape.pages_scraped
    
    # Verify screenshot file exists
    assert scrape.screenshot_path is not None
    assert os.path.exists(scrape.screenshot_path)
    
    # Cleanup screenshot file
    if os.path.exists(scrape.screenshot_path):
        os.remove(scrape.screenshot_path)

@pytest.mark.asyncio
async def test_scrape_unreachable_fail(db_session):
    # Insert pending lead with invalid port
    lead = Lead(
        name="Failed Corp",
        website_url="http://127.0.0.1:9999",
        domain="127.0.0.1",
        email="info@failed.com",
        status="pending"
    )
    db_session.add(lead)
    db_session.commit()
    
    res = await scrape_single_lead(db_session, lead.id)
    
    assert res["success"] is False
    
    db_session.refresh(lead)
    assert lead.status == "failed"
    assert "Scrape error" in lead.error_message
    
    scrape = db_session.query(Scrape).filter_by(lead_id=lead.id).first()
    assert scrape is not None
    assert scrape.reachable is False
    assert scrape.error is not None
