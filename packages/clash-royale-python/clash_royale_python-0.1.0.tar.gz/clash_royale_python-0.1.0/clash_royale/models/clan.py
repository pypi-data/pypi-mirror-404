from __future__ import annotations

from pydantic import Field
from typing_extensions import Literal

from .base import CRBaseModel
from .common import Arena, Badge
from .location import Location


class ClanMember(CRBaseModel):
    """Represents a member of a clan."""

    tag: str
    name: str
    role: Literal["leader", "coLeader", "elder", "admin", "member", "notMember"]
    exp_level: int = Field(alias="expLevel")
    trophies: int
    arena: Arena
    clan_rank: int = Field(alias="clanRank")
    previous_clan_rank: int = Field(alias="previousClanRank")
    donations: int
    donations_received: int = Field(alias="donationsReceived")
    clan_chest_points: int = Field(alias="clanChestPoints")


class Clan(CRBaseModel):
    """Represents a Clash Royale clan."""

    tag: str
    name: str
    type: Literal["open", "inviteOnly", "closed"]
    description: str
    badge_id: int = Field(alias="badgeId")
    badge_urls: Badge | None = Field(default=None, alias="badgeUrls")
    clan_score: int = Field(alias="clanScore")
    clan_war_trophies: int = Field(alias="clanWarTrophies")
    location: Location
    required_trophies: int = Field(alias="requiredTrophies")
    donations_per_week: int = Field(alias="donationsPerWeek")
    clan_chest_status: Literal["inactive", "active", "completed", "unknown"] = Field(
        alias="clanChestStatus"
    )
    clan_chest_level: int = Field(alias="clanChestLevel")
    clan_chest_max_level: int = Field(alias="clanChestMaxLevel")
    members: int
    member_list: list[ClanMember] = Field(default_factory=list, alias="memberList")


class ClanSearchResult(CRBaseModel):
    """Represents a clan in search results."""

    tag: str
    name: str
    type: Literal["open", "inviteOnly", "closed"]
    badge_id: int = Field(alias="badgeId")
    badge_urls: Badge | None = Field(default=None, alias="badgeUrls")
    clan_score: int = Field(alias="clanScore")
    clan_war_trophies: int = Field(alias="clanWarTrophies")
    location: Location
    required_trophies: int = Field(alias="requiredTrophies")
    donations_per_week: int = Field(alias="donationsPerWeek")
    members: int


class RiverRaceParticipant(CRBaseModel):
    """Represents a participant in a river race."""

    tag: str
    name: str
    fame: int
    repair_points: int = Field(alias="repairPoints")
    boat_attacks: int = Field(alias="boatAttacks")
    decks_used: int = Field(alias="decksUsed")
    decks_used_today: int = Field(alias="decksUsedToday")


class RiverRaceClan(CRBaseModel):
    """Represents a clan participating in a river race."""

    tag: str
    name: str
    badge_id: int = Field(alias="badgeId")
    clan_score: int = Field(alias="clanScore")
    fame: int
    repair_points: int = Field(alias="repairPoints")
    finish_time: str | None = Field(default=None, alias="finishTime")
    period_points: int = Field(alias="periodPoints")
    participants: list[RiverRaceParticipant] = Field(default_factory=list)


class RiverRaceLogStanding(CRBaseModel):
    """Represents a clan standing in a river race log."""

    rank: int
    trophy_change: int = Field(alias="trophyChange")
    clan: RiverRaceClan


class RiverRace(CRBaseModel):
    """Represents a river race."""

    state: Literal[
        "clanNotFound", "accessDenied", "matchmaking", "matched", "full", "ended"
    ]
    clan: RiverRaceClan
    clans: list[RiverRaceClan] = Field(default_factory=list)
    collection_end_time: str | None = Field(default=None, alias="collectionEndTime")
    war_end_time: str | None = Field(default=None, alias="warEndTime")
    section_index: int = Field(alias="sectionIndex")
    period_index: int = Field(alias="periodIndex")
    period_type: Literal["training", "warDay", "colosseum"] = Field(alias="periodType")
    period_logs: list[PeriodLog] = Field(default_factory=list, alias="periodLogs")


class RiverRaceLog(CRBaseModel):
    """Represents a river race log entry."""

    season_id: int = Field(alias="seasonId")
    section_index: int = Field(alias="sectionIndex")
    created_date: str = Field(alias="createdDate")
    standings: list[RiverRaceLogStanding] = Field(default_factory=list)


class PeriodLog(CRBaseModel):
    """Represents a period log."""

    period_index: int = Field(alias="periodIndex")
    items: list[PeriodLogEntry] = Field(default_factory=list)


class PeriodLogEntry(CRBaseModel):
    """Represents a period log entry."""

    clan: PeriodLogEntryClan
    points_earned: int = Field(alias="pointsEarned")
    progress_start_of_day: int = Field(alias="progressStartOfDay")
    progress_end_of_day: int = Field(alias="progressEndOfDay")
    end_of_day_rank: int = Field(alias="endOfDayRank")
    progress_earned: int = Field(alias="progressEarned")
    num_of_defenses_remaining: int = Field(alias="numOfDefensesRemaining")
    progress_earned_from_defenses: int = Field(alias="progressEarnedFromDefenses")


class PeriodLogEntryClan(CRBaseModel):
    """Represents a clan in a period log entry."""

    tag: str
