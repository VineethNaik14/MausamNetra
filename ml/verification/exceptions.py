"""Custom exception hierarchy for the verification engine.

Keeping exceptions specific (rather than raising bare ``Exception``) lets
the API layer translate failures into clean HTTP responses without ever
leaking stack traces to clients.
"""


class VerificationError(Exception):
    """Base class for all verification-engine errors."""


class InvalidReportError(VerificationError):
    """Raised when a report fails validation or is structurally unusable."""


class ClassifierUnavailableError(VerificationError):
    """Raised when the event-classification dependency cannot be reached."""


class ClassifierTimeoutError(ClassifierUnavailableError):
    """Raised when an HTTP/local classifier call exceeds its timeout."""


class ImageProcessingError(VerificationError):
    """Raised when an image cannot be safely loaded/processed."""


class UnsupportedMediaError(ImageProcessingError):
    """Raised when media fails type/size/security validation."""


class ConfigurationError(VerificationError):
    """Raised when configuration is missing or inconsistent."""
