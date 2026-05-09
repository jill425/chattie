from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from ..config.constants import MAX_TEXT_LENGTH
from ..utils.text import contains_chinese

GROUP_COMMAND_PATTERN = re.compile(r"^/(?:check|grade|fix)\s+(.+)", re.I)
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.I)
ENGLISH_WORD_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


@dataclass(frozen=True)
class MessageFilterDecision:
    action: Literal["grade", "skip"]
    text: str | None = None
    reason: str | None = None


def _is_group_like_source(source: dict | None) -> bool:
    return (source or {}).get("type") in {"group", "room"}


def _is_mostly_url(text: str) -> bool:
    urls = URL_PATTERN.findall(text)
    if not urls:
        return False
    return sum(len(url) for url in urls) / len(text) > 0.5


def _is_noise_text(text: str) -> bool:
    letters = re.findall(r"[A-Za-z]", text)
    words = ENGLISH_WORD_PATTERN.findall(text)
    if len(letters) < 3:
        return True
    if len(words) < 2:
        return True
    return bool(re.fullmatch(r"[\W\d_]+", text))


def _extract_group_command_text(text: str) -> str | None:
    match = GROUP_COMMAND_PATTERN.match(text)
    return match.group(1).strip() if match and match.group(1).strip() else None


def _validate_text(text: str) -> str | None:
    if not text:
        return "empty-text"
    if len(text) > MAX_TEXT_LENGTH:
        return "text-too-long"
    if contains_chinese(text):
        return "contains-chinese"
    if _is_mostly_url(text):
        return "url-like-text"
    if _is_noise_text(text):
        return "noise-text"
    return None


def should_grade_message(event: dict) -> MessageFilterDecision:
    if event.get("type") != "message":
        return MessageFilterDecision("skip", reason="non-message-event")

    message = event.get("message", {})
    if message.get("type") != "text":
        return MessageFilterDecision("skip", reason="non-text-message")

    text = str(message.get("text", "")).strip()
    reason = _validate_text(text)
    if reason:
        return MessageFilterDecision("skip", reason=reason)

    if _is_group_like_source(event.get("source")):
        command_text = _extract_group_command_text(text)
        if not command_text:
            return MessageFilterDecision("skip", reason="missing-group-trigger")
        reason = _validate_text(command_text)
        if reason:
            return MessageFilterDecision("skip", reason=reason)
        return MessageFilterDecision("grade", text=command_text)

    return MessageFilterDecision("grade", text=text)

