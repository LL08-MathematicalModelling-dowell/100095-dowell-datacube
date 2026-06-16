"""Transactional email via Django SMTP (Gmail and other providers)."""

from __future__ import annotations

import logging
import os

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

_PURPOSE_SUBJECTS: dict[str, str] = {
    "register": "Verify your DataCube email",
    "login_email": "Your DataCube sign-in code",
    "reset_password": "Reset your DataCube password",
}

_PURPOSE_INTROS: dict[str, str] = {
    "register": (
        "Welcome to DataCube! Enter the verification code below to confirm your email "
        "and finish setting up your account."
    ),
    "login_email": "Enter the code below to sign in to your DataCube account.",
    "reset_password": "Enter the code below to reset your DataCube password.",
}


class EmailDeliveryError(Exception):
    """SMTP send failed or email is misconfigured."""


# Backward-compatible alias for any external imports
ResendDeliveryError = EmailDeliveryError


def _mask_email(email: str) -> str:
    if "@" in email:
        local, domain = email.split("@", 1)
        return f"{local[:2]}***@{domain}"
    return "***"


def _smtp_configured() -> bool:
    user = (getattr(settings, "EMAIL_HOST_USER", None) or "").strip()
    password = (getattr(settings, "EMAIL_HOST_PASSWORD", None) or "").strip()
    return bool(user and password)


def _from_address() -> str:
    email = (
        getattr(settings, "DEFAULT_FROM_EMAIL", None)
        or os.getenv("DEFAULT_FROM_EMAIL", "")
        or getattr(settings, "EMAIL_HOST_USER", "")
        or ""
    ).strip()
    if not email:
        raise EmailDeliveryError("DEFAULT_FROM_EMAIL or EMAIL_HOST_USER is not set.")
    name = (getattr(settings, "EMAIL_FROM_NAME", None) or os.getenv("EMAIL_FROM_NAME", "") or "").strip()
    return f"{name} <{email}>" if name else email


def _otp_expires_minutes() -> int:
    return int(getattr(settings, "OTP_EXPIRES_MINUTES", 10))


def _allow_stdout_email() -> bool:
    if getattr(settings, "ALLOW_STDOUT_EMAIL", False):
        return True
    return os.getenv("ALLOW_STDOUT_EMAIL", "").lower() in ("1", "true", "yes")


def _render_text(*, first_name: str, code: str, purpose: str, expires_minutes: int) -> str:
    intro = _PURPOSE_INTROS.get(purpose, "Your one-time code:")
    return (
        f"Hi {first_name},\n\n"
        f"{intro}\n\n"
        f"Your code: {code}\n\n"
        f"This code expires in {expires_minutes} minutes. "
        "If you didn't request it, you can ignore this email.\n\n"
        "— DataCube"
    )


def send_otp_email(
    *,
    to_email: str,
    first_name: str,
    code: str,
    purpose: str,
) -> None:
    """Send OTP via SMTP (or log to stdout when SMTP is unset and ALLOW_STDOUT_EMAIL=true)."""
    expires_minutes = _otp_expires_minutes()
    subject = _PURPOSE_SUBJECTS.get(purpose, "Your DataCube verification code")
    intro = _PURPOSE_INTROS.get(purpose, "Your one-time code:")

    text_body = _render_text(
        first_name=first_name,
        code=code,
        purpose=purpose,
        expires_minutes=expires_minutes,
    )
    html_body = render_to_string(
        "emails/otp.html",
        {
            "subject": subject,
            "first_name": first_name,
            "code": code,
            "intro": intro,
            "expires_minutes": expires_minutes,
        },
    )

    if not _smtp_configured():
        if _allow_stdout_email():
            logger.info(
                "STDOUT EMAIL [OTP] -> to: %s, purpose: %s, code: %s",
                _mask_email(to_email),
                purpose,
                code,
            )
            return
        raise EmailDeliveryError(
            "EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are not set. "
            "Configure Gmail SMTP in .env or enable ALLOW_STDOUT_EMAIL=true."
        )

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=_from_address(),
            to=[to_email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send(fail_silently=False)
    except Exception as exc:
        logger.exception(
            "Failed to send OTP email to %s (purpose=%s)",
            _mask_email(to_email),
            purpose,
        )
        raise EmailDeliveryError(str(exc)) from exc
