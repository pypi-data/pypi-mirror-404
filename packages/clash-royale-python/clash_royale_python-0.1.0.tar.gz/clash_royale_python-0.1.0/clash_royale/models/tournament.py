from __future__ import annotations

from pydantic import Field
from typing_extensions import Literal

from clash_royale.models.common import PlayerClan

from .base import CRBaseModel, ISO8601DateTime


class TournamentMember(CRBaseModel):
    """Represents a member in a tournament."""

    tag: str
    name: str
    score: int
    rank: int
    clan: PlayerClan | None = None


class TournamentHeader(CRBaseModel):
    """Represents a Clash Royale tournament header."""

    tag: str
    type: Literal["open", "passwordProtected", "unknown"]
    status: Literal["inPreparation", "inProgress", "ended", "unknown"]
    creator_tag: str = Field(alias="creatorTag")
    name: str
    description: str | None = None
    capacity: int
    max_capacity: int = Field(alias="maxCapacity")
    preparation_duration: int = Field(alias="preparationDuration")
    duration: int
    created_time: ISO8601DateTime = Field(alias="createdTime")
    first_place_card_prize: int = Field(alias="firstPlaceCardPrize")
    level_cap: int = Field(alias="levelCap")


class Tournament(TournamentHeader):
    """Represents a Clash Royale tournament."""

    started_time: ISO8601DateTime | None = Field(default=None, alias="startedTime")
    ended_time: ISO8601DateTime | None = Field(default=None, alias="endedTime")
    members_list: list[TournamentMember] = Field(
        default_factory=list, alias="membersList"
    )
