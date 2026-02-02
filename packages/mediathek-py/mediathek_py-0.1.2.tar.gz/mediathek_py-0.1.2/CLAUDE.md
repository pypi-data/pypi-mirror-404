# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python API wrapper and CLI for [MediathekViewWeb](https://mediathekviewweb.de/), a search interface for German public broadcasting media libraries. Provides both a fluent builder API and a Click CLI with Rich output.

**This project uses the `uv` package manager** for dependency management and Python environment handling.

## Commands

```bash
# Install (editable, with dev deps)
uv sync

# Run all tests
uv run pytest

# Run a single test file or test
uv run pytest tests/test_client.py
uv run pytest tests/test_client.py::TestSearchBuilder::test_sends_correct_request -v

# Run CLI
uv run mediathek search "!ard #tagesschau"
uv run mediathek info "#tagesschau"
uv run mediathek download "#tagesschau"
uv run mediathek batch "#Feuer & Flamme" --season 3 --quality hd -o ./downloads/

```

### Work with beads work management tool. Read ./.beads/README.md file for more information

```bash
# Create new issues
bd create "Add user authentication"

# View all issues
bd list

# View issue details
bd show <issue-id>

# Update issue status
bd update <issue-id> --status in_progress
bd update <issue-id> --status done

# Sync with git remote
bd sync
```

## Architecture

Single package at `src/mediathek_py/` with five modules:

- **`client.py`** — `Mediathek` (HTTP client wrapping httpx) and `SearchBuilder` (fluent builder). `Mediathek` also contains `build_from_string()` which parses prefix syntax (`!channel #topic +title *description >min_dur <max_dur`) into a `SearchBuilder`.
- **`models.py`** — Pydantic models for request (`MediathekRequest`, `Query`) and response (`QueryResult`, `QueryInfo`, `Item`). Uses `Field(alias=...)` for camelCase JSON mapping and `field_validator(mode="before")` to handle API quirks (empty strings → None, string-encoded numbers).
- **`series.py`** — Domain logic for batch/series operations: `parse_episode_info()` extracts season/episode from titles via regex (`(SXX/EXX)` and `Folge N` patterns), `collect_series()` paginates through all API results for a topic and returns deduplicated, sorted `SeriesEpisode` objects.
- **`exceptions.py`** — Three-level hierarchy: `MediathekError` → `ApiError` (carries error messages list) / `EmptyResponseError`.
- **`cli.py`** — Click command group (`search`, `info`, `download`, `batch`) with Rich tables/panels/progress bars.

All public symbols are re-exported from `__init__.py`.

## Key API Quirks

These are non-obvious behaviors that affect how code must be written:

- The MediathekViewWeb API requires `Content-Type: text/plain` despite sending JSON.
- Optional request fields must be **omitted entirely** (not null) — enforced via `model_dump(by_alias=True, exclude_none=True)`.
- Duration values in the builder API are **minutes** but the API expects **seconds** — conversion (`* 60`) happens in `SearchBuilder.duration_min()`/`duration_max()`.
- Response fields have type ambiguities: empty strings for None, string-encoded integers for timestamps, string-encoded floats for timing. All handled by Pydantic validators on `Item` and `QueryInfo`.

## Testing

Tests use `pytest` with `respx` for HTTP mocking at the transport level (no real network calls). CLI tests use Click's `CliRunner`. Test fixtures in `conftest.py` provide realistic API payloads with edge cases. CLI tests define their own mock responses independently from conftest. All tests are run using `uv run pytest`.
