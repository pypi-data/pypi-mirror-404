from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Generic, TypeVar, overload

from .models.base import CRBaseModel
from .types import ClanSearchParams, PaginationParams

if TYPE_CHECKING:
    from .client import Client

ResourceType = TypeVar("ResourceType", bound="CRBaseModel")


class PaginatedList(Generic[ResourceType]):
    """Lazy-loading paginated list that fetches pages on demand."""

    def __init__(
        self,
        client: Client,
        endpoint: str,
        model: type[ResourceType],
        params: PaginationParams | ClanSearchParams | None = None,
    ):
        self._client = client
        self._endpoint = endpoint
        self._model = model

        # Extract client-side pagination control params
        _params = params.copy() if params else {}
        self._limit: int | None = _params.pop("limit", None)
        self._page_size: int | None = _params.pop("page_size", None)

        # Remaining params are for the API (after, before, etc.)
        self._params: dict[str, str | int] = _params

        self._elements: list[ResourceType] = []
        self._after_cursor: str | None = None
        self._has_more: bool = True
        self._iter = iter(self)

    def __repr__(self) -> str:
        repr_size = 5
        data: list[ResourceType | str] = list(self[: repr_size + 1])
        if len(data) > repr_size:
            data[-1] = "..."
        return f"<{self.__class__.__name__} {data!r}>"

    @overload
    def __getitem__(self, index: int) -> ResourceType: ...

    @overload
    def __getitem__(self, index: slice) -> list[ResourceType]: ...

    def __getitem__(self, index: int | slice) -> ResourceType | list[ResourceType]:
        if isinstance(index, int):
            self._fetch_to_index(index)
            return self._elements[index]
        if index.stop is not None:
            self._fetch_to_index(index.stop)
        else:
            self._fetch_all()
        return self._elements[index]

    def __iter__(self) -> Generator[ResourceType, None, None]:
        yield from self._elements
        while self._has_more and (
            self._limit is None or len(self._elements) < self._limit
        ):
            yield from self._grow()

    def __next__(self) -> ResourceType:
        return next(self._iter)

    def _could_grow(self) -> bool:
        if self._limit is not None and len(self._elements) >= self._limit:
            return False
        return self._has_more

    def _grow(self) -> list[ResourceType]:
        new_elements = self._fetch_next_page()
        # If limit is set, only add elements up to the limit
        if self._limit is not None:
            remaining = self._limit - len(self._elements)
            if remaining <= 0:
                return []
            new_elements = new_elements[:remaining]
        self._elements.extend(new_elements)
        return new_elements

    def _fetch_next_page(self) -> list[ResourceType]:
        params = self._params.copy()

        if self._after_cursor:
            params["after"] = self._after_cursor

        if self._page_size:
            # Send page_size as "limit" to the API
            params["limit"] = self._page_size

        response = self._client._request("GET", self._endpoint, params=params)

        # Update cursor for next page
        paging = response.get("paging", {})
        cursors = paging.get("cursors", {})
        self._after_cursor = cursors.get("after")
        self._has_more = self._after_cursor is not None

        # Parse items with model
        items = response.get("items", [])
        return [self._model.model_validate(item) for item in items]

    def _fetch_to_index(self, index: int) -> None:
        while len(self._elements) <= index and self._could_grow():
            self._grow()

    def _fetch_all(self) -> None:
        while self._could_grow():
            self._grow()
