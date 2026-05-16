"""Rules for who may authenticate (verification + account status)."""


def effective_email_verified(user_doc: dict | None) -> bool:
    if not user_doc or user_doc.get("deleted_at"):
        return False
    # Grandfather: documents created before strict verification omit the flag
    if "is_email_verified" not in user_doc:
        return True
    return bool(user_doc.get("is_email_verified"))


def is_account_deleted(user_doc: dict | None) -> bool:
    return bool(user_doc and user_doc.get("deleted_at"))
