from __future__ import annotations

from typing_extensions import Unpack

from clash_royale.models import TournamentHeader

from ..models.tournament import Tournament
from ..pagination import PaginatedList
from ..types import PaginationParams
from .resource import Resource


class Tournaments(Resource):
    """
    Resource for tournament-related endpoints.

    Check the :clash-royale-api:`tournaments`
    for more detailed information about each endpoint.
    """

    def get(self, tag: str) -> Tournament:
        """Get tournament information by tag."""
        encoded_tag = self._encode_tag(tag)
        response = self._client._request("GET", f"/tournaments/{encoded_tag}")
        return Tournament.model_validate(response)

    def search(
        self, name: str, **params: Unpack[PaginationParams]
    ) -> PaginatedList[TournamentHeader]:
        """Search tournaments by name."""
        api_params = {"name": name, **params}

        return PaginatedList(
            client=self._client,
            endpoint="/tournaments",
            model=TournamentHeader,
            params=api_params,  # ty:ignore[invalid-argument-type]
        )
