import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from src.config import settings
from src.integrations.sender_base import EmailSender
from src.utils.logging import logger

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

class GmailSender(EmailSender):
    """
    Gmail sending client using the Google OAuth2 and Gmail API.
    If credentials files are missing, it falls back to mock logging behavior.
    """
    def __init__(self):
        self.creds = None
        self.service = None
        self._authenticate()

    def _authenticate(self):
        token_path = settings.gmail_token_path
        creds_path = settings.gmail_oauth_credentials
        
        # Ensure directories exist
        token_dir = os.path.dirname(token_path)
        if token_dir:
            os.makedirs(token_dir, exist_ok=True)

        if os.path.exists(token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                logger.error("Failed to load authorized user file, re-authenticating", error=str(e))
                self.creds = None
            
        # Let user authenticate if invalid
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    logger.error("Failed to refresh Gmail OAuth token, re-authenticating", error=str(e))
                    self.creds = None
                    
            if not self.creds:
                if not os.path.exists(creds_path):
                    logger.warning(
                        "Google Cloud OAuth credentials JSON file not found. "
                        "Sending will operate in simulator mode.",
                        expected_path=creds_path
                    )
                    return
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error("Exception during OAuth authentication flow", error=str(e))
                    return
                
            # Save credentials
            with open(token_path, "w") as token:
                token.write(self.creds.to_json())
                
        if self.creds:
            try:
                self.service = build("gmail", "v1", credentials=self.creds)
            except Exception as e:
                logger.error("Failed to build Gmail service client", error=str(e))

    def send_email(self, to_email: str, subject: str, body: str) -> str:
        if not self.service:
            # Act as a simulator if not fully authenticated
            logger.info(
                "[Gmail Simulator] Sending email...",
                to=to_email,
                subject=subject,
                body_preview=body[:100] + "..."
            )
            return "mock-gmail-message-id"
            
        try:
            message = MIMEText(body)
            message["to"] = to_email
            message["subject"] = subject
            
            # Base64url encode
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            
            sent_msg = self.service.users().messages().send(
                userId="me",
                body={"raw": raw_message}
            ).execute()
            
            msg_id = sent_msg.get("id", "gmail-sent-id")
            logger.info("Email successfully sent via Gmail API", to=to_email, message_id=msg_id)
            return msg_id
        except Exception as e:
            logger.error("Failed to send email via Gmail API", error=str(e), to=to_email)
            raise e
