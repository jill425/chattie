from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Env:
    line_channel_secret: str
    line_channel_access_token: str
    anthropic_api_key: str
    port: int
    llm_enabled: bool
    log_level: str
    languagetool_api_url: str


def parse_bool(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return value.lower() != "false"


def parse_port(value: str | None) -> int:
    if value is None or value == "":
        return 3000
    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError("Invalid env var: PORT") from exc
    if port <= 0 or port > 65535:
        raise ValueError("Invalid env var: PORT")
    return port


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing env var: {name}")
    return value


def load_env(require_credentials: bool = True) -> Env:
    get_required = require_env if require_credentials else lambda name: os.environ.get(name, "")
    return Env(
        line_channel_secret=get_required("LINE_CHANNEL_SECRET"),
        line_channel_access_token=get_required("LINE_CHANNEL_ACCESS_TOKEN"),
        anthropic_api_key=get_required("ANTHROPIC_API_KEY"),
        port=parse_port(os.environ.get("PORT")),
        llm_enabled=parse_bool(os.environ.get("LLM_ENABLED"), True),
        log_level=os.environ.get("LOG_LEVEL", "info"),
        languagetool_api_url=os.environ.get(
            "LANGUAGETOOL_API_URL", "https://api.languagetool.org"
        ),
    )

