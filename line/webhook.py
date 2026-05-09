from __future__ import annotations

from ..utils.logger import logger
from .message_handler import handle_event


def handle_webhook_body(body: dict) -> None:
    for event in body.get("events", []) or []:
        try:
            handle_event(event)
        except Exception as exc:
            logger.error("webhook event failed: %s", exc)

