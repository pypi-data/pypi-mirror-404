from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import CRBaseModel, ISO8601DateTime
from .card import Card, SupportCard
from .common import Arena, GameMode, PlayerClan


class PlayerCard(Card):
    """Represents a card in a player's collection."""

    level: int
    star_level: int | None = Field(default=None, alias="starLevel")
    evolution_level: int | None = Field(default=None, alias="evolutionLevel")


class LeagueStatistics(CRBaseModel):
    """Player's league statistics."""

    current_season: dict | None = Field(default=None, alias="currentSeason")
    previous_season: dict | None = Field(default=None, alias="previousSeason")
    best_season: dict | None = Field(default=None, alias="bestSeason")


class Player(CRBaseModel):
    """Represents a Clash Royale player."""

    tag: str
    name: str
    exp_level: int = Field(alias="expLevel")
    trophies: int
    best_trophies: int = Field(alias="bestTrophies")
    wins: int
    losses: int
    battle_count: int = Field(alias="battleCount")
    three_crown_wins: int = Field(alias="threeCrownWins")
    challenge_cards_won: int = Field(alias="challengeCardsWon")
    challenge_max_wins: int = Field(alias="challengeMaxWins")
    tournament_cards_won: int = Field(alias="tournamentCardsWon")
    tournament_battle_count: int = Field(alias="tournamentBattleCount")
    role: str | None = None
    donations: int | None = None
    donations_received: int | None = Field(default=None, alias="donationsReceived")
    total_donations: int = Field(alias="totalDonations")
    clan: PlayerClan | None = None
    arena: Arena | None = None
    league_statistics: LeagueStatistics | None = Field(
        default=None, alias="leagueStatistics"
    )
    cards: list[Card] = []
    current_deck: list[PlayerCard] = Field(default_factory=list, alias="currentDeck")
    current_favourite_card: Card | None = Field(
        default=None, alias="currentFavouriteCard"
    )
    star_points: int | None = Field(default=None, alias="starPoints")
    exp_points: int | None = Field(default=None, alias="expPoints")


class BattlePlayer(CRBaseModel):
    """Player information in a battle."""

    tag: str
    name: str
    crowns: int
    king_tower_hit_points: int | None = Field(default=None, alias="kingTowerHitPoints")
    princess_towers_hit_points: list[int] | None = Field(
        default=None, alias="princessTowersHitPoints"
    )
    cards: list[Card] = []
    support_cards: list[SupportCard] | None = Field(default=None, alias="supportCards")
    starting_trophies: int | None = Field(default=None, alias="startingTrophies")
    trophy_change: int | None = Field(default=None, alias="trophyChange")
    clan: PlayerClan | None = None
    global_rank: int | None = Field(default=None, alias="globalRank")
    elixir_leaked: float | None = Field(default=None, alias="elixirLeaked")


class BattleTeam(CRBaseModel):
    """Team information in a battle."""

    crowns: int
    elixir_leaked: float | None = Field(default=None, alias="elixirLeaked")


class Battle(CRBaseModel):
    """Represents a battle in a player's battle log."""

    type: Literal[
        "PvP",
        "PvE",
        "clanMate",
        "tournament",
        "friendly",
        "survival",
        "PvP2v2",
        "clanMate2v2",
        "challenge2v2",
        "clanWarCollectionDay",
        "clanWarWarDay",
        "casual1v1",
        "casual2v2",
        "boatBattle",
        "boatBattlePractice",
        "riverRacePvP",
        "riverRacePvp",
        "riverRaceDuel",
        "riverRaceDuelColosseum",
        "tutorial",
        "pathOfLegend",
        "seasonalBattle",
        "practice",
        "trail",
        "unknown",
    ]
    battle_time: ISO8601DateTime = Field(alias="battleTime")
    is_ladder_tournament: bool = Field(alias="isLadderTournament")
    arena: Arena
    game_mode: GameMode = Field(alias="gameMode")
    deck_selection: (
        Literal[
            "collection",
            "draft",
            "draftCompetitive",
            "predefined",
            "eventDeck",
            "pick",
            "wardeckPick",
            "warDeckPick",
            "quaddeckPick",
            "unknown",
        ]
        | None
    ) = Field(default=None, alias="deckSelection")
    team: list[BattlePlayer] = []
    opponent: list[BattlePlayer] = []
    is_hosted_match: bool = Field(alias="isHostedMatch")
    league_number: int = Field(alias="leagueNumber")


class UpcomingChest(CRBaseModel):
    """Represents an upcoming chest for a player."""

    index: int
    name: str
