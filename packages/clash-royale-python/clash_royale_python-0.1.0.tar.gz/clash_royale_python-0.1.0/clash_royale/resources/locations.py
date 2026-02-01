from __future__ import annotations

import warnings

from typing_extensions import Unpack

from ..models.location import (
    ClanRanking,
    LadderTournamentRanking,
    LeagueSeason,
    LeagueSeasonV2,
    Location,
    PlayerPathOfLegendRanking,
    PlayerRanking,
    PlayerSeasonRanking,
)
from ..pagination import PaginatedList
from ..types import PaginationParams
from .resource import Resource


class Locations(Resource):
    """
    Resource for location-related endpoints.

    Check the :clash-royale-api:`locations`
    for more detailed information about each endpoint.
    """

    def list(self, **params: Unpack[PaginationParams]) -> PaginatedList[Location]:
        """List all available locations."""
        return PaginatedList(
            client=self._client,
            endpoint="/locations",
            model=Location,
            params=params,  # ty:ignore[invalid-argument-type]
        )

    def get(self, location_id: int) -> Location:
        """Get location information by ID.

        :param location_id: The location ID from the locations list.
        """
        response = self._client._request("GET", f"/locations/{location_id}")
        return Location.model_validate(response)

    def get_clan_rankings(
        self,
        location_id: int,
        **params: Unpack[PaginationParams],
    ) -> PaginatedList[ClanRanking]:
        """Get clan rankings for a specific location.

        :param location_id: The location ID from the locations list.
        """
        return PaginatedList(
            client=self._client,
            endpoint=f"/locations/{location_id}/rankings/clans",
            model=ClanRanking,
            params=params,  # ty:ignore[invalid-argument-type]
        )

    def get_player_rankings(
        self,
        location_id: int,
        **params: Unpack[PaginationParams],
    ) -> PaginatedList[PlayerRanking]:
        """Get player rankings for a specific location.

        :param location_id: The location ID from the locations list.
        """
        return PaginatedList(
            client=self._client,
            endpoint=f"/locations/{location_id}/rankings/players",
            model=PlayerRanking,
            params=params,  # ty:ignore[invalid-argument-type]
        )

    def get_clan_war_rankings(
        self,
        location_id: int,
        **params: Unpack[PaginationParams],
    ) -> PaginatedList[ClanRanking]:
        """Get clan war rankings for a specific location.

        :param location_id: The location ID from the locations list.
        """
        return PaginatedList(
            client=self._client,
            endpoint=f"/locations/{location_id}/rankings/clanwars",
            model=ClanRanking,
            params=params,  # ty:ignore[invalid-argument-type]
        )

    def get_path_of_legend_player_rankings(
        self,
        location_id: int,
        **params: Unpack[PaginationParams],
    ) -> PaginatedList[PlayerPathOfLegendRanking]:
        """Get player rankings in Path of Legend for a specific location.

        :param location_id: The location ID from the locations list.
        """
        return PaginatedList(
            client=self._client,
            endpoint=f"/locations/{location_id}/pathoflegend/players",
            model=PlayerPathOfLegendRanking,
            params=params,  # ty:ignore[invalid-argument-type]
        )

    def get_path_of_legend_season_rankings(
        self,
        season_id: str,
        **params: Unpack[PaginationParams],
    ) -> PaginatedList[PlayerPathOfLegendRanking]:
        """Get top Path of Legend players for a given season.

        :param season_id: The season ID (e.g., "2024-01").
        """
        return PaginatedList(
            client=self._client,
            endpoint=f"/locations/global/pathoflegend/{season_id}/rankings/players",
            model=PlayerPathOfLegendRanking,
            params=params,  # ty:ignore[invalid-argument-type]
        )

    def get_season(self, season_id: str) -> LeagueSeason | LeagueSeasonV2:
        """Get top player league season.

        This method automatically selects the appropriate API endpoint based on
        the ``season_id`` format:

        - **Numeric ID** (e.g., ``"1"``, ``"2"``): Uses the V2 endpoint and returns
          :class:`~clash_royale.models.leaderboard.LeagueSeasonV2`.
        - **Date-based code** (e.g., ``"2016-02"``, ``"2025-07"``): Uses the legacy
          endpoint and returns :class:`~clash_royale.models.leaderboard.LeagueSeason`.

        .. warning:: The Clash Royale API may occasionally return incomplete
            season data with null values. This is a known API issue, not a
            library bug.

        :param season_id: Identifier of the season. Can be either a numeric unique
            ID (e.g., ``"1"``) or a date-based code (e.g., ``"2016-02"``).
        :return: :class:`~clash_royale.models.leaderboard.LeagueSeasonV2` if
            ``season_id`` is numeric, otherwise
            :class:`~clash_royale.models.leaderboard.LeagueSeason`.
        """
        warnings.warn(
            "The API may return incomplete season data with null values.",
            UserWarning,
            stacklevel=2,
        )

        if season_id.isdigit():
            response = self._client._request(
                "GET", f"/locations/global/seasons/{season_id}"
            )
            return LeagueSeasonV2.model_validate(response)

        response = self._client._request(
            "GET", f"/locations/global/seasons/{season_id}"
        )
        return LeagueSeason.model_validate(response)

    def get_season_player_rankings(
        self,
        season_id: str,
        **params: Unpack[PaginationParams],
    ) -> PaginatedList[PlayerSeasonRanking]:
        """Get top player rankings for a season.

        :param season_id: The season ID (e.g., "2017-03").
        """
        return PaginatedList(
            client=self._client,
            endpoint=f"/locations/global/seasons/{season_id}/rankings/players",
            model=PlayerSeasonRanking,
            params=params,  # ty:ignore[invalid-argument-type]
        )

    def list_seasons(self) -> PaginatedList[LeagueSeason]:
        """List top player league seasons.

        .. warning:: The Clash Royale API may occasionally return incomplete
            season data with null values. This is a known API issue, not a
            library bug. Consider using :meth:`list_seasons_v2` instead.
        """
        warnings.warn(
            "The API may return incomplete season data with null values.",
            UserWarning,
            stacklevel=2,
        )

        return PaginatedList(
            client=self._client,
            endpoint="/locations/global/seasons",
            model=LeagueSeason,
            params={},
        )

    def list_seasons_v2(self) -> PaginatedList[LeagueSeasonV2]:
        """List league seasons with more details.

        .. warning:: The Clash Royale API may occasionally return incomplete
            season data with null values. This is a known API issue, not a
            library bug.
        """
        warnings.warn(
            "The API may return incomplete season data with null values.",
            UserWarning,
            stacklevel=2,
        )

        return PaginatedList(
            client=self._client,
            endpoint="/locations/global/seasonsV2",
            model=LeagueSeasonV2,
            params={},
        )

    def get_global_tournament_rankings(
        self,
        tournament_tag: str,
        **params: Unpack[PaginationParams],
    ) -> PaginatedList[LadderTournamentRanking]:
        """Get global tournament rankings."""
        encoded_tag = self._encode_tag(tournament_tag)
        return PaginatedList(
            client=self._client,
            endpoint=f"/locations/global/rankings/tournaments/{encoded_tag}",
            model=LadderTournamentRanking,
            params=params,  # ty:ignore[invalid-argument-type]
        )
