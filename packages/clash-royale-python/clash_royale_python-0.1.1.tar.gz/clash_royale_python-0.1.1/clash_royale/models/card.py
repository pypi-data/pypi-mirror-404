from __future__ import annotations

from pydantic import Field
from typing_extensions import Literal

from .base import CRBaseModel
from .common import Icon


class Card(CRBaseModel):
    """Represents a card in Clash Royale."""

    name: str
    id: int
    max_level: int = Field(alias="maxLevel")
    max_evolution_level: int | None = Field(default=None, alias="maxEvolutionLevel")
    elixir_cost: int | None = Field(
        default=None, alias="elixirCost"
    )  # elxir_cost may be `None` due to the "mirror" card
    icon_urls: Icon = Field(alias="iconUrls")
    rarity: Literal["common", "rare", "epic", "legendary", "champion"]


class SupportCard(CRBaseModel):
    """Represents a support card in Clash Royale with additional attributes."""

    name: str
    id: int
    level: int
    max_level: int = Field(alias="maxLevel")
    icon_urls: Icon = Field(alias="iconUrls")
    rarity: Literal["common", "rare", "epic", "legendary", "champion"]
