from __future__ import annotations

import json as json_lib
from pathlib import Path
from typing import Callable

import httpx

from mediathek_py.exceptions import ApiError, EmptyResponseError, MediathekError
from mediathek_py.models import (
    MediathekRequest,
    Query,
    QueryField,
    QueryResult,
    SortField,
    SortOrder,
)


class Mediathek:
    """Client for the MediathekViewWeb API."""

    def __init__(
        self,
        user_agent: str = "mediathek-py",
        base_url: str = "https://mediathekviewweb.de",
    ):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(headers={"User-Agent": user_agent})

    def search(self) -> SearchBuilder:
        """Create a new search query builder."""
        return SearchBuilder(self)

    def build_from_string(
        self, query_string: str, search_everywhere: bool = False
    ) -> SearchBuilder:
        """Parse a prefixed search string and return a builder (does not execute).

        Prefix syntax:
            !channel  #topic  +title  *description  >min_dur  <max_dur
        Unprefixed tokens search topic+title (or all fields with search_everywhere).
        Commas in prefixed tokens are replaced with spaces.
        """
        tokens = query_string.split()
        builder = self.search()
        duration_min: int | None = None
        duration_max: int | None = None

        prefix_map: dict[str, list[QueryField]] = {
            "!": [QueryField.CHANNEL],
            "#": [QueryField.TOPIC],
            "+": [QueryField.TITLE],
            "*": [QueryField.DESCRIPTION],
        }

        unprefixed_tokens: list[str] = []

        for token in tokens:
            if not token:
                continue

            first = token[0]

            if first in prefix_map:
                value = token[1:].replace(",", " ")
                builder = builder.query(prefix_map[first], value)
            elif first == ">":
                try:
                    duration_min = int(token[1:])
                except ValueError:
                    pass
            elif first == "<":
                try:
                    duration_max = int(token[1:])
                except ValueError:
                    pass
            else:
                unprefixed_tokens.append(token)

        if unprefixed_tokens:
            if search_everywhere:
                fields = [
                    QueryField.CHANNEL,
                    QueryField.TOPIC,
                    QueryField.TITLE,
                    QueryField.DESCRIPTION,
                ]
            else:
                fields = [QueryField.TOPIC, QueryField.TITLE]
            builder = builder.query(fields, " ".join(unprefixed_tokens))

        if duration_min is not None:
            builder = builder.duration_min(duration_min)
        if duration_max is not None:
            builder = builder.duration_max(duration_max)

        return builder

    def search_by_string(
        self, query_string: str, search_everywhere: bool = False
    ) -> QueryResult:
        """Parse a prefixed search string and execute the query."""
        return self.build_from_string(query_string, search_everywhere).execute()

    def download(
        self,
        url: str,
        output: Path,
        progress_callback: Callable[[int, int | None], None] | None = None,
    ) -> Path:
        """Download a video file from the given URL."""
        try:
            with self._client.stream("GET", url) as response:
                response.raise_for_status()
                total = (
                    int(response.headers["content-length"])
                    if "content-length" in response.headers
                    else None
                )
                downloaded = 0
                with open(output, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)
        except httpx.HTTPStatusError as e:
            raise MediathekError(f"Download failed: HTTP {e.response.status_code}") from e
        return output

    def _send_query(self, request: MediathekRequest) -> QueryResult:
        """Send a query to the MediathekViewWeb API."""
        body = request.model_dump(by_alias=True, exclude_none=True)
        try:
            response = self._client.post(
                f"{self._base_url}/api/query",
                content=json_lib.dumps(body),
                headers={"Content-Type": "text/plain"},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise MediathekError(f"HTTP error: {e.response.status_code}") from e

        data = response.json()

        if data.get("err"):
            raise ApiError(data["err"])

        if data.get("result") is None:
            raise EmptyResponseError()

        return QueryResult.model_validate(data["result"])

    def __enter__(self) -> Mediathek:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()


class SearchBuilder:
    """Fluent builder for MediathekViewWeb search queries."""

    def __init__(self, client: Mediathek):
        self._client = client
        self._queries: list[Query] = []
        self._duration_min: int | None = None
        self._duration_max: int | None = None
        self._future: bool | None = None
        self._sort_by: SortField | None = None
        self._sort_order: SortOrder | None = None
        self._size: int | None = None
        self._offset: int | None = None

    def query(self, fields: list[QueryField], text: str) -> SearchBuilder:
        self._queries.append(Query(fields=fields, query=text))
        return self

    def duration_min(self, minutes: int) -> SearchBuilder:
        self._duration_min = minutes * 60
        return self

    def duration_max(self, minutes: int) -> SearchBuilder:
        self._duration_max = minutes * 60
        return self

    def include_future(self, value: bool = True) -> SearchBuilder:
        self._future = value
        return self

    def sort_by(self, field: SortField) -> SearchBuilder:
        self._sort_by = field
        return self

    def sort_order(self, order: SortOrder) -> SearchBuilder:
        self._sort_order = order
        return self

    def size(self, n: int) -> SearchBuilder:
        self._size = n
        return self

    def offset(self, n: int) -> SearchBuilder:
        self._offset = n
        return self

    def execute(self) -> QueryResult:
        request = MediathekRequest(
            queries=self._queries,
            duration_min=self._duration_min,
            duration_max=self._duration_max,
            future=self._future,
            sort_by=self._sort_by,
            sort_order=self._sort_order,
            size=self._size,
            offset=self._offset,
        )
        return self._client._send_query(request)
