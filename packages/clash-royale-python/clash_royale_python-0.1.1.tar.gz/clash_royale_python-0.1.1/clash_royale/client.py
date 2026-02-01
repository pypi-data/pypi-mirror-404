from __future__ import annotations

import httpx

from .auth import CRAuth
from .exceptions import ClashRoyaleHTTPError
from .resources import (
    Cards,
    Clans,
    GlobalTournaments,
    Leaderboards,
    Locations,
    Players,
    Tournaments,
)

CURRENT_VERSION = "v1"
BASE_URL = f"https://api.clashroyale.com/{CURRENT_VERSION}"


class Client(httpx.Client):
    """
    A client to retrieve data from the Clash Royale API.

    Create a client instance with the given options.

        >>> import clash_royale
        >>> client = clash_royale.Client(api_key="your_api_key_here")

    This client provides several methods to retrieve the content most
    kinds of Clash Royale objects, based on their json structure.

    If your server does not have a static IP address, you can use a proxy server by setting the `proxy` parameter.

        >>> client = clash_royale.Client(
                api_key="your_api_key_here",
                proxy="https://my.proxy.com",
            )

    For more detail about proxy usage, check the usage section of the documentation.

    :param api_key: The Clash Royale API key.
    :param proxy: Proxy URL (default: None).
    :param timeout: Request timeout in seconds (default: 10.0).
    :param base_url: Base URL for the API (default: https://api.clashroyale.com/v1).
    """

    players: Players
    clans: Clans
    cards: Cards
    tournaments: Tournaments
    leaderboards: Leaderboards
    locations: Locations
    global_tournaments: GlobalTournaments
    _auth: CRAuth

    def __init__(
        self,
        api_key: str,
        proxy: str | None = None,
        timeout: float = 10.0,
        base_url: str = BASE_URL,
    ):
        self._auth = CRAuth(api_key)

        if proxy:
            # Ensure proxy URL has the version suffix
            if not proxy.endswith(CURRENT_VERSION):
                base_url = proxy.rstrip("/") + "/" + CURRENT_VERSION
            else:
                base_url = proxy

        super().__init__(
            base_url=base_url,
            auth=self._auth,
            timeout=timeout,
        )

        self.players = Players(self)
        self.clans = Clans(self)
        self.cards = Cards(self)
        self.tournaments = Tournaments(self)
        self.leaderboards = Leaderboards(self)
        self.locations = Locations(self)
        self.global_tournaments = GlobalTournaments(self)

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, str | int] | None = None,
    ) -> dict:
        """Make an HTTP request to the API.

        :param method: HTTP method (GET, POST, etc.).
        :param endpoint: API endpoint (e.g., /players/{tag}).
        :param params: Query parameters.

        :returns: The JSON response as a dictionary.

        :raises ClashRoyaleNotFoundError: If resource is not found (404).
        :raises ClashRoyaleUnauthorizedError: If API key is invalid (403).
        :raises ClashRoyaleRateLimitError: If rate limit is exceeded (429).
        :raises ClashRoyaleBadRequestError: If request is malformed (400).
        :raises ClashRoyaleServerError: If server error occurs (5xx).
        :raises ClashRoyaleHTTPError: For other API errors.
        """
        # Convert snake_case parameter names to camelCase for API compatibility
        if params:
            params = self._convert_params_to_camel_case(params)

        try:
            response = super().request(method, endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise ClashRoyaleHTTPError.from_http_error(exc) from exc

    def _convert_params_to_camel_case(
        self, params: dict[str, str | int]
    ) -> dict[str, str | int]:
        """Convert snake_case parameter keys to camelCase for API.

        :param params: Dictionary with snake_case keys.
        :returns: Dictionary with camelCase keys.
        """
        converted = {}
        for key, value in params.items():
            # Convert snake_case to camelCase
            if "_" in key:
                parts = key.split("_")
                camel_key = parts[0] + "".join(word.capitalize() for word in parts[1:])
                converted[camel_key] = value
            else:
                converted[key] = value
        return converted
