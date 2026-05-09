from __future__ import annotations


class NlpApiError(Exception):
    pass


class LlmApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LlmParseError(Exception):
    def __init__(self, message: str, raw_content: str | None = None) -> None:
        super().__init__(message)
        self.raw_content = raw_content
