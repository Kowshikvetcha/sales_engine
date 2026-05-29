import asyncio
import time
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.db import Lead, Email, Suppression, Event
from src.config import settings
from src.integrations.gmail_sender import GmailSender
from src.utils.logging import logger

def verify_compliance_config():
    """
    Refuses to send if CAN-SPAM physical address or unsubscribe URL is missing/empty.
    """
    address = settings.email.physical_address.strip()
    unsub_url = settings.email.unsubscribe_base_url.strip()
    
    if not address or address == "123 Main St, Anytown, USA":
        raise ValueError(
            "CAN-SPAM Compliance Blocker: A valid physical_address must be configured in settings/config.yaml."
        )
    if not unsub_url or unsub_url == "http://localhost:8000/unsubscribe":
        raise ValueError(
            "CAN-SPAM Compliance Blocker: A valid unsubscribe_base_url must be configured in settings/config.yaml."
        )

def get_daily_sent_count(db: Session) -> int:
    """
    Counts the number of emails sent today (since midnight UTC).
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Count sent emails
    count = db.query(func.count(Email.id))\
              .filter(Email.status == "sent")\
              .filter(Email.sent_at >= today_start)\
              .scalar()
    return count or 0

async def send_emails(
    db: Session,
    limit: Optional[int] = None,
    dry_run: Optional[bool] = None,
    progress_callback = None
) -> Dict[str, Any]:
    """
    Orchestrates sending of approved (or drafted if human review disabled) emails.
    Enforces daily cap limits, suppression checks, throttling, and compliance validation.
    """
    # 1. Enforce compliance configuration check
    verify_compliance_config()

    if dry_run is None:
        dry_run = settings.send.dry_run

    # Determine daily send cap
    daily_cap = settings.send.daily_send_limit
    
    # Determine query statuses based on review settings
    if settings.send.require_human_review:
        target_statuses = ["approved"]
    else:
        target_statuses = ["approved", "draft"]

    # Query candidate emails
    candidates = db.query(Email)\
                   .filter(Email.status.in_(target_statuses))\
                   .join(Lead, Lead.id == Email.lead_id)\
                   .filter(Lead.status.in_(["approved", "drafted"]))\
                   .all()

    if not candidates:
        logger.info("No emails found that are ready for sending.")
        return {"total": 0, "sent": 0, "suppressed": 0, "failed": 0, "cap_hit": False}

    # Initialize sender
    sender = GmailSender()

    stats = {"total": len(candidates), "sent": 0, "suppressed": 0, "failed": 0, "cap_hit": False}
    
    # Track daily count inside the sending loop
    sent_today = get_daily_sent_count(db)
    total = len(candidates)

    for i, email_row in enumerate(candidates):
        lead = email_row.lead
        
        # A. Check daily send limit
        if sent_today >= daily_cap:
            logger.warning(
                "Daily sending cap limit hit. Stopping send pipeline.",
                sent_today=sent_today,
                daily_cap=daily_cap
            )
            stats["cap_hit"] = True
            break

        # Apply limit if passed via CLI
        if limit is not None and stats["sent"] >= limit:
            logger.info("Limit specified by user reached. Stopping.", limit=limit)
            break

        # B. Real-time suppression list check
        is_suppressed = db.query(Suppression).filter(Suppression.email == lead.email).first() is not None
        if is_suppressed:
            logger.warning("Lead is on the suppression list. Skipping send.", email=lead.email, lead_id=lead.id)
            lead.status = "suppressed"
            email_row.status = "failed"
            email_row.reject_reason = "Suppressed: recipient is on the suppression list"
            db.commit()
            stats["suppressed"] += 1
            if progress_callback:
                await progress_callback(i + 1, total)
            continue

        # C. Send email
        logger.info(
            "Sending email...",
            lead_id=lead.id,
            to=lead.email,
            dry_run=dry_run
        )
        
        try:
            if dry_run:
                # Dry run: log and simulate success
                msg_id = f"dryrun-msg-{lead.id}-{int(time.time())}"
                logger.info("[Dry Run] Simulating email send", to=lead.email, subject=email_row.subject)
            else:
                # Real run: call sender integration
                msg_id = sender.send_email(
                    to_email=lead.email,
                    subject=email_row.subject,
                    body=email_row.body
                )

            # Update DB state
            email_row.status = "sent"
            email_row.sent_at = datetime.utcnow()
            email_row.gmail_message_id = msg_id
            lead.status = "sent"
            lead.error_message = None

            # Record event
            event = Event(
                lead_id=lead.id,
                email_id=email_row.id,
                event_type="sent",
                occurred_at=datetime.utcnow(),
                metadata_json={"dry_run": dry_run, "gmail_message_id": msg_id}
            )
            db.add(event)
            db.commit()
            
            stats["sent"] += 1
            sent_today += 1

            # D. Apply per-message throttle delay if there are more emails to process
            if i < len(candidates) - 1 and sent_today < daily_cap:
                delay = settings.send.per_message_delay_s
                if limit is not None and stats["sent"] >= limit:
                    # No need to delay if this was the last limit item
                    pass
                else:
                    logger.info(f"Throttling: sleeping for {delay} seconds before next send...")
                    await asyncio.sleep(delay)

        except Exception as e:
            logger.error("Failed to send email", error=str(e), lead_id=lead.id)
            email_row.status = "failed"
            lead.status = "failed"
            lead.error_message = str(e)
            db.commit()
            stats["failed"] += 1
        finally:
            if progress_callback:
                await progress_callback(i + 1, total)

    return stats
