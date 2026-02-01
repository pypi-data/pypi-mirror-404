from __future__ import annotations

from pydantic import Field

from clash_royale.models.common import Arena, Badge

from .base import CRBaseModel


class Location(CRBaseModel):
    """Represents a location."""

    id: int
    name: str
    is_country: bool = Field(alias="isCountry")
    country_code: str | None = Field(default=None, alias="countryCode")


class ClanRanking(CRBaseModel):
    """Represents a clan ranking."""

    clan_score: int = Field(alias="clanScore")
    badge_id: int = Field(alias="badgeId")
    location: Location
    members: int
    tag: str
    name: str
    rank: int
    previous_rank: int = Field(alias="previousRank")
    badge_urls: Badge | None = Field(default=None, alias="badgeUrls")


class PlayerRanking(CRBaseModel):
    """Represents a player ranking."""

    trophies: int
    clan: PlayerRankingClan | None = None
    tag: str
    name: str
    rank: int
    previous_rank: int = Field(alias="previousRank")
    badge_urls: Badge | None = Field(default=None, alias="badgeUrls")


class PlayerRankingClan(CRBaseModel):
    """Represents a player's clan in rankings."""

    tag: str
    name: str
    badge_id: int = Field(alias="badgeId")
    badge_urls: Badge | None = Field(default=None, alias="badgeUrls")


class PlayerPathOfLegendRanking(CRBaseModel):
    """Represents a player ranking in Path of Legends."""

    tag: str
    name: str
    exp_level: int = Field(alias="expLevel")
    elo_rating: int = Field(alias="eloRating")
    rank: int
    clan: PlayerRankingClan | None = None


class PlayerSeasonRanking(CRBaseModel):
    """Represents a player ranking for a season."""

    tag: str
    name: str
    exp_level: int = Field(alias="expLevel")
    trophies: int
    rank: int
    previous_rank: int | None = Field(default=None, alias="previousRank")
    clan: PlayerRankingClan | None = None
    arena: Arena | None = None


class LeagueSeason(CRBaseModel):
    """Represents a league season.

    .. note:: The API may return null values due to a known bug.
    """

    id: str | None = None


class LeagueSeasonV2(CRBaseModel):
    """Represents a league season with end dates.

    .. note:: The API may return null/missing values due to a known bug.
    """

    code: str | None = None
    unique_id: str | None = Field(default=None, alias="uniqueId")
    end_time: str | None = Field(default=None, alias="endTime")


class LadderTournamentRanking(CRBaseModel):
    """Represents a ladder tournament ranking."""

    clan: PlayerRankingClan | None = None
    wins: int
    losses: int
    tag: str
    name: str
    rank: int
    previous_rank: int = Field(alias="previousRank")
