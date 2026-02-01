from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from ..types import ClanSearchParams, PaginationParams

if TYPE_CHECKING:
    from ..client import Client

# Re-export for backward compatibility
__all__ = ["Resource", "PaginationParams", "ClanSearchParams"]


class Resource:
    """Base class for all API resources."""

    def __init__(self, client: Client):
        """Initialize the resource with a client."""
        self._client = client

    def _encode_tag(self, tag: str) -> str:
        """Encode a Clash Royale tag for use in URLs."""
        tag = self._normalize_tag(tag)
        return quote(tag, safe="")

    def _normalize_tag(self, tag: str) -> str:
        """Normalize a Clash Royale tag by ensuring it starts with '#' and is uppercase."""
        if not tag.startswith("#"):
            tag = f"#{tag}"
        return tag.upper()
