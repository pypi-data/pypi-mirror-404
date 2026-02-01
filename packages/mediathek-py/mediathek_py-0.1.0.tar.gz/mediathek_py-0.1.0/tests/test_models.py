import pytest

from mediathek_py.models import (
    Item,
    MediathekRequest,
    Query,
    QueryField,
    QueryInfo,
    QueryResult,
    SortField,
    SortOrder,
)


class TestItem:
    def test_parses_complete_response(self, sample_response):
        raw = sample_response["result"]["results"][0]
        item = Item.model_validate(raw)

        assert item.channel == "ARD"
        assert item.topic == "tagesschau"
        assert item.title == "tagesschau 20:00 Uhr"
        assert item.description == "Aktuelle Nachrichten aus aller Welt"
        assert item.timestamp == 1696269600
        assert item.duration == 932
        assert item.size == 137363456
        assert item.url_website == "https://www.ardmediathek.de/video/1"
        assert item.url_subtitle is None  # empty string → None
        assert item.url_video == "https://media.tagesschau.de/video/medium.mp4"
        assert item.url_video_low == "https://media.tagesschau.de/video/low.mp4"
        assert item.url_video_hd == "https://media.tagesschau.de/video/hd.mp4"
        assert item.filmliste_timestamp == 1696339020  # string → int
        assert item.id == "DCeoosOJEZLg30zx2pxtMQPBv4oBQnc+XEZf6LHOtC0="

    def test_empty_string_fields_become_none(self, sample_response):
        raw = sample_response["result"]["results"][1]
        item = Item.model_validate(raw)

        assert item.description is None
        assert item.url_video_low is None
        assert item.url_video_hd is None

    def test_livestream_empty_duration(self, sample_item_livestream):
        item = Item.model_validate(sample_item_livestream)
        assert item.duration is None

    def test_timestamp_as_string(self, sample_response):
        raw = sample_response["result"]["results"][0].copy()
        raw["timestamp"] = "1696269600"
        item = Item.model_validate(raw)
        assert item.timestamp == 1696269600
        assert isinstance(item.timestamp, int)


class TestQueryInfo:
    def test_parses_search_engine_time(self, sample_response):
        raw = sample_response["result"]["queryInfo"]
        qi = QueryInfo.model_validate(raw)
        assert isinstance(qi.search_engine_time, float)
        assert qi.search_engine_time == pytest.approx(4.39)

    def test_parses_camel_case(self, sample_response):
        raw = sample_response["result"]["queryInfo"]
        qi = QueryInfo.model_validate(raw)
        assert qi.filmliste_timestamp == 1696361700
        assert qi.result_count == 2
        assert qi.total_results == 61


class TestQueryResult:
    def test_parses_full_response(self, sample_response):
        raw = sample_response["result"]
        qr = QueryResult.model_validate(raw)
        assert qr.query_info.result_count == 2
        assert len(qr.results) == 2
        assert qr.results[0].channel == "ARD"
        assert qr.results[1].channel == "ZDF"


class TestMediathekRequest:
    def test_serializes_with_aliases(self):
        req = MediathekRequest(
            queries=[Query(fields=[QueryField.TOPIC], query="test")],
            sort_by=SortField.TIMESTAMP,
            sort_order=SortOrder.DESCENDING,
        )
        data = req.model_dump(by_alias=True, exclude_none=True)
        assert "sortBy" in data
        assert "sortOrder" in data
        assert data["sortBy"] == "timestamp"
        assert data["sortOrder"] == "desc"

    def test_omits_none_fields(self):
        req = MediathekRequest(
            queries=[Query(fields=[QueryField.TOPIC], query="test")],
        )
        data = req.model_dump(by_alias=True, exclude_none=True)
        assert "sortBy" not in data
        assert "sortOrder" not in data
        assert "duration_min" not in data
        assert "duration_max" not in data
        assert "future" not in data
        assert "size" not in data
        assert "offset" not in data


class TestEnums:
    def test_query_field_values(self):
        assert QueryField.TOPIC.value == "topic"
        assert QueryField.TITLE.value == "title"
        assert QueryField.CHANNEL.value == "channel"
        assert QueryField.DESCRIPTION.value == "description"

    def test_sort_field_values(self):
        assert SortField.CHANNEL.value == "channel"
        assert SortField.TIMESTAMP.value == "timestamp"
        assert SortField.DURATION.value == "duration"

    def test_sort_order_values(self):
        assert SortOrder.ASCENDING.value == "asc"
        assert SortOrder.DESCENDING.value == "desc"
