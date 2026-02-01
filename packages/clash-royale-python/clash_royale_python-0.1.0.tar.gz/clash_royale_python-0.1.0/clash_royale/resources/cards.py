from __future__ import annotations

from typing_extensions import Unpack

from ..models.card import Card
from ..pagination import PaginatedList
from ..types import PaginationParams
from .resource import Resource


class Cards(Resource):
    """
    Resource for card-related endpoints.

    Check the :clash-royale-api:`cards`
    for more detailed information about each endpoint.
    """

    def list(self, **params: Unpack[PaginationParams]) -> PaginatedList[Card]:
        """List all available cards."""
        return PaginatedList(
            client=self._client,
            endpoint="/cards",
            model=Card,
            params=params,  # ty:ignore[invalid-argument-type]
        )
