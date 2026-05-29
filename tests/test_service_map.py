import pytest
from src.core.service_map import map_signals_to_services

def test_mapping_performance():
    # Performance score under 50
    signals = {
        "perf_score": 40,
        "load_time_ms": 3000,
        "mobile_friendly": True,
        "has_ssl": True,
        "seo_score": 90,
        "meta_title_present": True,
        "meta_description_present": True,
        "has_analytics": True,
        "has_contact_form": True,
    }
    
    service_map = map_signals_to_services(signals)
    assert "Full-stack design" in service_map
    assert "Lighthouse performance 40/100" in service_map["Full-stack design"]["evidence"]

def test_mapping_load_time():
    # Load time over 4000 ms
    signals = {
        "perf_score": 80,
        "load_time_ms": 5000,
        "mobile_friendly": True,
        "has_ssl": True,
        "seo_score": 95,
        "meta_title_present": True,
        "meta_description_present": True,
        "has_analytics": True,
        "has_contact_form": True,
    }
    
    service_map = map_signals_to_services(signals)
    assert "Full-stack design" in service_map
    assert "loads in 5000 ms" in service_map["Full-stack design"]["evidence"]

def test_mapping_mobile_unfriendly():
    # Not mobile friendly
    signals = {
        "perf_score": 90,
        "load_time_ms": 1500,
        "mobile_friendly": False,
        "has_ssl": True,
        "seo_score": 90,
        "meta_title_present": True,
        "meta_description_present": True,
        "has_analytics": True,
        "has_contact_form": True,
    }
    
    service_map = map_signals_to_services(signals)
    assert "Full-stack design" in service_map
    assert "Not mobile-optimized" in service_map["Full-stack design"]["evidence"]

def test_mapping_ssl_missing():
    # Served over HTTP
    signals = {
        "perf_score": 90,
        "load_time_ms": 1500,
        "mobile_friendly": True,
        "has_ssl": False,
        "seo_score": 90,
        "meta_title_present": True,
        "meta_description_present": True,
        "has_analytics": True,
        "has_contact_form": True,
    }
    
    service_map = map_signals_to_services(signals)
    assert "Full-stack design" in service_map
    assert "No valid SSL certificate" in service_map["Full-stack design"]["evidence"]

def test_mapping_seo_and_meta():
    # SEO under 70 and missing meta title/desc
    signals = {
        "perf_score": 90,
        "load_time_ms": 1500,
        "mobile_friendly": True,
        "has_ssl": True,
        "seo_score": 60,
        "meta_title_present": False,
        "meta_description_present": False,
        "has_analytics": True,
        "has_contact_form": True,
    }
    
    service_map = map_signals_to_services(signals)
    assert "Data analytics" in service_map
    assert "Missing meta title and description; SEO score 60/100" in service_map["Data analytics"]["evidence"]

def test_mapping_missing_crm_form():
    # No contact form
    signals = {
        "perf_score": 95,
        "load_time_ms": 1000,
        "mobile_friendly": True,
        "has_ssl": True,
        "seo_score": 95,
        "meta_title_present": True,
        "meta_description_present": True,
        "has_analytics": True,
        "has_contact_form": False,
    }
    
    service_map = map_signals_to_services(signals)
    assert "CRM" in service_map
    assert "No lead-capture form found" in service_map["CRM"]["evidence"]

def test_mapping_missing_analytics():
    # No analytics tag
    signals = {
        "perf_score": 95,
        "load_time_ms": 1000,
        "mobile_friendly": True,
        "has_ssl": True,
        "seo_score": 95,
        "meta_title_present": True,
        "meta_description_present": True,
        "has_analytics": False,
        "has_contact_form": True,
    }
    
    service_map = map_signals_to_services(signals)
    assert "Data analytics" in service_map
    assert "No visitor analytics or personalization detected" in service_map["Data analytics"]["evidence"]

def test_mapping_manual_workflows():
    # No contact form AND no analytics tag -> triggers manual workflows for Data solutions
    signals = {
        "perf_score": 95,
        "load_time_ms": 1000,
        "mobile_friendly": True,
        "has_ssl": True,
        "seo_score": 95,
        "meta_title_present": True,
        "meta_description_present": True,
        "has_analytics": False,
        "has_contact_form": False,
    }
    
    service_map = map_signals_to_services(signals)
    assert "Full-stack data solutions" in service_map
    assert "Manual processes visible" in service_map["Full-stack data solutions"]["evidence"]

def test_mapping_zero_findings():
    # Perfect website -> zero findings
    signals = {
        "perf_score": 95,
        "load_time_ms": 1000,
        "mobile_friendly": True,
        "has_ssl": True,
        "seo_score": 95,
        "meta_title_present": True,
        "meta_description_present": True,
        "has_analytics": True,
        "has_contact_form": True,
    }
    
    service_map = map_signals_to_services(signals)
    assert len(service_map) == 0

def test_mapping_max_findings_limit():
    # Trigger 5 findings, check that it limits to max_findings (default 3) and sorts by severity
    # Findings triggered:
    # 1. Performance (medium severity)
    # 2. SSL (high severity)
    # 3. Mobile friendly (high severity)
    # 4. SEO (medium severity)
    # 5. CRM (medium severity)
    signals = {
        "perf_score": 45,
        "load_time_ms": 4500,
        "mobile_friendly": False,
        "has_ssl": False,
        "seo_score": 55,
        "meta_title_present": False,
        "meta_description_present": False,
        "has_analytics": True,
        "has_contact_form": False,
    }
    
    # We should expect 3 services mapped, prioritizing high severity ("Full-stack design" for SSL/mobile,
    # and either CRM or Data analytics for others)
    service_map = map_signals_to_services(signals, max_findings=3)
    assert len(service_map) == 3
    
    # "Full-stack design" must be in there because it has multiple high severity signals
    assert "Full-stack design" in service_map
