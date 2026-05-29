from typing import Dict, List, Any, Tuple
from src.config import settings

def map_signals_to_services(
    signals_dict: Dict[str, Any],
    max_findings: int = 3
) -> Dict[str, Dict[str, str]]:
    """
    Evaluates objective analysis signals and maps them to B2B services we sell:
    - Full-stack design
    - CRM
    - Data analytics
    - Full-stack data solutions

    Returns a service map: {service_name: {"service": service_name, "evidence": evidence_string}}
    ordered by finding severity.
    """
    findings: List[Tuple[str, str, str]] = []  # List of (service_name, evidence_string, severity)

    # 1. Performance check -> Full-stack design
    perf_score = signals_dict.get("perf_score")
    load_time_ms = signals_dict.get("load_time_ms", 0)
    
    if perf_score is not None and (perf_score < 50 or load_time_ms > 4000):
        severity = "high" if perf_score < 30 or load_time_ms > 6000 else "medium"
        evidence = f"Homepage loads in {load_time_ms} ms (Lighthouse performance {perf_score}/100)"
        findings.append(("Full-stack design", evidence, severity))

    # 2. Mobile friendly check -> Full-stack design
    mobile_friendly = signals_dict.get("mobile_friendly")
    if mobile_friendly is False:
        findings.append((
            "Full-stack design",
            "Not mobile-optimized (no responsive viewport detected)",
            "high"
        ))

    # 3. SSL check -> Full-stack design
    has_ssl = signals_dict.get("has_ssl")
    if has_ssl is False:
        findings.append((
            "Full-stack design",
            "No valid SSL certificate (served over HTTP)",
            "high"
        ))

    # 4. SEO check / missing meta -> Data analytics / Full-stack design
    seo_score = signals_dict.get("seo_score")
    meta_title = signals_dict.get("meta_title_present", True)
    meta_desc = signals_dict.get("meta_description_present", True)
    
    if seo_score is not None and seo_score < 70:
        meta_gap = ""
        if not meta_title and not meta_desc:
            meta_gap = "meta title and description"
        elif not meta_title:
            meta_gap = "meta title"
        elif not meta_desc:
            meta_gap = "meta description"
        else:
            meta_gap = "meta tags optimization"
            
        evidence = f"Missing {meta_gap}; SEO score {seo_score}/100"
        severity = "high" if seo_score < 50 else "medium"
        
        # We can offer Data analytics for SEO tracking, or Design for layouts
        findings.append(("Data analytics", evidence, severity))

    # 5. Contact form check -> CRM
    has_contact_form = signals_dict.get("has_contact_form", True)
    if not has_contact_form:
        findings.append((
            "CRM",
            "No lead-capture form found; inquiries rely on a raw email link",
            "medium"
        ))

    # 6. Analytics tag check -> Data analytics
    has_analytics = signals_dict.get("has_analytics", True)
    if not has_analytics:
        findings.append((
            "Data analytics",
            "No visitor analytics or personalization detected",
            "medium"
        ))

    # 7. Evident manual workflow / no integrations -> Full-stack data solutions
    # If a site has no form and no analytics, it is a fully static site and relies on manual workflows.
    if not has_contact_form and not has_analytics:
        findings.append((
            "Full-stack data solutions",
            "Manual processes visible; no system integrations detected",
            "low"
        ))

    # Deduplicate findings per service and pick the most severe finding for each service
    severity_order = {"high": 3, "medium": 2, "low": 1}
    service_best_finding: Dict[str, Tuple[str, str]] = {}  # service_name -> (evidence, severity)
    
    for service, evidence, severity in findings:
        current_sev_val = severity_order.get(severity, 1)
        if service in service_best_finding:
            existing_sev_val = severity_order.get(service_best_finding[service][1], 1)
            if current_sev_val > existing_sev_val:
                service_best_finding[service] = (evidence, severity)
        else:
            service_best_finding[service] = (evidence, severity)

    # Sort final findings by severity value descending
    sorted_services = sorted(
        service_best_finding.items(),
        key=lambda item: severity_order.get(item[1][1], 1),
        reverse=True
    )

    # Limit to max_findings
    selected_findings = sorted_services[:max_findings]

    # Convert to expected service_map structure
    service_map = {}
    for service, (evidence, _) in selected_findings:
        service_map[service] = {
            "service": service,
            "evidence": evidence
        }

    return service_map
