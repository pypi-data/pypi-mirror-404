from __future__ import annotations

from typing_extensions import Unpack

from ..models.clan import Clan, ClanMember, ClanSearchResult, RiverRace, RiverRaceLog
from ..pagination import PaginatedList
from ..types import ClanSearchParams, PaginationParams
from .resource import Resource


class Clans(Resource):
    """
    Resource for clan-related endpoints.

    Check the :clash-royale-api:`clans`
    for more detailed information about each endpoint.
    """

    def get(self, tag: str) -> Clan:
        """Get clan information by tag."""
        encoded_tag = self._encode_tag(tag)
        response = self._client._request("GET", f"/clans/{encoded_tag}")
        return Clan.model_validate(response)

    def search(
        self, name: str, **params: Unpack[ClanSearchParams]
    ) -> PaginatedList[ClanSearchResult]:
        """Search clans by name."""
        api_params = {"name": name, **params}

        return PaginatedList(
            client=self._client,
            endpoint="/clans",
            model=ClanSearchResult,
            params=api_params,  # ty:ignore[invalid-argument-type]
        )

    def get_members(
        self, tag: str, **params: Unpack[PaginationParams]
    ) -> PaginatedList[ClanMember]:
        """Get clan members."""
        encoded_tag = self._encode_tag(tag)
        return PaginatedList(
            client=self._client,
            endpoint=f"/clans/{encoded_tag}/members",
            model=ClanMember,
            params=params,  # ty:ignore[invalid-argument-type]
        )

    def get_current_river_race(self, tag: str) -> RiverRace:
        """Get current river race information for a clan."""
        encoded_tag = self._encode_tag(tag)
        response = self._client._request(
            "GET", f"/clans/{encoded_tag}/currentriverrace"
        )
        return RiverRace.model_validate(response)

    def get_river_race_log(
        self, tag: str, **params: Unpack[PaginationParams]
    ) -> PaginatedList[RiverRaceLog]:
        """Get river race log for a clan."""
        encoded_tag = self._encode_tag(tag)
        return PaginatedList(
            client=self._client,
            endpoint=f"/clans/{encoded_tag}/riverracelog",
            model=RiverRaceLog,
            params=params,  # ty:ignore[invalid-argument-type]
        )
