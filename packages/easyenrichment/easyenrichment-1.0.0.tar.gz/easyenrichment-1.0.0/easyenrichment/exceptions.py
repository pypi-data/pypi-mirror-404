"""Exception classes for Easy Enrichment API."""


class EasyEnrichmentError(Exception):
    """Base exception for Easy Enrichment API errors.

    Attributes:
        message: Human-readable error message.
        code: Machine-readable error code string (e.g., 'INVALID_API_KEY').
        status: HTTP status code from the API response.
    """

    def __init__(self, message: str, code: str = None, status: int = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"code={self.code}")
        if self.status:
            parts.append(f"status={self.status}")
        return " | ".join(parts)

    def __repr__(self) -> str:
        return (
            f"EasyEnrichmentError(message={self.message!r}, "
            f"code={self.code!r}, status={self.status!r})"
        )
