from __future__ import annotations

from typing import Any, Callable

from config.constants import MAX_TEXT_LENGTH
from grading.pipeline import run_grading_pipeline
from grading.types import GradingResult
from utils.logger import logger
from utils.text import contains_chinese


def invalid_text(message: str) -> tuple[int, dict[str, Any]]:
    return 400, {"error": {"code": "invalid_text", "message": message}}


def grade_text_payload(
    payload: dict[str, Any] | None,
    pipeline: Callable[[str], GradingResult] = run_grading_pipeline,
) -> tuple[int, dict[str, Any]]:
    text = (payload or {}).get("text")
    if not isinstance(text, str):
        return invalid_text("text must be a string")

    trimmed = text.strip()
    if not trimmed:
        return invalid_text("text is required")
    if len(trimmed) > MAX_TEXT_LENGTH:
        return invalid_text("text must be 1000 characters or fewer")
    if contains_chinese(trimmed):
        return invalid_text("only English text is supported")

    try:
        return 200, pipeline(trimmed).to_dict()
    except Exception as exc:
        logger.error("POST /grade failed: %s", exc)
        return 500, {"error": {"code": "grading_failed", "message": "grading failed"}}
