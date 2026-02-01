from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict


def parse_iso8601_datetime(v: str | datetime) -> datetime:
    """Parse ISO 8601 datetime string to datetime object.

    Handles format like: "20260109T222745.000Z"
    """
    if isinstance(v, datetime):
        return v
    # Parse ISO 8601 format with Z timezone
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


ISO8601DateTime = Annotated[datetime, BeforeValidator(parse_iso8601_datetime)]
"""Type annotation for ISO 8601 datetime fields."""


class CRBaseModel(BaseModel):
    """Base model for all Clash Royale API models."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )
