from __future__ import annotations

from pydantic import Field
from typing_extensions import Literal

from .base import CRBaseModel
from .common import GameMode


class GlobalTournament(CRBaseModel):
    """Represents a global tournament."""

    tag: str
    title: str
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    max_losses: int = Field(alias="maxLosses")
    min_exp_level: int = Field(alias="minExpLevel")
    tournament_level: int = Field(alias="tournamentLevel")
    milestones: list[SurvivalMilestoneReward] = Field(default_factory=list)
    free_tier_rewards: list[SurvivalMilestoneReward] | None = Field(
        default=None, alias="freeTierRewards"
    )
    top_rank_reward: list[SurvivalMilestoneReward] | None = Field(
        default=None, alias="topRankReward"
    )
    game_mode: GameMode | None = Field(default=None, alias="gameMode")
    max_top_reward_rank: int | None = Field(default=None, alias="maxTopRewardRank")


class SurvivalMilestoneReward(CRBaseModel):
    """Represents a survival milestone reward in Clash Royale."""

    rarity: Literal["common", "rare", "epic", "legendary", "champion"]
    chest: str
    resources: Literal["gold", "unknown"]
    type: Literal[
        "none",
        "card_stack",
        "chest",
        "card_stack_random",
        "resource",
        "trade_token",
        "consumable",
    ]
    amount: int
    card: SurvivalMilestoneRewardCard | None = None
    consumable_name: str | None = Field(default=None, alias="consumableName")
    wins: int


class SurvivalMilestoneRewardCard(CRBaseModel):
    """Represents a card in a survival milestone reward."""

    id: int
    name: str
    rarity: Literal["common", "rare", "epic", "legendary", "champion"]
    max_level: int = Field(alias="maxLevel")
    elixir_cost: int = Field(alias="elixirCost")
    max_evolution_level: int | None = Field(default=None, alias="maxEvolutionLevel")
