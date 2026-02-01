from __future__ import annotations

from .base import CRBaseModel
from .player import PlayerClan


class Leaderboard(CRBaseModel):
    """Represents a leaderboard."""

    id: int
    name: str


class LeaderboardPlayer(CRBaseModel):
    """Represents a player in a leaderboard."""

    tag: str
    name: str
    rank: int
    score: int
    clan: PlayerClan | None = None
