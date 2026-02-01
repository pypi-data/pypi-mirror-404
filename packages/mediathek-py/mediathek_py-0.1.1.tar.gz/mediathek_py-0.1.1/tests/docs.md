# Noridoc: tests

Path: @/tests

### Overview

The test suite for mediathek-py, using pytest with `respx` for HTTP mocking. Tests verify real Pydantic parsing behavior against realistic API payloads, client request construction and response handling through mocked HTTP, series episode parsing and collection logic, and end-to-end CLI command behavior (including batch downloads) using Click's `CliRunner`.

### How it fits into the larger codebase

The tests import from `@/src/mediathek_py` and validate all four layers of the package: models, client, series domain logic, and CLI. HTTP interactions are mocked at the transport level using `respx`, so tests verify actual serialization/deserialization, request building, and error handling without hitting the real MediathekViewWeb API. The test directory is configured as the `testpaths` in `@/pyproject.toml`.

### Core Implementation

**`conftest.py`** provides shared pytest fixtures that represent realistic API JSON payloads: a successful response with two items (including edge cases like empty-string fields and string-encoded timestamps), an error response, an empty response, and a livestream item with empty-string duration. These fixtures are used by both model and client tests.

**`test_models.py`** validates Pydantic model behavior: parsing complete items, empty-string-to-None coercion, livestream duration handling, string-to-int timestamp coercion, camelCase alias resolution on `QueryInfo`, full `QueryResult` parsing, `MediathekRequest` alias serialization, None-field omission, and enum value correctness.

**`test_client.py`** uses `respx` to intercept HTTP calls and verifies: correct request structure (Content-Type, User-Agent, JSON body shape), the fluent builder API (multiple queries, duration filters, sort/pagination, future flag), the prefix-syntax string parser (all prefix types including `!`, `#`, `+`, `*`, `>`, `<`, comma replacement, unprefixed defaults, everywhere mode, mixed queries), error handling (`ApiError`, `EmptyResponseError`, HTTP errors), context manager behavior, and file download with content verification.

**`test_series.py`** tests the series domain logic in three groups: `TestParseEpisodeInfo` validates regex extraction of season/episode from various title formats (standard `(SXX/EXX)`, `Folge N` fallback, precedence when both are present, and `None` returns for non-matching titles like trailers). `TestSeriesEpisode` validates the `filename()` method's zero-padded `sXXeXX.mp4` output. `TestCollectSeries` uses `respx` to mock paginated API responses and verifies single-page collection, multi-page pagination (checking request offset values), filtering of unparseable items, deduplication by `(season, episode)`, sorting order, and correct query construction (topic field, timestamp sort, ascending order).

**`test_cli.py`** uses `CliRunner` with `respx` mocking to test the CLI commands end-to-end: search output formatting, CLI option pass-through to API requests (sort, size, everywhere, future flags), error display, info panel rendering, download with quality selection, and batch operations. The batch tests (`TestBatchCommand`) validate preview table display, season filtering, downloads with the `--yes` flag (verifying file creation in topic subdirectories), skip-if-exists behavior (pre-creating a file and verifying it is not overwritten), error cases for empty results and unparseable episodes, quality option pass-through in batch mode (verifying the correct URL tier is downloaded), and resilience to individual download failures (one episode returning HTTP 500 while the batch continues and reports correct counts). Download and batch tests use `tmp_path` to verify actual file creation. Batch tests expect sanitized directory names (e.g., `"Feuer & Flamme"` becomes `"Feuer _ Flamme"`) consistent with `_sanitize_path_component()` in `cli.py`.

### Things to Know

- The CLI tests define their own `_mock_search_response()` function rather than using conftest fixtures, because `CliRunner` invocations do not directly accept fixture-injected data into the mocked routes. The response structure mirrors conftest's `sample_response` but is independent. Similarly, the batch tests define `_mock_batch_response()` with episode-style titles containing `(SXX/EXX)` patterns.
- The series tests (`test_series.py`) define their own `_make_item_dict()` and `_make_api_response()` helpers to construct realistic API payloads with episode-style titles. These are independent from conftest fixtures and from the CLI test helpers.
- All client, series, and CLI tests use `@respx.mock` as a decorator to activate HTTP mocking. The mock intercepts `httpx` calls at the transport level, which means tests exercise the full `httpx.Client` request/response cycle.
- Download and batch tests use pytest's `tmp_path` fixture and verify file existence. The batch skip-if-exists test pre-creates a file and asserts its content is not overwritten.
- The series pagination test uses `route.side_effect` with a list of `respx.MockResponse` objects to return different responses for successive API calls, and verifies the offset values in each request body.

Created and maintained by Nori.
