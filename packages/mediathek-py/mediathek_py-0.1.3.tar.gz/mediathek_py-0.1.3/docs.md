# Noridoc: mediathek-py

Path: @

### Overview

A Python API wrapper and CLI for [MediathekViewWeb](https://mediathekviewweb.de/), the search interface for German public broadcasting media libraries. The project provides both a programmatic library with a fluent builder pattern and a terminal CLI with Rich-formatted output for searching, downloading, and batch-downloading entire series of video content.

### How it fits into the larger codebase

This is the repository root. The project follows a `src/` layout with a single package at `@/src/mediathek_py` and tests at `@/tests`. The build system uses `hatchling` configured in `@/pyproject.toml`, which also registers the `mediathek` CLI entry point. The project depends on `httpx` (HTTP client), `pydantic` (data models), `click` (CLI framework), and `rich` (terminal output). Dev dependencies are `pytest` and `respx`.

### Core Implementation

The project communicates with a single external API endpoint: `POST https://mediathekviewweb.de/api/query`. All search functionality flows through this endpoint. There are two user-facing interfaces, plus a domain layer for series operations:

```
Library API:                          CLI:
  Mediathek.search()                    mediathek search "..."
      -> SearchBuilder                  mediathek info "..."
      -> .execute()                     mediathek download "..."
  Mediathek.search_by_string("...")     mediathek batch "#topic"
      |                                    |
  collect_series(client, topic)            uses Mediathek + series.py
      -> paginated SearchBuilder           |
      -> parse/dedup/sort episodes         |
      |                                    |
      v                                    v
  POST /api/query  <-----------------------+
      |
      v
  QueryResult (Pydantic models)
```

The library API offers two modes: a `SearchBuilder` fluent interface for programmatic construction of queries, and `search_by_string()` which parses a prefix-syntax string (prefixes `!`, `#`, `+`, `*`, `>`, `<` map to channel, topic, title, description, min duration, max duration respectively). The CLI wraps these into `search`, `info`, `download`, and `batch` commands. The `series.py` module provides `collect_series()` and `parse_episode_info()` as a domain logic layer between the HTTP client and the CLI, orchestrating paginated API calls and extracting structured episode data from title strings.

`PROGRESS.md` at the root tracks implementation status and a changelog of significant changes per branch.

### Things to Know

- The MediathekViewWeb API requires `Content-Type: text/plain` despite the body being JSON. This is a known API quirk documented in the implementation plan.
- Duration values at the user-facing layer (builder API and CLI prefix syntax) are in **minutes**, but the API expects **seconds**. The conversion happens in `SearchBuilder.duration_min()` / `duration_max()`.
- The API response envelope uses `{"err": [...], "result": {...}}`. When `err` is non-null, the client raises `ApiError`. When both `err` is null and `result` is null, it raises `EmptyResponseError`. File download HTTP failures raise `DownloadError` (which carries `status_code` and `url`, and provides a `reason` property mapping codes to human-readable messages). All three inherit from `MediathekError`.
- Optional fields in the request body must be **omitted** (not sent as null) -- enforced by Pydantic's `exclude_none=True` serialization.
- Several API response fields have type ambiguities (empty strings for None, string-encoded integers for timestamps, string-encoded floats for timing) which are handled by Pydantic `field_validator(mode="before")` in the `Item` and `QueryInfo` models.

Created and maintained by Nori.
