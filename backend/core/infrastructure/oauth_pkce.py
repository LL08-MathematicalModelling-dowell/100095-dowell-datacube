"""OAuth2 authorization-code exchange with PKCE (Google + GitHub)."""

from __future__ import annotations

import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


def exchange_google_code(
    *,
    code: str,
    code_verifier: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> dict[str, Any]:
    r = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if not r.ok:
        logger.error("Google token error %s: %s", r.status_code, r.text)
        r.raise_for_status()
    return r.json()


def google_userinfo(access_token: str) -> dict[str, Any]:
    r = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def exchange_github_code(
    *,
    code: str,
    code_verifier: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> dict[str, Any]:
    r = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if not r.ok:
        logger.error("GitHub token error %s: %s", r.status_code, r.text)
        r.raise_for_status()
    return r.json()


def github_primary_email(access_token: str) -> tuple[Optional[str], bool]:
    r = requests.get(
        "https://api.github.com/user/emails",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )
    r.raise_for_status()
    emails = r.json()
    primary_verified = None
    for row in emails:
        if row.get("primary"):
            primary_verified = (row.get("email"), bool(row.get("verified")))
            break
    if primary_verified:
        return primary_verified
    for row in emails:
        if row.get("verified"):
            return row.get("email"), True
    return None, False


def github_profile(access_token: str) -> dict[str, Any]:
    r = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()
