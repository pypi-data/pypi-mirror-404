import pytest


@pytest.fixture()
def sample_response():
    """Complete realistic API success response."""
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
                    "description": "Aktuelle Nachrichten aus aller Welt",
                    "timestamp": 1696269600,
                    "duration": 932,
                    "size": 137363456,
                    "url_website": "https://www.ardmediathek.de/video/1",
                    "url_subtitle": "",
                    "url_video": "https://media.tagesschau.de/video/medium.mp4",
                    "url_video_low": "https://media.tagesschau.de/video/low.mp4",
                    "url_video_hd": "https://media.tagesschau.de/video/hd.mp4",
                    "filmlisteTimestamp": "1696339020",
                    "id": "DCeoosOJEZLg30zx2pxtMQPBv4oBQnc+XEZf6LHOtC0=",
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
                    "url_subtitle": "https://www.zdf.de/subtitle/2.xml",
                    "url_video": "https://media.zdf.de/video/medium.mp4",
                    "url_video_low": "",
                    "url_video_hd": "",
                    "filmlisteTimestamp": "1696339020",
                    "id": "ABCdef123456789=",
                },
            ],
        },
    }


@pytest.fixture()
def sample_error_response():
    """API error response."""
    return {"err": ["query too short"], "result": None}


@pytest.fixture()
def sample_empty_response():
    """API empty response (no results, no error)."""
    return {"err": None, "result": None}


@pytest.fixture()
def sample_item_livestream():
    """Item dict with empty duration (livestream)."""
    return {
        "channel": "ARD",
        "topic": "Livestream",
        "title": "ARD Livestream",
        "description": "",
        "timestamp": 1696269600,
        "duration": "",
        "size": 0,
        "url_website": "https://www.ardmediathek.de/live",
        "url_subtitle": "",
        "url_video": "https://media.tagesschau.de/live.m3u8",
        "url_video_low": "",
        "url_video_hd": "",
        "filmlisteTimestamp": "1696339020",
        "id": "LIVE123=",
    }
