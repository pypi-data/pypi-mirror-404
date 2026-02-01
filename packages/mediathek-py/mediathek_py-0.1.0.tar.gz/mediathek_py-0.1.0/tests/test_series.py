import json

import respx

from mediathek_py.series import (
    EpisodeInfo,
    SeriesEpisode,
    collect_series,
    parse_episode_info,
)
from mediathek_py.client import Mediathek
from mediathek_py.models import Item


BASE_URL = "https://mediathekviewweb.de"


def _make_item_dict(
    title, topic="Feuer & Flamme", channel="WDR", timestamp=1696269600, duration=2600
):
    """Build a realistic item dict for testing."""
    return {
        "channel": channel,
        "topic": topic,
        "title": title,
        "description": "",
        "timestamp": timestamp,
        "duration": duration,
        "size": 137363456,
        "url_website": "https://www.ardmediathek.de/video/1",
        "url_subtitle": "",
        "url_video": "https://media.example.de/video/medium.mp4",
        "url_video_low": "https://media.example.de/video/low.mp4",
        "url_video_hd": "https://media.example.de/video/hd.mp4",
        "filmlisteTimestamp": "1696339020",
        "id": f"id-{title[:10]}",
    }


def _make_api_response(items, total_results=None):
    """Wrap item dicts in a full API response envelope."""
    if total_results is None:
        total_results = len(items)
    return {
        "err": None,
        "result": {
            "queryInfo": {
                "filmlisteTimestamp": 1696361700,
                "resultCount": len(items),
                "searchEngineTime": "1.23",
                "totalResults": total_results,
            },
            "results": items,
        },
    }


class TestParseEpisodeInfo:
    def test_standard_sxx_exx_format(self):
        info = parse_episode_info("Folge 6: Explosion bei Brand (S06/E06)")
        assert info is not None
        assert info.season == 6
        assert info.episode == 6

    def test_sxx_exx_with_different_numbers(self):
        info = parse_episode_info("Folge 1: Feuer & Flamme (S01/E01)")
        assert info is not None
        assert info.season == 1
        assert info.episode == 1

    def test_sxx_exx_double_digit(self):
        info = parse_episode_info(
            "Folge 10: Seniorin stürzt auf Wanderung (S10/E10)"
        )
        assert info is not None
        assert info.season == 10
        assert info.episode == 10

    def test_folge_only_fallback(self):
        info = parse_episode_info("Folge 3: Some Episode Title")
        assert info is not None
        assert info.season == 1
        assert info.episode == 3

    def test_folge_only_high_number(self):
        info = parse_episode_info("Folge 42: Another Episode")
        assert info is not None
        assert info.season == 1
        assert info.episode == 42

    def test_trailer_returns_none(self):
        info = parse_episode_info("Trailer: Feuer & Flamme Staffel 10")
        assert info is None

    def test_unrelated_title_returns_none(self):
        info = parse_episode_info("tagesschau 20:00 Uhr")
        assert info is None

    def test_empty_title_returns_none(self):
        info = parse_episode_info("")
        assert info is None

    def test_sxx_exx_takes_precedence_over_folge(self):
        """When both patterns exist, (SXX/EXX) should win over Folge N for season."""
        info = parse_episode_info("Folge 3: Title (S02/E03)")
        assert info is not None
        assert info.season == 2
        assert info.episode == 3


class TestSeriesEpisode:
    def test_filename(self):
        item = Item.model_validate(
            _make_item_dict("Folge 6: Explosion bei Brand (S06/E06)")
        )
        ep = SeriesEpisode(item=item, info=EpisodeInfo(season=6, episode=6))
        assert ep.filename() == "s06e06.mp4"

    def test_filename_single_digit(self):
        item = Item.model_validate(
            _make_item_dict("Folge 1: Feuer & Flamme (S01/E01)")
        )
        ep = SeriesEpisode(item=item, info=EpisodeInfo(season=1, episode=1))
        assert ep.filename() == "s01e01.mp4"

    def test_filename_double_digit(self):
        item = Item.model_validate(
            _make_item_dict("Folge 10: Something (S10/E10)")
        )
        ep = SeriesEpisode(item=item, info=EpisodeInfo(season=10, episode=10))
        assert ep.filename() == "s10e10.mp4"


class TestCollectSeries:
    @respx.mock
    def test_collects_single_page(self):
        items = [
            _make_item_dict("Folge 1: Feuer & Flamme (S01/E01)", timestamp=100),
            _make_item_dict("Folge 2: Feuer & Flamme (S01/E02)", timestamp=200),
        ]
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_make_api_response(items),
        )

        with Mediathek() as m:
            episodes = collect_series(m, "Feuer & Flamme")

        assert len(episodes) == 2
        assert episodes[0].info.season == 1
        assert episodes[0].info.episode == 1
        assert episodes[1].info.season == 1
        assert episodes[1].info.episode == 2

    @respx.mock
    def test_paginates_across_pages(self):
        page1_items = [
            _make_item_dict(f"Folge {i}: Title (S01/E{i:02d})", timestamp=i * 100)
            for i in range(1, 4)
        ]
        page2_items = [
            _make_item_dict(f"Folge {i}: Title (S01/E{i:02d})", timestamp=i * 100)
            for i in range(4, 6)
        ]

        route = respx.post(f"{BASE_URL}/api/query")
        route.side_effect = [
            respx.MockResponse(json=_make_api_response(page1_items, total_results=5)),
            respx.MockResponse(json=_make_api_response(page2_items, total_results=5)),
        ]

        with Mediathek() as m:
            episodes = collect_series(m, "Feuer & Flamme", page_size=3)

        assert len(episodes) == 5
        # Verify pagination happened — two API calls
        assert route.call_count == 2
        # Verify request offsets
        first_body = json.loads(route.calls[0].request.content)
        second_body = json.loads(route.calls[1].request.content)
        assert first_body["offset"] == 0
        assert second_body["offset"] == 3

    @respx.mock
    def test_skips_unparseable_items(self):
        items = [
            _make_item_dict("Folge 1: Feuer & Flamme (S01/E01)", timestamp=100),
            _make_item_dict("Trailer: Feuer & Flamme", timestamp=200),
            _make_item_dict("Folge 2: Feuer & Flamme (S01/E02)", timestamp=300),
        ]
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_make_api_response(items),
        )

        with Mediathek() as m:
            episodes = collect_series(m, "Feuer & Flamme")

        assert len(episodes) == 2
        titles = [ep.item.title for ep in episodes]
        assert "Trailer: Feuer & Flamme" not in titles

    @respx.mock
    def test_deduplicates_by_season_episode(self):
        items = [
            _make_item_dict("Folge 1: Feuer & Flamme (S01/E01)", timestamp=100),
            _make_item_dict("Folge 1: Feuer & Flamme (S01/E01)", timestamp=200),
            _make_item_dict("Folge 2: Feuer & Flamme (S01/E02)", timestamp=300),
        ]
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_make_api_response(items),
        )

        with Mediathek() as m:
            episodes = collect_series(m, "Feuer & Flamme")

        assert len(episodes) == 2

    @respx.mock
    def test_sorts_by_season_then_episode(self):
        items = [
            _make_item_dict("Folge 2: Title (S02/E02)", timestamp=300),
            _make_item_dict("Folge 1: Title (S01/E01)", timestamp=100),
            _make_item_dict("Folge 1: Title (S02/E01)", timestamp=200),
        ]
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_make_api_response(items),
        )

        with Mediathek() as m:
            episodes = collect_series(m, "Feuer & Flamme")

        assert [(ep.info.season, ep.info.episode) for ep in episodes] == [
            (1, 1),
            (2, 1),
            (2, 2),
        ]

    @respx.mock
    def test_uses_topic_query(self):
        items = [
            _make_item_dict("Folge 1: Title (S01/E01)"),
        ]
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=_make_api_response(items),
        )

        with Mediathek() as m:
            collect_series(m, "Feuer & Flamme")

        body = json.loads(route.calls.last.request.content)
        assert body["queries"] == [{"fields": ["topic"], "query": "Feuer & Flamme"}]
        assert body["sortBy"] == "timestamp"
        assert body["sortOrder"] == "asc"
