from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from grading.formatter import format_reply
from grading.types import GradingResult


def _reply_message(reply_token: str, text: str, timeout: float = 10.0) -> None:
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("Missing LINE_CHANNEL_ACCESS_TOKEN")

    payload = json.dumps(
        {"replyToken": reply_token, "messages": [{"type": "text", "text": text}]}
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.line.me/v2/bot/message/reply",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout):
        return


def send_grading_reply(reply_token: str, result: GradingResult) -> None:
    _reply_message(reply_token, format_reply(result))


def send_error_reply(reply_token: str, message: str) -> None:
    _reply_message(reply_token, message)
