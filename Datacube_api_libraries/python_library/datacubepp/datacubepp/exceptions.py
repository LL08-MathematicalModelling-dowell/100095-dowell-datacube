"""
This module defines custom exception classes for handling various errors in the package.
Classes:
    MyPackageError(Exception): Base exception for all errors in the package.
    APIError(MyPackageError): General exception for API errors.
        - from_response(cls, response: dict, status_code: int): Creates an APIError 
            from an API response.
    AuthenticationError(APIError): Raised when there is an authentication failure.
    ValidationError(MyPackageError): Raised when input validation fails.
    ResourceNotFoundError(APIError): Raised when a requested resource is not found.
    ServerError(APIError): Raised when the server encounters an error.
    TimeoutError(APIError): Raised when a request times out.
    RateLimitError(APIError): Raised when the rate limit for the API is exceeded.
Functions:
    map_status_code_to_exception(status_code: int, response: dict) -> APIError:
"""

from typing import Optional


class MyPackageError(Exception):
    """
    Base exception for all errors in the package.
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class APIError(MyPackageError):
    """
    General exception for API errors.
    """
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details

    @classmethod
    def from_response(cls, response: dict, status_code: int):
        """
        Creates an APIError from an API response.
        """
        message = response.get("message", "An unknown API error occurred.")
        details = response.get("details", {})
        return cls(message=message, status_code=status_code, details=details)


class AuthenticationError(APIError):
    """
    Raised when there is an authentication failure.
    """
    def __init__(self, message: str = "Authentication failed. Check your API key.", status_code: Optional[int] = 401):
        super().__init__(message, status_code)


class ValidationError(MyPackageError):
    """
    Raised when input validation fails.
    """
    def __init__(self, message: str):
        super().__init__(message)


class ResourceNotFoundError(APIError):
    """
    Raised when a requested resource is not found.
    """
    def __init__(self, message: str = "Requested resource not found.", status_code: Optional[int] = 404):
        super().__init__(message, status_code)


class ServerError(APIError):
    """
    Raised when the server encounters an error.
    """
    def __init__(self, message: str = "An error occurred on the server.", status_code: Optional[int] = 500):
        super().__init__(message, status_code)


class TimeoutError(APIError):
    """
    Raised when a request times out.
    """
    def __init__(self, message: str = "The request timed out.", status_code: Optional[int] = 408):
        super().__init__(message, status_code)


class RateLimitError(APIError):
    """
    Raised when the rate limit for the API is exceeded.
    """
    def __init__(self, message: str = "Rate limit exceeded.", status_code: Optional[int] = 429):
        super().__init__(message, status_code)


# Exception mapping function
def map_status_code_to_exception(status_code: int, response: dict) -> APIError:
    """
    Map an HTTP status code to a specific exception.

    Args:
        status_code (int): The HTTP status code.
        response (dict): The API response payload.

    Returns:
        APIError: The appropriate exception class instance.
    """
    if status_code == 401:
        return AuthenticationError(response.get("message", "Authentication failed."))
    elif status_code == 404:
        return ResourceNotFoundError(response.get("message", "Resource not found."))
    elif status_code == 408:
        return TimeoutError(response.get("message", "Request timed out."))
    elif status_code == 429:
        return RateLimitError(response.get("message", "Rate limit exceeded."))
    elif 500 <= status_code < 600:
        return ServerError(response.get("message", "Server error occurred."))
    else:
        return APIError.from_response(response, status_code)
