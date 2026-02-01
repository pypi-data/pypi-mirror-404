from __future__ import annotations

from .client import Client
from .exceptions import (
    ClashRoyaleBadRequestError,
    ClashRoyaleException,
    ClashRoyaleHTTPError,
    ClashRoyaleNotFoundError,
    ClashRoyaleRateLimitError,
    ClashRoyaleServerError,
    ClashRoyaleUnauthorizedError,
    InvalidAPIKeyError,
)
from .models import (
    Arena,
    Badge,
    Battle,
    Card,
    Clan,
    ClanMember,
    ClanSearchResult,
    Icon,
    Location,
    Player,
    RiverRace,
    RiverRaceLog,
    UpcomingChest,
)
from .models.base import ISO8601DateTime
from .pagination import PaginatedList
from .resources import (
    Cards,
    Clans,
    GlobalTournaments,
    Leaderboards,
    Locations,
    Players,
    Tournaments,
)
from .types import ClanSearchParams, PaginationParams

__version__ = "0.1.1"

__all__ = [
    "Arena",
    "Badge",
    "Battle",
    "Card",
    "Cards",
    "Clan",
    "ClanMember",
    "ClanSearchParams",
    "ClanSearchResult",
    "Clans",
    "ClashRoyaleBadRequestError",
    "ClashRoyaleException",
    "ClashRoyaleHTTPError",
    "ClashRoyaleNotFoundError",
    "ClashRoyaleRateLimitError",
    "ClashRoyaleServerError",
    "ClashRoyaleUnauthorizedError",
    "Client",
    "GlobalTournaments",
    "Icon",
    "InvalidAPIKeyError",
    "ISO8601DateTime",
    "Leaderboards",
    "Location",
    "Locations",
    "PaginatedList",
    "PaginationParams",
    "Player",
    "Players",
    "RiverRace",
    "RiverRaceLog",
    "Tournaments",
    "UpcomingChest",
]
