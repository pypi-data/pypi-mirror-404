import json
from pathlib import Path

import httpx
import pytest
import respx

from mediathek_py.client import Mediathek, SearchBuilder
from mediathek_py.exceptions import ApiError, EmptyResponseError, MediathekError
from mediathek_py.models import QueryField, SortField, SortOrder


BASE_URL = "https://mediathekviewweb.de"


class TestSearchBuilder:
    @respx.mock
    def test_sends_correct_request(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            result = (
                m.search()
                .query([QueryField.TOPIC], "tagesschau")
                .execute()
            )

        assert route.called
        request = route.calls.last.request
        assert request.headers["content-type"] == "text/plain"
        assert "user-agent" in request.headers

        body = json.loads(request.content)
        assert body["queries"] == [{"fields": ["topic"], "query": "tagesschau"}]

        assert result.query_info.result_count == 2
        assert len(result.results) == 2
        assert result.results[0].channel == "ARD"

    @respx.mock
    def test_query_adds_to_queries_list(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search().query(
                [QueryField.TOPIC], "tagesschau"
            ).query(
                [QueryField.TITLE], "nachrichten"
            ).execute()

        body = json.loads(route.calls.last.request.content)
        assert len(body["queries"]) == 2
        assert body["queries"][0] == {"fields": ["topic"], "query": "tagesschau"}
        assert body["queries"][1] == {"fields": ["title"], "query": "nachrichten"}

    @respx.mock
    def test_duration_filter(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search().query(
                [QueryField.TOPIC], "test"
            ).duration_min(10).duration_max(30).execute()

        body = json.loads(route.calls.last.request.content)
        assert body["duration_min"] == 600
        assert body["duration_max"] == 1800

    @respx.mock
    def test_sort_and_pagination(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search().query(
                [QueryField.TOPIC], "test"
            ).sort_by(SortField.TIMESTAMP).sort_order(
                SortOrder.DESCENDING
            ).size(5).offset(10).execute()

        body = json.loads(route.calls.last.request.content)
        assert body["sortBy"] == "timestamp"
        assert body["sortOrder"] == "desc"
        assert body["size"] == 5
        assert body["offset"] == 10

    @respx.mock
    def test_include_future(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search().query(
                [QueryField.TOPIC], "test"
            ).include_future(True).execute()

        body = json.loads(route.calls.last.request.content)
        assert body["future"] is True


class TestSearchByString:
    @respx.mock
    def test_channel_prefix(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search_by_string("!ard")

        body = json.loads(route.calls.last.request.content)
        assert {"fields": ["channel"], "query": "ard"} in body["queries"]

    @respx.mock
    def test_topic_prefix(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search_by_string("#tagesschau")

        body = json.loads(route.calls.last.request.content)
        assert {"fields": ["topic"], "query": "tagesschau"} in body["queries"]

    @respx.mock
    def test_title_prefix(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search_by_string("+nachrichten")

        body = json.loads(route.calls.last.request.content)
        assert {"fields": ["title"], "query": "nachrichten"} in body["queries"]

    @respx.mock
    def test_description_prefix(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search_by_string("*norwegen")

        body = json.loads(route.calls.last.request.content)
        assert {"fields": ["description"], "query": "norwegen"} in body["queries"]

    @respx.mock
    def test_duration_prefixes(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search_by_string(">10 <30")

        body = json.loads(route.calls.last.request.content)
        assert body["duration_min"] == 600
        assert body["duration_max"] == 1800

    @respx.mock
    def test_comma_replacement(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search_by_string("#sturm,der,liebe")

        body = json.loads(route.calls.last.request.content)
        assert {"fields": ["topic"], "query": "sturm der liebe"} in body["queries"]

    @respx.mock
    def test_unprefixed_default(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search_by_string("tagesschau")

        body = json.loads(route.calls.last.request.content)
        assert {"fields": ["topic", "title"], "query": "tagesschau"} in body["queries"]

    @respx.mock
    def test_unprefixed_everywhere(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search_by_string("tagesschau", search_everywhere=True)

        body = json.loads(route.calls.last.request.content)
        assert {
            "fields": ["channel", "topic", "title", "description"],
            "query": "tagesschau",
        } in body["queries"]

    @respx.mock
    def test_mixed(self, sample_response):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_response,
        )

        with Mediathek() as m:
            m.search_by_string("!ard #tagesschau >10")

        body = json.loads(route.calls.last.request.content)
        assert {"fields": ["channel"], "query": "ard"} in body["queries"]
        assert {"fields": ["topic"], "query": "tagesschau"} in body["queries"]
        assert body["duration_min"] == 600


class TestErrorHandling:
    @respx.mock
    def test_api_error_raises_exception(self, sample_error_response):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_error_response,
        )

        with Mediathek() as m:
            with pytest.raises(ApiError) as exc_info:
                m.search().query([QueryField.TOPIC], "x").execute()

        assert "query too short" in str(exc_info.value)

    @respx.mock
    def test_empty_response_raises_exception(self, sample_empty_response):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=sample_empty_response,
        )

        with Mediathek() as m:
            with pytest.raises(EmptyResponseError):
                m.search().query([QueryField.TOPIC], "test").execute()

    @respx.mock
    def test_http_error_raises_exception(self):
        respx.post(f"{BASE_URL}/api/query").respond(status_code=500)

        with Mediathek() as m:
            with pytest.raises(MediathekError):
                m.search().query([QueryField.TOPIC], "test").execute()


class TestClientContextManager:
    def test_context_manager(self):
        with Mediathek() as m:
            assert isinstance(m, Mediathek)


class TestDownload:
    @respx.mock
    def test_download_video_streams_to_file(self, tmp_path):
        video_content = b"fake video content " * 100
        respx.get("https://media.tagesschau.de/video/hd.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )

        output_path = tmp_path / "test.mp4"
        with Mediathek() as m:
            m.download("https://media.tagesschau.de/video/hd.mp4", output_path)

        assert output_path.exists()
        assert output_path.read_bytes() == video_content
