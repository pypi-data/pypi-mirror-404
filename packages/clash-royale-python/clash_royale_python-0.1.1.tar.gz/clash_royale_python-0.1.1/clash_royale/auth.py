from __future__ import annotations

import httpx

from .exceptions import InvalidAPIKeyError


class CRAuth(httpx.Auth):
    """
    Clash Royale Auth for httpx.

    Attaches the API key to the Authorization header of each request.

    :params api_key: Your Clash Royale API key.
    :raises ValueError: If the API key is empty or None.
    """

    def __init__(self, api_key: str):
        if not api_key or (isinstance(api_key, str) and not api_key.strip()):
            raise InvalidAPIKeyError()
        self.api_key = api_key

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.api_key}"
        yield request
