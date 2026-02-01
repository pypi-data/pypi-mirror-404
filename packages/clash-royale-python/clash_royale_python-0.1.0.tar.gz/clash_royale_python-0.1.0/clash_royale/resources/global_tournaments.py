from __future__ import annotations

from typing_extensions import Unpack

from ..models.global_tournament import GlobalTournament
from ..pagination import PaginatedList
from ..types import PaginationParams
from .resource import Resource


class GlobalTournaments(Resource):
    """
    Resource for global tournament related endpoints.

    Check the :clash-royale-api:`globaltournaments`
    for more detailed information about each endpoint.
    """

    def list(
        self, **params: Unpack[PaginationParams]
    ) -> PaginatedList[GlobalTournament]:
        """Get list of global tournaments."""
        return PaginatedList(
            client=self._client,
            endpoint="/globaltournaments",
            model=GlobalTournament,
            params=params,  # ty:ignore[invalid-argument-type]
        )
