from __future__ import annotations


class SpinDynamicsError(Exception):
    """Base exception for all SpinDynamics errors."""


class APIError(SpinDynamicsError):
    """An error returned by the SpinDynamics API."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id


class AuthenticationError(APIError):
    """Raised when API authentication fails (HTTP 401)."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, status_code=401, error_code=error_code, request_id=request_id
        )


class RateLimitError(APIError):
    """Raised when the API rate limit is exceeded (HTTP 429)."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message, status_code=429, error_code=error_code, request_id=request_id
        )
