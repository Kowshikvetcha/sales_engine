import httpx
from typing import Dict, Any, Optional
from src.config import settings
from src.utils.logging import logger

PAGESPEED_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

async def run_pagespeed_audit(url: str) -> Optional[Dict[str, Any]]:
    """
    Queries Google PageSpeed Insights API for Lighthouse scores.
    If the API key is set to 'mock-key', empty, or queries fail,
    it returns a default mocked analysis response to support local dry-runs.
    """
    api_key = settings.pagespeed_api_key
    strategy = settings.analysis.pagespeed_strategy or "mobile"

    # Detect if we should use mock fallback
    if not api_key or api_key == "mock-key":
        logger.warning(
            "PageSpeed API key is missing or set to mock-key. Falling back to default mock scores.",
            url=url
        )
        return {
            "perf_score": 45,
            "seo_score": 68,
            "accessibility_score": 82,
            "best_practices_score": 75,
            "mobile_friendly": False,
            "load_time_ms": 4500,
        }

    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "seo", "accessibility", "best-practices"],
    }
    if api_key:
        params["key"] = api_key

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info("Querying PageSpeed Insights API...", url=url, strategy=strategy)
            response = await client.get(PAGESPEED_API_URL, params=params)
            
            if response.status_code != 200:
                logger.error(
                    "PageSpeed API returned non-200 status", 
                    status_code=response.status_code, 
                    body=response.text
                )
                # Fallback to mock on API failure to prevent blocking execution
                return None
                
            data = response.json()
            lh_result = data.get("lighthouseResult", {})
            categories = lh_result.get("categories", {})
            
            # Scores are fractions between 0 and 1. We scale to 0-100.
            perf = int(categories.get("performance", {}).get("score", 0) * 100)
            seo = int(categories.get("seo", {}).get("score", 0) * 100)
            a11y = int(categories.get("accessibility", {}).get("score", 0) * 100)
            bp = int(categories.get("best-practices", {}).get("score", 0) * 100)
            
            # Get Speed Index or Interactive load time
            speed_index_audit = lh_result.get("audits", {}).get("speed-index", {})
            load_time_ms = int(speed_index_audit.get("numericValue", 2000))
            
            # Mobile friendly check based on viewport audit
            viewport_audit = lh_result.get("audits", {}).get("viewport", {})
            mobile_friendly = viewport_audit.get("score") == 1
            
            return {
                "perf_score": perf,
                "seo_score": seo,
                "accessibility_score": a11y,
                "best_practices_score": bp,
                "mobile_friendly": mobile_friendly,
                "load_time_ms": load_time_ms,
            }
    except Exception as e:
        logger.error("Exception during PageSpeed Insight audit", error=str(e), url=url)
        return None
