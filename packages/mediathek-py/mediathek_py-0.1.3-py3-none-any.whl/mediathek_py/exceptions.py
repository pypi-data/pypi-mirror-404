class MediathekError(Exception):
    """Base exception for mediathek-py."""


class ApiError(MediathekError):
    """Raised when the API returns an error response."""

    def __init__(self, messages: list[str]):
        self.messages = messages
        super().__init__("; ".join(messages))


class DownloadError(MediathekError):
    """Raised when a file download fails."""

    _REASONS: dict[int, str] = {
        403: "Access denied — content may have expired or is geo-restricted",
        404: "File not found — content is no longer available",
        410: "Content has been permanently removed",
        429: "Rate limited — too many requests, try again later",
        500: "Server error — try again later",
        502: "Server error — try again later",
        503: "Server temporarily unavailable — try again later",
    }

    def __init__(self, status_code: int, url: str):
        self.status_code = status_code
        self.url = url
        super().__init__(self.reason)

    @property
    def reason(self) -> str:
        return self._REASONS.get(
            self.status_code, f"HTTP {self.status_code}"
        )


class EmptyResponseError(MediathekError):
    """Raised when the API returns no result and no error."""

    def __init__(self):
        super().__init__("API returned empty response (no result and no error)")
