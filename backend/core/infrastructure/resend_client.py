"""Transactional email via Resend (https://resend.com)."""

from __future__ import annotations

import html
import logging
import os

import resend
from django.conf import settings

logger = logging.getLogger(__name__)

_PURPOSE_SUBJECTS: dict[str, str] = {
    "register": "Verify your email",
    "login_email": "Your sign-in code",
    "reset_password": "Your password reset code",
}

_PURPOSE_INTROS: dict[str, str] = {
    "register": (
        "Welcome to DataCube! Use the code below to verify your email and finish creating your account."
    ),
    "login_email": "Use the code below to sign in to your DataCube account.",
    "reset_password": "Use the code below to reset your DataCube password.",
}


class ResendDeliveryError(Exception):
    """Resend API rejected the send or the server is misconfigured."""


def _mask_email(email: str) -> str:
    if "@" in email:
        local, domain = email.split("@", 1)
        return f"{local[:2]}***@{domain}"
    return "***"


def _resend_api_key() -> str:
    return (getattr(settings, "RESEND_API_KEY", None) or os.getenv("RESEND_API_KEY", "") or "").strip()


def _from_address() -> str:
    email = (
        getattr(settings, "RESEND_FROM_EMAIL", None)
        or os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        or ""
    ).strip()
    if not email:
        raise ResendDeliveryError("RESEND_FROM_EMAIL is not set.")
    name = (getattr(settings, "RESEND_FROM_NAME", None) or os.getenv("RESEND_FROM_NAME", "") or "").strip()
    return f"{name} <{email}>" if name else email


def _otp_expires_minutes() -> int:
    return int(getattr(settings, "OTP_EXPIRES_MINUTES", 10))


def _allow_stdout_email() -> bool:
    if getattr(settings, "ALLOW_STDOUT_EMAIL", False):
        return True
    return os.getenv("ALLOW_STDOUT_EMAIL", "").lower() in ("1", "true", "yes")


def _render_html(*, first_name: str, code: str, purpose: str, expires_minutes: int) -> str:
    intro = _PURPOSE_INTROS.get(purpose, "Your one-time code:")
    safe_first_name = html.escape(first_name, quote=True)
    safe_code = html.escape(code, quote=True)
    return f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto;">
  <h2 style="color: #111;">Hi {safe_first_name},</h2>
  <p style="color: #333; line-height: 1.5;">{intro}</p>
  <div style="font-size: 32px; font-weight: 700; letter-spacing: 8px; padding: 16px 24px; background: #f4f6fb; border-radius: 8px; text-align: center; color: #111;">
    {safe_code}
  </div>
  <p style="color: #666; font-size: 14px; margin-top: 16px;">
    This code expires in {expires_minutes} minutes. If you didn't request it, you can safely ignore this email.
  </p>
</div>
""".strip()


def _render_text(*, first_name: str, code: str, purpose: str, expires_minutes: int) -> str:
    intro = _PURPOSE_INTROS.get(purpose, "Your one-time code:")
    return (
        f"Hi {first_name},\n\n"
        f"{intro}\n\n"
        f"Your code: {code}\n\n"
        f"This code expires in {expires_minutes} minutes. "
        "If you didn't request it, you can ignore this email."
    )


def send_otp_email(
    *,
    to_email: str,
    first_name: str,
    code: str,
    purpose: str,
) -> None:
    """Send the OTP via Resend (or log to stdout when RESEND_API_KEY is unset)."""
    expires_minutes = _otp_expires_minutes()
    subject = _PURPOSE_SUBJECTS.get(purpose, "Your verification code")
    html_body = _render_html(
        first_name=first_name,
        code=code,
        purpose=purpose,
        expires_minutes=expires_minutes,
    )
    text_body = _render_text(
        first_name=first_name,
        code=code,
        purpose=purpose,
        expires_minutes=expires_minutes,
    )

    api_key = _resend_api_key()
    if not api_key:
        if _allow_stdout_email():
            logger.info(
                "STDOUT EMAIL [OTP] -> to: %s, purpose: %s, code: %s",
                _mask_email(to_email),
                purpose,
                code,
            )
            return
        raise ResendDeliveryError(
            "RESEND_API_KEY is not set. Set it in backend/.env or enable ALLOW_STDOUT_EMAIL=true."
        )

    resend.api_key = api_key
    try:
        resend.Emails.send(
            {
                "from": _from_address(),
                "to": [to_email],
                "subject": subject,
                "text": text_body,
                "html": html_body,
            }
        )
    except Exception as exc:
        logger.exception(
            "Failed to send OTP email to %s (purpose=%s)",
            _mask_email(to_email),
            purpose,
        )
        raise ResendDeliveryError(str(exc)) from exc
