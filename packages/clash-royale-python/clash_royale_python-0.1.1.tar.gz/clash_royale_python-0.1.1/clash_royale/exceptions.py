from __future__ import annotations

import httpx


class ClashRoyaleException(Exception):
    """Base exception for all library errors."""


class ClashRoyaleHTTPError(ClashRoyaleException):
    """API returned an error response."""

    def __init__(self, http_exception: httpx.HTTPStatusError, *args: object) -> None:
        if http_exception.response is not None and http_exception.response.text:
            url = http_exception.response.request.url
            status_code = http_exception.response.status_code
            text = http_exception.response.text
            super().__init__(status_code, url, text, *args)
        else:
            super().__init__(http_exception, *args)

    @classmethod
    def from_http_error(cls, exc: httpx.HTTPStatusError) -> ClashRoyaleHTTPError:
        """Initialize the appropriate internal exception from a HTTPError."""
        if exc.response is not None:
            if exc.response.status_code in {500, 503}:
                return ClashRoyaleServerError(exc)
            if exc.response.status_code == 403:
                return ClashRoyaleUnauthorizedError(exc)
            if exc.response.status_code == 404:
                return ClashRoyaleNotFoundError(exc)
            if exc.response.status_code == 429:
                return ClashRoyaleRateLimitError(exc)
            if exc.response.status_code == 400:
                return ClashRoyaleBadRequestError(exc)
        return ClashRoyaleHTTPError(exc)


class ClashRoyaleNotFoundError(ClashRoyaleHTTPError):
    """Resource was not found (404)."""


class ClashRoyaleUnauthorizedError(ClashRoyaleHTTPError):
    """Access denied, either because of missing/incorrect credentials
    or used API token does not grant access to the requested resource (403).
    """


class ClashRoyaleRateLimitError(ClashRoyaleHTTPError):
    """Request was throttled, because amount of requests was above the
    threshold defined for the used API token (429).
    """


class ClashRoyaleBadRequestError(ClashRoyaleHTTPError):
    """Client provided incorrect parameters for the request (400)."""


class ClashRoyaleServerError(ClashRoyaleHTTPError):
    """Server error (5xx)."""


class InvalidAPIKeyError(ClashRoyaleException):
    """Invalid or missing API key."""

    def __init__(
        self,
        message: str = "API key is required. Please provide a valid Clash Royale API key. You can get one from https://developer.clashroyale.com/#/account/",
    ):
        super().__init__(message)
