from __future__ import annotations

from grading.pipeline import run_grading_pipeline
from line.message_filter import should_grade_message
from line.reply_helper import send_error_reply, send_grading_reply
from utils.logger import logger


LOG_TEXT_LIMIT = 120


def _is_group_like_source(source: dict | None) -> bool:
    return (source or {}).get("type") in {"group", "room"}


def _log_event(event: dict, action: str, reason: str | None, grading_text: str | None) -> None:
    message = event.get("message", {})
    source = event.get("source", {})
    raw_text = message.get("text") if isinstance(message, dict) else None
    text_preview = None
    if isinstance(raw_text, str):
        text_preview = raw_text.replace("\n", "\\n")[:LOG_TEXT_LIMIT]
    logger.info(
        "LINE event: event_type=%s message_type=%s source_type=%s group_id=%s room_id=%s user_id=%s text=%r action=%s reason=%s grading_text=%r",
        event.get("type"),
        message.get("type") if isinstance(message, dict) else None,
        source.get("type") if isinstance(source, dict) else None,
        source.get("groupId") if isinstance(source, dict) else None,
        source.get("roomId") if isinstance(source, dict) else None,
        source.get("userId") if isinstance(source, dict) else None,
        text_preview,
        action,
        reason,
        grading_text,
    )


def _send_skip_hint(reply_token: str, reason: str | None) -> None:
    if reason == "non-text-message":
        send_error_reply(reply_token, "英文小老師只批改文字訊息，請輸入英文句子")
    elif reason == "empty-text":
        send_error_reply(reply_token, "請輸入英文句子讓我批改 ✍️")
    elif reason == "text-too-long":
        send_error_reply(reply_token, "訊息過長，請輸入少於 1000 字的英文句子")


def handle_event(event: dict) -> None:
    decision = should_grade_message(event)
    _log_event(event, decision.action, decision.reason, decision.text)
    if event.get("type") != "message":
        return

    token = event.get("replyToken")
    if not token:
        logger.warning("missing replyToken")
        return

    if decision.action == "skip":
        if _is_group_like_source(event.get("source")):
            return
        try:
            _send_skip_hint(token, decision.reason)
        except Exception as exc:
            logger.error("fallback reply failed: %s", exc)
        return

    try:
        result = run_grading_pipeline(decision.text or "")
        try:
            send_grading_reply(token, result)
        except Exception as exc:
            logger.error("reply failed after grading: %s", exc)
    except Exception as exc:
        logger.error("message grading failed: %s", exc)
        try:
            send_error_reply(token, "批改時發生錯誤，請稍後再試")
        except Exception as fallback_exc:
            logger.error("fallback reply failed: %s", fallback_exc)
