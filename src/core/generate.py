import json
import asyncio
from datetime import datetime
import time
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from src.db import Lead, Analysis, Email
from src.config import settings
from src.llm.client import build_llm
from src.llm.prompts import COLD_EMAIL_SYSTEM_PROMPT, COLD_EMAIL_USER_TEMPLATE
from src.llm.validate import validate_grounding
from src.utils.logging import logger

def append_compliance_footer(body: str, email_address: str) -> str:
    """
    Appends CAN-SPAM compliant details (physical address + unsubscribe link) deterministically.
    Never relies on the LLM to format this section.
    """
    company = settings.email.sender_company
    address = settings.email.physical_address
    unsub_url = settings.email.unsubscribe_base_url
    
    footer = (
        f"\n\n---\n"
        f"{company} | {address}\n"
        f"To unsubscribe from future audits, click here: {unsub_url}?email={email_address}"
    )
    return body + footer

async def generate_email_for_lead(
    db: Session,
    lead_id: int,
    model_override: Optional[str] = None,
    provider_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Orchestrates cold email generation:
    1. Loads lead and mapped service findings.
    2. Invokes LLM (or mock output) to draft a JSON email.
    3. Runs grounding validation.
    4. Appends compliance footer and saves draft.
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        return {"success": False, "error": "Lead not found"}
        
    analysis = lead.analysis
    if not analysis or not analysis.service_map:
        lead.status = "failed"
        lead.error_message = "No mapped service findings for email generation"
        db.commit()
        return {"success": False, "error": "No findings mapped"}
        
    findings_dict = analysis.service_map
    evidence_list = [entry["evidence"] for entry in findings_dict.values()]
    
    api_key = settings.anthropic_api_key or settings.openai_api_key or settings.google_api_key
    model_name = model_override or settings.llm.default_model
    provider_name = provider_override or settings.llm.default_provider

    subject = ""
    body = ""
    findings_cited = []

    # 1. Check if mock API key
    if not api_key or api_key == "mock-key":
        # Generate detailed mock email based on findings mapping to services
        subject = f"Website Audit & Growth Strategy for {lead.name or lead.domain}"
        body_parts = [
            f"Hi {lead.name or 'there'},\n\n"
            f"I recently conducted a technical audit of the website for {lead.name or lead.domain}. "
            f"I identified a few key areas where we can make significant improvements to enhance your visitor experience, SEO rankings, and lead conversion rates:"
        ]
        
        # Build detailed breakdown matching how the agency can help
        for service, info in findings_dict.items():
            ev = info["evidence"]
            if service == "Full-stack design":
                body_parts.append(
                    f"\n- Design & UX Opportunity: We detected that {ev}. "
                    f"Our Full-stack design services can optimize your page load speeds, resolve any responsive layout issues, "
                    f"and ensure secure SSL connections to restore visitor trust and search ranking."
                )
            elif service == "CRM":
                body_parts.append(
                    f"\n- CRM & Lead Capture Optimization: Our audit noted that {ev}. "
                    f"By implementing a customized CRM form, we can connect inquiries directly to your sales pipeline, "
                    f"automating follow-ups and stopping leads from falling through the cracks."
                )
            elif service == "Data analytics":
                body_parts.append(
                    f"\n- Analytics & SEO Tracking: The audit showed that {ev}. "
                    f"Our Data analytics solutions can instrument visitor tracking and web traffic instrumentation, "
                    f"helping you track performance and boost organic SEO presence."
                )
            elif service == "Full-stack data solutions":
                body_parts.append(
                    f"\n- Systems Integration: We found that {ev}. "
                    f"We can build automated database flows and API links, eliminating manual processes and making your operations seamless."
                )
        
        body_parts.append(
            f"\n\nWe specialize in resolving these technical gaps. {settings.email.cta or 'Would you be open to a quick call next week to discuss this?'}\n\n"
            f"Best regards,\n"
            f"{settings.email.sender_name}\n"
            f"{settings.email.sender_company}"
        )
        body = "".join(body_parts)
        findings_cited = evidence_list
        is_grounded = True
        logger.info("Mock LLM generation complete", lead_id=lead.id)
    else:
        # Live generation with retry loop
        max_attempts = settings.llm.max_generation_attempts or 3
        is_grounded = False
        attempt = 0
        validation_reason = ""
        
        llm = build_llm(model=model_name, provider=provider_name)
        
        user_prompt = COLD_EMAIL_USER_TEMPLATE.format(
            lead_name=lead.name or "Website Owner",
            business=lead.name or lead.domain,
            website_url=lead.website_url,
            findings="\n".join(f"- {ev}" for ev in evidence_list),
            cta=settings.email.cta
        )
        
        messages = [
            {"role": "system", "content": COLD_EMAIL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        while attempt < max_attempts and not is_grounded:
            attempt += 1
            try:
                logger.info(
                    "Querying LLM for email draft...", 
                    lead_id=lead.id, 
                    model=model_name, 
                    attempt=attempt
                )
                response = await llm.ainvoke(messages)
                content = response.content.strip()
                
                # Clean JSON code wrapper formatting
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                email_json = json.loads(content)
                subject = email_json.get("subject", "").strip()
                body = email_json.get("body", "").strip()
                
                # Validate grounding
                is_grounded, findings_cited, validation_reason = await validate_grounding(body, evidence_list)
                
                if not is_grounded:
                    logger.warning(
                        "Grounding validation failed. Retrying email generation...",
                        lead_id=lead.id,
                        reason=validation_reason
                    )
                    # Append feedback to messages for retry
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user", 
                        "content": f"Your previous draft failed grounding validation for this reason: {validation_reason}. Please regenerate and ensure all claims are strictly backed by the findings list."
                    })
                    
            except Exception as e:
                logger.error("Exception during LLM email generation", error=str(e), lead_id=lead.id)
                validation_reason = str(e)
                
        if not is_grounded:
            lead.status = "failed"
            lead.error_message = f"Email generation failed grounding validator: {validation_reason}"
            db.commit()
            return {"success": False, "error": f"Failed validation: {validation_reason}"}

    # 2. Append compliance footer and save draft
    final_body = append_compliance_footer(body, lead.email)
    
    email_row = db.query(Email).filter(Email.lead_id == lead.id).first()
    if not email_row:
        email_row = Email(lead_id=lead.id)
        db.add(email_row)
        
    email_row.model_used = model_name
    email_row.subject = subject
    email_row.body = final_body
    email_row.findings_cited = findings_cited
    email_row.status = "draft"
    email_row.generated_at = datetime.utcnow() if hasattr(datetime, "utcnow") else time.time()
    
    lead.status = "drafted"
    lead.error_message = None
    db.commit()
    
    return {"success": True, "lead_id": lead.id, "subject": subject}

async def run_email_generation(
    db: Session,
    limit: Optional[int] = None,
    model_override: Optional[str] = None,
    provider_override: Optional[str] = None,
    progress_callback = None
) -> Dict[str, int]:
    """
    Iterates over analyzed leads, generating structured, grounded emails.
    """
    query = db.query(Lead).filter(Lead.status == "analyzed")
    if limit is not None:
        query = query.limit(limit)
        
    analyzed_leads = query.all()
    if not analyzed_leads:
        return {"total": 0, "success": 0, "failed": 0}
        
    total = len(analyzed_leads)
    done = 0

    async def wrapped_generate(lead_id):
        nonlocal done
        res = await generate_email_for_lead(db, lead_id, model_override, provider_override)
        done += 1
        if progress_callback:
            await progress_callback(done, total)
        return res

    tasks = [
        wrapped_generate(lead.id)
        for lead in analyzed_leads
    ]
    results = await asyncio.gather(*tasks)
    
    stats = {"total": len(results), "success": 0, "failed": 0}
    for res in results:
        if res.get("success"):
            stats["success"] += 1
        else:
            stats["failed"] += 1
            
    return stats
