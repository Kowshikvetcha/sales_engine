import sys
from datetime import datetime
from sqlalchemy.orm import Session
from src.db import Lead, Email
from src.core.generate import append_compliance_footer
from src.utils.logging import logger

def interactive_review_loop(db: Session) -> dict:
    """
    Finds leads with status 'drafted' and steps through them interactively in the console.
    Allows user to Approve [A], Reject [R], Edit [E], Skip [S], or Quit [Q].
    """
    leads = db.query(Lead).filter(Lead.status == "drafted").all()
    if not leads:
        print("No drafts to review.")
        return {"total": 0, "approved": 0, "rejected": 0, "skipped": 0}

    stats = {"total": len(leads), "approved": 0, "rejected": 0, "skipped": 0}
    print(f"Found {len(leads)} drafts to review. Starting queue...\n")

    for lead in leads:
        # Find the draft email for this lead
        email_row = db.query(Email).filter(Email.lead_id == lead.id, Email.status == "draft").first()
        if not email_row:
            print(f"Warning: Lead {lead.id} is in drafted status but has no draft Email row. Skipping.")
            continue

        print("=" * 60)
        print(f"LEAD ID: {lead.id} | Business: {lead.name or lead.domain}")
        print(f"Website: {lead.website_url} | Email: {lead.email}")
        
        # Display screenshot info if available
        if lead.scrape and lead.scrape.screenshot_path:
            print(f"Screenshot Path: {lead.scrape.screenshot_path}")
        else:
            print("Screenshot Path: None")

        # Display service mapping / findings
        print("\n--- Mapped Findings ---")
        if lead.analysis and lead.analysis.service_map:
            for service, details in lead.analysis.service_map.items():
                print(f"- [{service.upper()}] {details.get('evidence', '')}")
        else:
            print("(No findings mapped)")

        print("\n--- Current Email Draft ---")
        print(f"Subject: {email_row.subject}")
        print(f"Body:\n{email_row.body}")
        print("-" * 60)

        while True:
            choice = input("Action [A]pprove, [R]eject, [E]dit, [S]kip, [Q]uit: ").strip().upper()
            if choice == "A":
                # Approve email
                email_row.status = "approved"
                email_row.approved_at = datetime.utcnow()
                lead.status = "approved"
                lead.error_message = None
                db.commit()
                print(f"Lead {lead.id} email approved.")
                stats["approved"] += 1
                break

            elif choice == "R":
                # Reject email
                reason = input("Enter rejection reason (optional): ").strip()
                email_row.status = "rejected"
                email_row.reject_reason = reason if reason else None
                lead.status = "rejected"
                db.commit()
                print(f"Lead {lead.id} email rejected.")
                stats["rejected"] += 1
                break

            elif choice == "E":
                # Edit email
                print("\n--- Editing Email Draft ---")
                new_subject = input(f"New Subject (press Enter to keep current: '{email_row.subject}'): ").strip()
                if new_subject:
                    email_row.subject = new_subject
                
                print("Enter new Body (type 'EOF' on a single line to finish, or press Enter to keep current):")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "EOF":
                        break
                    lines.append(line)
                
                new_body_raw = "\n".join(lines).strip()
                if new_body_raw:
                    # Append compliance footer to the newly edited body
                    email_row.body = append_compliance_footer(new_body_raw, lead.email)
                
                db.commit()
                print("\nDraft updated. Displaying updated draft:")
                print(f"Subject: {email_row.subject}")
                print(f"Body:\n{email_row.body}")
                print("-" * 60)
                # Keep loop running so they can approve/reject/edit the updated draft

            elif choice == "S":
                print(f"Skipping Lead {lead.id}.")
                stats["skipped"] += 1
                break

            elif choice == "Q":
                print("Exiting review queue.")
                return stats
            else:
                print("Invalid input. Please choose A, R, E, S, or Q.")

    print("\nReview queue complete.")
    return stats
