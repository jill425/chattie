from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from utils.errors import LlmParseError


@dataclass(frozen=True)
class ParsedResponse:
    suggestion: str
    tips: str


def _try_parse_object(content: str) -> dict[str, Any] | None:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def parse_response(content: str | dict[str, Any]) -> ParsedResponse:
    raw_content = content.get("content", "") if isinstance(content, dict) else content
    parsed = _try_parse_object(raw_content.strip())
    if parsed is None:
        match = re.search(r"\{[\s\S]*\}", raw_content)
        if match:
            parsed = _try_parse_object(match.group(0))

    if parsed is None:
        raise LlmParseError("Failed to parse LLM response: invalid JSON", raw_content)

    return ParsedResponse(
        suggestion="" if "suggestion" not in parsed else str(parsed["suggestion"]),
        tips="" if "tips" not in parsed else str(parsed["tips"]),
    )
