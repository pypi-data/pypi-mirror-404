from __future__ import annotations

import re
from dataclasses import dataclass

from mediathek_py.client import Mediathek
from mediathek_py.models import Item, QueryField, SortField, SortOrder

_SXX_EXX_RE = re.compile(r"\(S(\d+)/E(\d+)\)")
_FOLGE_RE = re.compile(r"Folge\s+(\d+)")
_MAX_PAGES = 200


@dataclass
class EpisodeInfo:
    season: int
    episode: int


@dataclass
class SeriesEpisode:
    item: Item
    info: EpisodeInfo

    def filename(self) -> str:
        return f"s{self.info.season:02d}e{self.info.episode:02d}.mp4"


def parse_episode_info(title: str) -> EpisodeInfo | None:
    """Extract season and episode from a title string.

    Tries (SXX/EXX) format first, then falls back to 'Folge N' (season defaults to 1).
    Returns None if neither pattern matches.
    """
    m = _SXX_EXX_RE.search(title)
    if m:
        return EpisodeInfo(season=int(m.group(1)), episode=int(m.group(2)))

    m = _FOLGE_RE.search(title)
    if m:
        return EpisodeInfo(season=1, episode=int(m.group(1)))

    return None


def collect_series(
    client: Mediathek, topic: str, page_size: int = 50
) -> list[SeriesEpisode]:
    """Collect all episodes for a topic, paginating through the full result set.

    Returns episodes sorted by (season, episode), deduplicated by (season, episode)
    keeping the earliest-timestamp occurrence (since results are fetched in timestamp
    ascending order).  Items whose titles can't be parsed are skipped.

    Pagination is capped at _MAX_PAGES requests to prevent runaway loops if the API
    returns inconsistent total counts.
    """
    episodes: list[SeriesEpisode] = []
    seen: set[tuple[int, int]] = set()
    offset = 0

    for _ in range(_MAX_PAGES):
        result = (
            client.search()
            .query([QueryField.TOPIC], topic)
            .sort_by(SortField.TIMESTAMP)
            .sort_order(SortOrder.ASCENDING)
            .size(page_size)
            .offset(offset)
            .execute()
        )

        if not result.results:
            break

        for item in result.results:
            info = parse_episode_info(item.title)
            if info is None:
                continue
            key = (info.season, info.episode)
            if key in seen:
                continue
            seen.add(key)
            episodes.append(SeriesEpisode(item=item, info=info))

        offset += page_size
        if offset >= result.query_info.total_results:
            break

    episodes.sort(key=lambda ep: (ep.info.season, ep.info.episode))
    return episodes
