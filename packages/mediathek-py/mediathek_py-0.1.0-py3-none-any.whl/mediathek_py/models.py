from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryField(str, Enum):
    CHANNEL = "channel"
    TOPIC = "topic"
    TITLE = "title"
    DESCRIPTION = "description"


class SortField(str, Enum):
    CHANNEL = "channel"
    TIMESTAMP = "timestamp"
    DURATION = "duration"


class SortOrder(str, Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class Query(BaseModel):
    fields: list[QueryField]
    query: str


class MediathekRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    queries: list[Query]
    duration_min: int | None = None
    duration_max: int | None = None
    future: bool | None = None
    sort_by: SortField | None = Field(default=None, alias="sortBy")
    sort_order: SortOrder | None = Field(default=None, alias="sortOrder")
    size: int | None = None
    offset: int | None = None


def _empty_string_to_none(v: object) -> object:
    if v == "":
        return None
    return v


def _parse_int_or_string(v: object) -> int | None:
    if v == "" or v is None:
        return None
    return int(v)


class Item(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    channel: str
    topic: str
    title: str
    description: str | None = None
    timestamp: int
    duration: int | None = None
    size: int | None = None
    url_website: str
    url_subtitle: str | None = None
    url_video: str
    url_video_low: str | None = None
    url_video_hd: str | None = None
    filmliste_timestamp: int = Field(alias="filmlisteTimestamp")
    id: str

    @field_validator("description", "url_subtitle", "url_video_low", "url_video_hd", mode="before")
    @classmethod
    def empty_string_to_none(cls, v: object) -> object:
        return _empty_string_to_none(v)

    @field_validator("duration", mode="before")
    @classmethod
    def parse_duration(cls, v: object) -> int | None:
        return _parse_int_or_string(v)

    @field_validator("timestamp", "filmliste_timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: object) -> int:
        return int(v)


class QueryInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    filmliste_timestamp: int = Field(alias="filmlisteTimestamp")
    result_count: int = Field(alias="resultCount")
    search_engine_time: float = Field(alias="searchEngineTime")
    total_results: int = Field(alias="totalResults")

    @field_validator("search_engine_time", mode="before")
    @classmethod
    def parse_search_engine_time(cls, v: object) -> float:
        return float(v)


class QueryResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query_info: QueryInfo = Field(alias="queryInfo")
    results: list[Item]
