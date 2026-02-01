from __future__ import annotations

from typing_extensions import Unpack

from ..models.leaderboard import Leaderboard, LeaderboardPlayer
from ..pagination import PaginatedList
from ..types import PaginationParams
from .resource import Resource


class Leaderboards(Resource):
    """
    Resource for leaderboard-related endpoints.

    Check the :clash-royale-api:`leaderboards`
    for more detailed information about each endpoint.
    """

    def list(self) -> list[Leaderboard]:  # ty:ignore[invalid-type-form]
        """List all available leaderboards."""
        response = self._client._request("GET", "/leaderboards")
        items = response.get("items", [])
        return [Leaderboard.model_validate(item) for item in items]

    def get(
        self, leaderboard_id: int, **params: Unpack[PaginationParams]
    ) -> PaginatedList[LeaderboardPlayer]:
        """Get player rankings for a specific leaderboard.

        :param leaderboard_id: The leaderboard ID from the leaderboards list.
        """
        return PaginatedList(
            client=self._client,
            endpoint=f"/leaderboard/{leaderboard_id}",
            model=LeaderboardPlayer,
            params=params,  # ty:ignore[invalid-argument-type]
        )
