"""Custom errors for the Teachworks SDK."""

from __future__ import annotations

from typing import Any


class TeachworksAPIError(RuntimeError):
    """Base API error for Teachworks responses.

    Attributes:
        status_code: HTTP status code returned by the API.
        code: API error code if provided.
        message: Human-readable error message.
        data: Additional error payload data.
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        code: str | None = None,
        data: Any | None = None,
    ) -> None:
        """Initialize the Teachworks API error.

        :param status_code: HTTP status code.
        :type status_code: int
        :param message: Human-readable error message.
        :type message: str
        :param code: Optional error code from Teachworks.
        :type code: str | None
        :param data: Additional error payload data.
        :type data: Any | None
        """
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.data = data


class TeachworksRateLimitError(TeachworksAPIError):
    """Raised when rate limiting persists after retries."""

class TeachworksInvalidPathError(TeachworksAPIError):
    """Raised when a call results in a 404 error."""
    def __init__(
        self,
        status_code: int,
        message: str,
        code: str | None = None,
        data: Any | None = None,
        url: str | None = None,
    ) -> None:
        """Initialize the TeachworksInvalidPathError.

        :param status_code: HTTP status code.
        :type status_code: int
        :param message: Human-readable error message.
        :type message: str
        :param code: Optional error code from Teachworks.
        :type code: str | None
        :param data: Additional error payload data.
        :type data: Any | None
        :param url: The request URL that resulted in the 404
        :type url: str | None
        """
        super().__init__(
            status_code=status_code,
            message=message,
            code=code,
            data=data
        )
        self.url = url
