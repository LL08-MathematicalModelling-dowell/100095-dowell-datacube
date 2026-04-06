import hmac
import hashlib
import time

from django.conf import settings


def generate_signed_url(
    file_id: str,
    user_id: str,
    expires_in_seconds: int = 300, # Default to 5 minutes
    path_prefix: str = "/api/v2/files/stream/"
) -> str:
    """
    Generate a signed URL for a file that expires after a given time.
    :param file_id: The GridFS file ID (as string)
    :param user_id: The user's ID (must match the owner)
    :param expires_in_seconds: URL validity duration (default 5 minutes)
    :param path_prefix: API endpoint path (adjust as needed)
    :return: Full signed URL (relative path, without domain)
    """
    expire_at = int(time.time()) + expires_in_seconds
    message = f"{file_id}:{user_id}:{expire_at}"
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"{path_prefix}{file_id}?expires={expire_at}&sig={signature}"

def verify_signed_url(file_id: str, user_id: str, expires: int, signature: str) -> bool:
    """
    Verify that a signed URL is valid and not expired.
    """
    # Check expiration
    current_time = int(time.time())
    if current_time > expires:
        return False
    
    # Recompute signature
    message = f"{file_id}:{user_id}:{expires}"
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, signature)