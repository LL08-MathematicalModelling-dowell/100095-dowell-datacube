"""Application roles for RBAC."""

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_DEVELOPER = "developer"

ROLES = (ROLE_ADMIN, ROLE_ANALYST, ROLE_DEVELOPER)
DEFAULT_ROLE = ROLE_DEVELOPER


def normalize_role(value: str | None) -> str:
    if not value:
        return DEFAULT_ROLE
    v = value.lower().strip()
    if v in ("user", "developer", "dev"):
        return ROLE_DEVELOPER
    if v == ROLE_ANALYST:
        return ROLE_ANALYST
    if v == ROLE_ADMIN:
        return ROLE_ADMIN
    return DEFAULT_ROLE
