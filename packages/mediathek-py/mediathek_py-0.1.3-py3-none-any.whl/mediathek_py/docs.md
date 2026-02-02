# Noridoc: mediathek_py

Path: @/src/mediathek_py

### Overview

This is the core library package for mediathek-py. It provides a synchronous Python client for the MediathekViewWeb API, Pydantic models for request/response serialization, a custom exception hierarchy, series/episode domain logic, and a Click-based CLI with Rich output. The package exposes two main interfaces: a programmatic fluent-builder API and a prefix-syntax string search API, plus a series collection layer for batch episode downloads.

### How it fits into the larger codebase

This package is the entire production source for mediathek-py. The `__init__.py` re-exports all public symbols from `client`, `models`, `exceptions`, and `series`, making `mediathek_py` the single import target for consumers. The CLI entry point (`mediathek` command) is registered in `pyproject.toml` pointing to `cli:cli`. The test suite at `@/tests` imports directly from this package and mocks the HTTP layer using `respx`.

### Core Implementation

The data flow through the package follows this path:

```
User input (builder API, prefix string, or series topic)
        |
        v
  SearchBuilder  --->  MediathekRequest (Pydantic)
        |                     |
        v                     v
  Mediathek._send_query()  model_dump(by_alias=True, exclude_none=True)
        |                     |
        v                     v
  httpx POST to /api/query  (Content-Type: text/plain, despite JSON body)
        |
        v
  Response JSON  --->  QueryResult (Pydantic, with field_validators)

For series/batch operations, an additional domain layer sits above:

  collect_series(client, topic)
        |
        v
  Paginated SearchBuilder calls (topic query, sorted by timestamp asc)
        |
        v
  parse_episode_info(title) on each Item
        |
        v
  Deduplicated, sorted list[SeriesEpisode]
```

**`client.py`** contains `Mediathek` and `SearchBuilder`. `Mediathek` wraps an `httpx.Client` and handles HTTP communication, the response envelope (`err`/`result`), and file downloads via streaming. `SearchBuilder` is a fluent builder that accumulates query parameters and calls `Mediathek._send_query()` on `.execute()`. The `build_from_string()` method on `Mediathek` parses a prefix-syntax string (e.g., `"!ard #tagesschau >10"`) into a `SearchBuilder` by tokenizing on whitespace and dispatching on the first character (`!`, `#`, `+`, `*`, `>`, `<`). Duration values in the builder API are accepted in minutes and converted to seconds (multiplied by 60) before being placed into the request.

**`models.py`** defines three enums (`QueryField`, `SortField`, `SortOrder`), request models (`Query`, `MediathekRequest`), and response models (`Item`, `QueryInfo`, `QueryResult`). All models use `ConfigDict(populate_by_name=True)` to support both snake_case attribute access and camelCase JSON aliases. `MediathekRequest` serialization uses `by_alias=True, exclude_none=True` so unset optional fields are omitted from the JSON body entirely. The `Item` model uses `field_validator(mode="before")` to handle API quirks: empty strings become `None` for optional fields, `duration` can be an empty string (livestreams), and timestamps accept both int and string representations.

**`exceptions.py`** defines `MediathekError` (base), `ApiError` (carries a `messages: list[str]` from the API `err` array), `DownloadError` (carries `status_code: int` and `url: str`, with a `reason` property that maps HTTP status codes to human-readable messages), and `EmptyResponseError` (when `result` is null without an error). `DownloadError` inherits from `MediathekError`, so existing `except MediathekError` catches remain backward-compatible. The `reason` property is the single source of truth for HTTP-status-to-message mapping (e.g., 403 -> expired/geo-restricted, 404 -> no longer available, 410 -> permanently removed, 429 -> rate limited, 5xx -> server error), falling back to `"HTTP {code}"` for unmapped codes.

**`series.py`** contains the domain logic for series/batch operations, with no HTTP logic of its own. `parse_episode_info(title)` uses two regex patterns to extract season and episode numbers from title strings: `(SXX/EXX)` format is tried first, then `Folge N` as a fallback (which defaults season to 1). `collect_series(client, topic)` paginates through search results by building `SearchBuilder` queries filtered to `[QueryField.TOPIC]`, sorted by timestamp ascending. Pagination is capped at `_MAX_PAGES` (200) requests to prevent unbounded API calls if the API returns inconsistent `total_results` values. It deduplicates episodes by `(season, episode)` tuple using a `seen` set (keeping the earliest-timestamp occurrence, since results arrive in timestamp ascending order), skips items whose titles cannot be parsed, and returns the full list sorted by `(season, episode)`. The `SeriesEpisode` dataclass wraps an `Item` and an `EpisodeInfo` and provides a `filename()` method that generates `sXXeXX.mp4` format strings.

**`cli.py`** provides four Click commands (`search`, `info`, `download`, `batch`) under a `@click.group()`. It uses Rich for output: `Table` for search results and batch preview, `Panel` for detailed info, and `Progress` with download-specific columns for file downloads. Two shared helpers factor out common behavior: `_sanitize_path_component(name)` replaces any character that is not alphanumeric, space, dash, or underscore with an underscore -- used by both `download` (for auto-generated filenames) and `batch` (for topic subdirectory names), ensuring consistent sanitization across all file-system paths; and `_download_progress()` is a factory that returns a preconfigured Rich `Progress` bar, reused by both `download` and `batch`. The `_select_video_url` helper implements a quality fallback chain (e.g., hd -> medium -> low). The `batch` command uses `collect_series()` from `series.py` to gather all episodes for a topic, displays a preview table, optionally filters by season (`--season`/`-s`) and/or episode number (`--episode`/`-e`), prompts for confirmation (skippable with `--yes`), creates a topic-named subdirectory, and downloads episodes sequentially with skip-if-exists logic. The season and episode filters compose sequentially: season filters first, then episode filters the remaining list, so `--season 1 --episode 2` selects only S01E02.

The `batch` command collects failures as `(filename, reason)` tuples, hides failed progress bars (via `progress.update(task_id, visible=False)`), and on completion prints a Rich Table titled "Failed downloads" listing each file with its human-readable reason. The summary line is color-coded: green when all succeed, yellow for partial success, red when all fail. The `download` command catches `DownloadError` before `MediathekError` to display the human-readable `reason` property instead of the raw exception message. Both commands rely on `DownloadError.reason` as the single source of truth for HTTP-status-to-message translation.

### Things to Know

- The API requires `Content-Type: text/plain` even though the body is JSON. This is a documented quirk of the MediathekViewWeb API and is hardcoded in `_send_query()`.
- `model_dump(by_alias=True, exclude_none=True)` on `MediathekRequest` is the serialization invariant -- the API rejects requests containing null-valued optional fields, so they must be omitted entirely.
- The prefix-syntax parser in `build_from_string()` replaces commas with spaces within prefixed tokens (e.g., `#sturm,der,liebe` becomes query `"sturm der liebe"`). Unprefixed tokens are joined with spaces into a single query targeting `[topic, title]` (or all four fields with `search_everywhere=True`).
- The `Item.size` field is `int | None` because the real API returns `null` for some items -- this was discovered during smoke testing and was not in the original plan.
- The download method uses `httpx.Client.stream()` with `iter_bytes()` and supports an optional progress callback that receives `(downloaded_bytes, total_bytes_or_none)`. On HTTP errors, it raises `DownloadError(status_code, url)` rather than a generic `MediathekError`, providing structured error info that the CLI uses for human-readable messages.
- `collect_series()` uses `QueryResult.query_info.total_results` to decide when to stop paginating. It compares the accumulated offset against this value. As a safety net, pagination is also hard-capped at `_MAX_PAGES` (200) iterations to guard against inconsistent API totals.
- `parse_episode_info()` returns `None` for titles that match neither the `(SXX/EXX)` nor `Folge N` patterns (e.g., trailers, specials). These items are silently dropped by `collect_series()`.
- The `batch` CLI command strips a leading `#` from the query argument before passing it as the topic to `collect_series()`, so users can use the same `#topic` prefix syntax as the search command.
- In the batch download loop, the progress callback closure captures `task_id` via a default argument (`_tid=task_id`) to avoid the late-binding closure problem when iterating through episodes.

Created and maintained by Nori.
