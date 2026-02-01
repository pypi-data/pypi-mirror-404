from __future__ import annotations

from ..models.player import Battle, Player, UpcomingChest
from .resource import Resource


class Players(Resource):
    """
    Resource for player-related endpoints.

    Check the :clash-royale-api:`players`
    for more detailed information about each endpoint.
    """

    def get(self, tag: str) -> Player:
        """Get player information by tag."""
        encoded_tag = self._encode_tag(tag)
        response = self._client._request("GET", f"/players/{encoded_tag}")
        return Player.model_validate(response)

    def get_battlelog(self, tag: str) -> list[Battle]:
        """Get player's battle log."""
        encoded_tag = self._encode_tag(tag)
        response = self._client._request("GET", f"/players/{encoded_tag}/battlelog")
        return [Battle.model_validate(battle) for battle in response]

    def get_upcoming_chests(self, tag: str) -> list[UpcomingChest]:
        """Get player's upcoming chests."""
        encoded_tag = self._encode_tag(tag)
        response = self._client._request(
            "GET", f"/players/{encoded_tag}/upcomingchests"
        )
        return [
            UpcomingChest.model_validate(upcoming_chest)
            for upcoming_chest in response["items"]
        ]
