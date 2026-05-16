"""Transactional email via Resend (https://resend.com)."""

from __future__ import annotations

import logging
import os
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


def _from_address() -> str:
    return getattr(settings, "RESEND_FROM_EMAIL", os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev"))


def send_email(*, to: str, subject: str, html: str, text: Optional[str] = None) -> dict:
    """
    Send one email. Returns Resend JSON on success.
    If RESEND_API_KEY is missing, logs only (local dev) and returns {"simulated": True}.
    """
    api_key = getattr(settings, "RESEND_API_KEY", None) or os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY not set; email to %s skipped. Subject: %s", to, subject)
        if text:
            logger.debug("Email text:\n%s", text)
        return {"simulated": True, "to": to, "subject": subject}

    payload = {
        "from": _from_address(),
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    resp = requests.post(
        RESEND_API_URL,
        json=payload,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    if not resp.ok:
        logger.error("Resend error %s: %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()


def send_otp_email(*, to: str, code: str, purpose: str) -> dict:
    """Send a one-time passcode (login or signup verification)."""
    if purpose == "register":
        subject = "Your verification code"
        intro = "Use this code to verify your email and activate your account:"
    elif purpose == "login_email":
        subject = "Your sign-in code"
        intro = "Use this code to sign in:"
    elif purpose == "reset_password":
        subject = "Your password reset code"
        intro = "Use this code to reset your password:"
    else:
        subject = "Your verification code"
        intro = "Your one-time code:"
    html = f"<p>{intro}</p><p style=\"font-size:24px;font-weight:700;letter-spacing:4px\">{code}</p>"
    text = f"{intro} {code}"
    return send_email(to=to, subject=subject, html=html, text=text)
