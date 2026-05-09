from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ..utils.errors import NlpApiError


def _normalize_api_url(api_url: str) -> str:
    return api_url.rstrip("/").removesuffix("/v2")


def check_grammar(text: str, timeout: float = 10.0) -> dict[str, Any]:
    api_url = _normalize_api_url(
        os.environ.get("LANGUAGETOOL_API_URL", "https://api.languagetool.org")
    )
    body = urllib.parse.urlencode({"text": text, "language": "en-AU"}).encode()
    request = urllib.request.Request(
        f"{api_url}/v2/check",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise NlpApiError(f"LanguageTool API error: {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise NlpApiError(f"Network error: {exc.reason}") from exc

    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise NlpApiError("Invalid response from LanguageTool") from exc

