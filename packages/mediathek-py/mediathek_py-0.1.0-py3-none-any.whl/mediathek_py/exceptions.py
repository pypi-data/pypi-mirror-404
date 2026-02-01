class MediathekError(Exception):
    """Base exception for mediathek-py."""


class ApiError(MediathekError):
    """Raised when the API returns an error response."""

    def __init__(self, messages: list[str]):
        self.messages = messages
        super().__init__("; ".join(messages))


class EmptyResponseError(MediathekError):
    """Raised when the API returns no result and no error."""

    def __init__(self):
        super().__init__("API returned empty response (no result and no error)")
