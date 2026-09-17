"""
NumberGuard — SMTP Email Adapter (Phase 3)
Real SMTP transactional email delivery.
Gated by settings.EMAIL_PROVIDER == "smtp" and valid SMTP credentials.
"""
from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

from app.adapters.base import EmailAdapter
from app.core.config import settings


class SmtpEmailAdapter(EmailAdapter):
    """
    Standard SMTP client adapter for transactional notifications.
    """
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.user = user or settings.SMTP_USER
        self.password = password or settings.SMTP_PASS

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.host or not self.user:
            return {
                "status": "FAILED",
                "error": "SMTP server not configured. Set SMTP_HOST and SMTP_USER.",
                "adapter": "SMTP"
            }

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.user
        msg["To"] = to_email

        part1 = MIMEText(body_text, "plain")
        msg.attach(part1)
        if body_html:
            part2 = MIMEText(body_html, "html")
            msg.attach(part2)

        try:
            # Connect and send
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, [to_email], msg.as_string())
            return {
                "status": "DELIVERED",
                "to": to_email,
                "subject": subject,
                "adapter": "SMTP"
            }
        except Exception as e:
            return {
                "status": "FAILED",
                "error": str(e),
                "adapter": "SMTP"
            }
