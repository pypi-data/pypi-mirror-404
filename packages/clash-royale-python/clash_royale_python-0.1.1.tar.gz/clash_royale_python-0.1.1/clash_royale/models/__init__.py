"""Pydantic models for Clash Royale API responses."""

from __future__ import annotations

from .card import Card
from .clan import Clan, ClanMember, ClanSearchResult, RiverRace, RiverRaceLog
from .common import Arena, Badge, Icon
from .global_tournament import GlobalTournament
from .leaderboard import Leaderboard, LeaderboardPlayer
from .location import (
    ClanRanking,
    LadderTournamentRanking,
    LeagueSeason,
    LeagueSeasonV2,
    Location,
    PlayerPathOfLegendRanking,
    PlayerRanking,
    PlayerSeasonRanking,
)
from .player import Battle, Player, UpcomingChest
from .tournament import Tournament, TournamentHeader, TournamentMember

__all__ = [
    "Arena",
    "Badge",
    "Battle",
    "Card",
    "Clan",
    "ClanMember",
    "ClanRanking",
    "ClanSearchResult",
    "GlobalTournament",
    "Icon",
    "LadderTournamentRanking",
    "Leaderboard",
    "LeaderboardPlayer",
    "LeagueSeason",
    "LeagueSeasonV2",
    "Location",
    "Player",
    "PlayerPathOfLegendRanking",
    "PlayerRanking",
    "PlayerSeasonRanking",
    "RiverRace",
    "RiverRaceLog",
    "Tournament",
    "TournamentHeader",
    "TournamentMember",
    "UpcomingChest",
]
