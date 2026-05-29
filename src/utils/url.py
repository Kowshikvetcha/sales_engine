import re
from typing import Optional
from urllib.parse import urlparse, urlunparse

def normalize_url(url: Optional[str]) -> Optional[str]:
    """
    Normalizes a website URL:
    - Adds https:// if no scheme is present
    - Strips tracking parameters, query params, and fragments
    - Lowercases the hostname
    """
    if not url:
        return None
    
    url = url.strip()
    if not url:
        return None
    
    # If it starts with neither http nor https, prepend https://
    if not re.match(r'^https?://', url, re.IGNORECASE):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        # Ensure scheme is lowercase (http/https) and netloc is lowercase
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        # Strip trailing dot from hostname if any
        if netloc.endswith('.'):
            netloc = netloc[:-1]
            
        # If there is port information, keep it, but netloc will contain it
        # Path cleanup: default to empty string if None
        path = parsed.path
        if not path:
            path = "/"
            
        # Reconstruct URL without query and fragment
        normalized = urlunparse((scheme, netloc, path, "", "", ""))
        return normalized
    except Exception:
        return None

def extract_domain(url: Optional[str]) -> Optional[str]:
    """
    Extracts the clean domain (hostname) from a URL.
    Example: https://www.example.com/about -> example.com or www.example.com
    We will extract the hostname and strip standard prefixes like 'www.' to get the root domain if needed,
    or just return the hostname. The spec mentions "deduplicate by domain". Returning the hostname
    with 'www.' stripped is often safer for business deduplication. Let's return the hostname
    with 'www.' stripped.
    """
    if not url:
        return None
    
    normalized = normalize_url(url)
    if not normalized:
        return None
        
    try:
        parsed = urlparse(normalized)
        hostname = parsed.hostname
        if not hostname:
            return None
            
        # Strip www.
        if hostname.startswith("www."):
            hostname = hostname[4:]
            
        return hostname
    except Exception:
        return None
