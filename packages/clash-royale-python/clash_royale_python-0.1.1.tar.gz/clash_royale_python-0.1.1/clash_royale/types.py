from __future__ import annotations

from typing import TypedDict


class PaginationParams(TypedDict, total=False):
    """Common pagination parameters for API requests.

    :param limit: Maximum total number of items to fetch (default: unlimited).
           Controls how many results you get in total.
           Example: `limit=50` will fetch at most 50 items across all pages.
    :param page_size: Number of items per API request.
               This is sent as "limit" to the API. Only change if you need
               to optimize request sizes or work around API constraints.
    :param after: Cursor for pagination (automatically managed by PaginatedList).
    :param before: Cursor for backward pagination (automatically managed by PaginatedList).
    """

    limit: int
    page_size: int
    after: str
    before: str


class ClanSearchParams(PaginationParams, total=False):
    """Parameters for clan search endpoint.

    :param limit: Maximum total number of items to fetch (default: unlimited).
            Controls how many results you get in total.
            Example: `limit=50` will fetch at most 50 items across all pages.
    :param page_size: Number of items per API request.
                This is sent as "limit" to the API. Only change if you need
                to optimize request sizes or work around API constraints.
    :param after: Cursor for pagination (automatically managed by PaginatedList).
    :param before: Cursor for backward pagination (automatically managed by PaginatedList).
    :param location_id: Filter by clan location identifier (e.g. 57000094).
    :param min_members: Filter by minimum number of clan members.
    :param max_members: Filter by maximum number of clan members.
    :param min_score: Filter by minimum amount of clan score.
    """

    location_id: int
    min_members: int
    max_members: int
    min_score: int
