from __future__ import annotations

import base64
import hashlib
import hmac
import os


def is_valid_line_signature(body: bytes, signature: str | None, secret: str | None = None) -> bool:
    if not signature:
        return False
    channel_secret = secret if secret is not None else os.environ.get("LINE_CHANNEL_SECRET", "")
    digest = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, signature)

