from __future__ import annotations

from pydantic import Field

from .base import CRBaseModel


class Icon(CRBaseModel):
    """Icon URLs for various game elements."""

    medium: str
    evolution_medium: str | None = Field(default=None, alias="evolutionMedium")
    hero_medium: str | None = Field(default=None, alias="heroMedium")


class Arena(CRBaseModel):
    """Arena information."""

    id: int
    name: str
    raw_name: str | None = Field(default=None, alias="rawName")


class GameMode(CRBaseModel):
    """Represents a game mode in Clash Royale."""

    id: int
    name: str | None = None


class PlayerClan(CRBaseModel):
    """Basic clan information for a player."""

    tag: str
    name: str
    badge_id: int | None = Field(default=None, alias="badgeId")


class Badge(CRBaseModel):
    """Clan badge information."""

    url: str
