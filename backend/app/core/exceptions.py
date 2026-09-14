"""
Centralized application exceptions.

All domain-level errors should raise one of these instead of raw
HTTPException, so the global exception handler (see app/main.py) can turn
them into a consistent { success, error: { code, message } } response
without leaking internals.
"""
from fastapi import status


class AppError(Exception):
    """Base class for all handled application errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "APP_ERROR"

    def __init__(self, message: str, code: str | None = None, status_code: int | None = None):
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"

    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(message, code=code, status_code=status.HTTP_404_NOT_FOUND)


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "VALIDATION_ERROR"

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, code="VALIDATION_ERROR", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, code="UNAUTHORIZED", status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"

    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(message, code="FORBIDDEN", status_code=status.HTTP_403_FORBIDDEN)


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, code="CONFLICT", status_code=status.HTTP_409_CONFLICT)


class FileUploadError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "FILE_UPLOAD_ERROR"

    def __init__(self, message: str = "Invalid file upload"):
        super().__init__(message, code="FILE_UPLOAD_ERROR", status_code=status.HTTP_400_BAD_REQUEST)


class RateLimitError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "RATE_LIMITED"

    def __init__(self, message: str = "Too many requests"):
        super().__init__(message, code="RATE_LIMITED", status_code=status.HTTP_429_TOO_MANY_REQUESTS)
