import json

import respx
from click.testing import CliRunner

from mediathek_py.cli import cli


BASE_URL = "https://mediathekviewweb.de"


def _mock_search_response():
    """Return a realistic search response for CLI tests."""
    return {
        "err": None,
        "result": {
            "queryInfo": {
                "filmlisteTimestamp": 1696361700,
                "resultCount": 2,
                "searchEngineTime": "4.39",
                "totalResults": 61,
            },
            "results": [
                {
                    "channel": "ARD",
                    "topic": "tagesschau",
                    "title": "tagesschau 20:00 Uhr",
                    "description": "Aktuelle Nachrichten",
                    "timestamp": 1696269600,
                    "duration": 932,
                    "size": 137363456,
                    "url_website": "https://www.ardmediathek.de/video/1",
                    "url_subtitle": "",
                    "url_video": "https://media.tagesschau.de/video/medium.mp4",
                    "url_video_low": "https://media.tagesschau.de/video/low.mp4",
                    "url_video_hd": "https://media.tagesschau.de/video/hd.mp4",
                    "filmlisteTimestamp": "1696339020",
                    "id": "abc123=",
                },
                {
                    "channel": "ZDF",
                    "topic": "heute",
                    "title": "heute 19:00 Uhr",
                    "description": "",
                    "timestamp": 1696269000,
                    "duration": 845,
                    "size": 98765432,
                    "url_website": "https://www.zdf.de/video/2",
                    "url_subtitle": "",
                    "url_video": "https://media.zdf.de/video/medium.mp4",
                    "url_video_low": "",
                    "url_video_hd": "",
                    "filmlisteTimestamp": "1696339020",
                    "id": "def456=",
                },
            ],
        },
    }


class TestSearchCommand:
    @respx.mock
    def test_displays_results(self):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_search_response(),
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "tagesschau"])

        assert result.exit_code == 0
        assert "ARD" in result.output
        assert "tagesschau" in result.output
        assert "ZDF" in result.output

    @respx.mock
    def test_with_options(self):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_search_response(),
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "search",
                "tagesschau",
                "--sort-by", "timestamp",
                "--sort-order", "desc",
                "--size", "5",
            ],
        )

        assert result.exit_code == 0
        body = json.loads(route.calls.last.request.content)
        assert body["sortBy"] == "timestamp"
        assert body["sortOrder"] == "desc"
        assert body["size"] == 5

    @respx.mock
    def test_everywhere_flag(self):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_search_response(),
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "tagesschau", "--everywhere"])

        assert result.exit_code == 0
        body = json.loads(route.calls.last.request.content)
        # Unprefixed tokens with --everywhere should search all fields
        found = any(
            q["fields"] == ["channel", "topic", "title", "description"]
            for q in body["queries"]
        )
        assert found

    @respx.mock
    def test_future_flag(self):
        route = respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_search_response(),
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "tagesschau", "--future"])

        assert result.exit_code == 0
        body = json.loads(route.calls.last.request.content)
        assert body["future"] is True

    @respx.mock
    def test_api_error(self):
        respx.post(f"{BASE_URL}/api/query").respond(
            json={"err": ["query too short"], "result": None},
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "x"])

        assert result.exit_code == 1
        assert "error" in result.output.lower()


class TestInfoCommand:
    @respx.mock
    def test_displays_detail(self):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_search_response(),
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["info", "tagesschau"])

        assert result.exit_code == 0
        assert "tagesschau 20:00 Uhr" in result.output
        assert "ARD" in result.output
        assert "https://media.tagesschau.de/video/medium.mp4" in result.output


class TestDownloadCommand:
    @respx.mock
    def test_basic(self, tmp_path):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_search_response(),
        )
        video_content = b"fake video bytes " * 50
        respx.get("https://media.tagesschau.de/video/hd.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )

        output_file = tmp_path / "test.mp4"
        runner = CliRunner()
        result = runner.invoke(
            cli, ["download", "tagesschau", "-o", str(output_file)]
        )

        assert result.exit_code == 0
        assert output_file.exists()

    @respx.mock
    def test_quality_option(self, tmp_path):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_search_response(),
        )
        video_content = b"low quality video " * 50
        respx.get("https://media.tagesschau.de/video/low.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )

        output_file = tmp_path / "test_low.mp4"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["download", "tagesschau", "--quality", "low", "-o", str(output_file)],
        )

        assert result.exit_code == 0
        assert output_file.exists()


def _mock_batch_response(total_results=None):
    """Return a series response with episode-style titles for batch CLI tests."""
    items = [
        {
            "channel": "WDR",
            "topic": "Feuer & Flamme",
            "title": "Folge 1: Feuer & Flamme (S01/E01)",
            "description": "",
            "timestamp": 1606420800,
            "duration": 2597,
            "size": 137363456,
            "url_website": "https://www.ardmediathek.de/video/1",
            "url_subtitle": "",
            "url_video": "https://media.example.de/s01e01/medium.mp4",
            "url_video_low": "https://media.example.de/s01e01/low.mp4",
            "url_video_hd": "https://media.example.de/s01e01/hd.mp4",
            "filmlisteTimestamp": "1696339020",
            "id": "ep-s01e01=",
        },
        {
            "channel": "WDR",
            "topic": "Feuer & Flamme",
            "title": "Folge 2: Feuer & Flamme (S01/E02)",
            "description": "",
            "timestamp": 1607025600,
            "duration": 2612,
            "size": 137363456,
            "url_website": "https://www.ardmediathek.de/video/2",
            "url_subtitle": "",
            "url_video": "https://media.example.de/s01e02/medium.mp4",
            "url_video_low": "https://media.example.de/s01e02/low.mp4",
            "url_video_hd": "https://media.example.de/s01e02/hd.mp4",
            "filmlisteTimestamp": "1696339020",
            "id": "ep-s01e02=",
        },
        {
            "channel": "WDR",
            "topic": "Feuer & Flamme",
            "title": "Folge 1: Wohnungsbrand (S02/E01)",
            "description": "",
            "timestamp": 1673291700,
            "duration": 2605,
            "size": 137363456,
            "url_website": "https://www.ardmediathek.de/video/3",
            "url_subtitle": "",
            "url_video": "https://media.example.de/s02e01/medium.mp4",
            "url_video_low": "https://media.example.de/s02e01/low.mp4",
            "url_video_hd": "https://media.example.de/s02e01/hd.mp4",
            "filmlisteTimestamp": "1696339020",
            "id": "ep-s02e01=",
        },
    ]
    return {
        "err": None,
        "result": {
            "queryInfo": {
                "filmlisteTimestamp": 1696361700,
                "resultCount": len(items),
                "searchEngineTime": "1.23",
                "totalResults": total_results if total_results is not None else len(items),
            },
            "results": items,
        },
    }


class TestBatchCommand:
    @respx.mock
    def test_displays_preview(self):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_batch_response(),
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "#Feuer & Flamme"], input="n\n")

        assert result.exit_code == 0
        assert "S01" in result.output or "s01" in result.output.lower()
        assert "3 episodes" in result.output.lower() or "3 episode" in result.output.lower()

    @respx.mock
    def test_season_filter(self):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_batch_response(),
        )

        runner = CliRunner()
        result = runner.invoke(
            cli, ["batch", "#Feuer & Flamme", "--season", "1"], input="n\n"
        )

        assert result.exit_code == 0
        # Should show only S01 episodes (2 of them), not S02
        assert "2 episode" in result.output.lower()

    @respx.mock
    def test_downloads_with_yes_flag(self, tmp_path):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_batch_response(),
        )
        video_content = b"fake video " * 50
        respx.get("https://media.example.de/s01e01/hd.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )
        respx.get("https://media.example.de/s01e02/hd.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )
        respx.get("https://media.example.de/s02e01/hd.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["batch", "#Feuer & Flamme", "--yes", "-o", str(tmp_path)],
        )

        assert result.exit_code == 0
        topic_dir = tmp_path / "Feuer _ Flamme"
        assert (topic_dir / "s01e01.mp4").exists()
        assert (topic_dir / "s01e02.mp4").exists()
        assert (topic_dir / "s02e01.mp4").exists()

    @respx.mock
    def test_skips_existing_files(self, tmp_path):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_batch_response(),
        )
        video_content = b"fake video " * 50
        respx.get("https://media.example.de/s01e02/hd.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )
        respx.get("https://media.example.de/s02e01/hd.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )

        # Pre-create one file so it gets skipped
        topic_dir = tmp_path / "Feuer _ Flamme"
        topic_dir.mkdir()
        existing = topic_dir / "s01e01.mp4"
        existing.write_bytes(b"already here")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "batch", "#Feuer & Flamme",
                "--yes", "-o", str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        # The existing file should NOT be overwritten
        assert existing.read_bytes() == b"already here"
        # Other files should be downloaded
        assert (topic_dir / "s01e02.mp4").exists()
        assert (topic_dir / "s02e01.mp4").exists()

    @respx.mock
    def test_empty_results_error(self):
        respx.post(f"{BASE_URL}/api/query").respond(
            json={
                "err": None,
                "result": {
                    "queryInfo": {
                        "filmlisteTimestamp": 1696361700,
                        "resultCount": 0,
                        "searchEngineTime": "0.5",
                        "totalResults": 0,
                    },
                    "results": [],
                },
            },
        )

        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "#nonexistent"])

        assert result.exit_code == 1
        assert "no episodes" in result.output.lower() or "error" in result.output.lower()

    @respx.mock
    def test_no_parseable_episodes(self):
        response = {
            "err": None,
            "result": {
                "queryInfo": {
                    "filmlisteTimestamp": 1696361700,
                    "resultCount": 1,
                    "searchEngineTime": "1.0",
                    "totalResults": 1,
                },
                "results": [
                    {
                        "channel": "WDR",
                        "topic": "Feuer & Flamme",
                        "title": "Trailer: Feuer & Flamme",
                        "description": "",
                        "timestamp": 1696269600,
                        "duration": 120,
                        "size": 5000000,
                        "url_website": "https://example.de",
                        "url_subtitle": "",
                        "url_video": "https://media.example.de/trailer.mp4",
                        "url_video_low": "",
                        "url_video_hd": "",
                        "filmlisteTimestamp": "1696339020",
                        "id": "trailer1=",
                    },
                ],
            },
        }
        respx.post(f"{BASE_URL}/api/query").respond(json=response)

        runner = CliRunner()
        result = runner.invoke(cli, ["batch", "#Feuer & Flamme"])

        assert result.exit_code == 1
        assert "no episodes" in result.output.lower() or "error" in result.output.lower()

    @respx.mock
    def test_quality_option_selects_correct_url(self, tmp_path):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_batch_response(),
        )
        video_content = b"low quality video " * 50
        respx.get("https://media.example.de/s01e01/low.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )
        respx.get("https://media.example.de/s01e02/low.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )
        respx.get("https://media.example.de/s02e01/low.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["batch", "#Feuer & Flamme", "--yes", "--quality", "low", "-o", str(tmp_path)],
        )

        assert result.exit_code == 0
        topic_dir = tmp_path / "Feuer _ Flamme"
        assert (topic_dir / "s01e01.mp4").exists()
        assert (topic_dir / "s01e02.mp4").exists()
        assert (topic_dir / "s02e01.mp4").exists()

    @respx.mock
    def test_continues_after_download_failure(self, tmp_path):
        respx.post(f"{BASE_URL}/api/query").respond(
            json=_mock_batch_response(),
        )
        video_content = b"fake video " * 50
        respx.get("https://media.example.de/s01e01/hd.mp4").respond(status_code=500)
        respx.get("https://media.example.de/s01e02/hd.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )
        respx.get("https://media.example.de/s02e01/hd.mp4").respond(
            content=video_content,
            headers={"content-length": str(len(video_content))},
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["batch", "#Feuer & Flamme", "--yes", "-o", str(tmp_path)],
        )

        assert result.exit_code == 0
        topic_dir = tmp_path / "Feuer _ Flamme"
        assert not (topic_dir / "s01e01.mp4").exists()
        assert (topic_dir / "s01e02.mp4").exists()
        assert (topic_dir / "s02e01.mp4").exists()
        assert "2 downloaded" in result.output
        assert "1 failed" in result.output
