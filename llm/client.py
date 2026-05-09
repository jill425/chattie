from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from config.constants import LLM_MAX_TOKENS, LLM_MODEL
from llm.prompt import LlmPrompt
from utils.errors import LlmApiError


@dataclass(frozen=True)
class LlmResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int


def call_llm(prompt: LlmPrompt, timeout: float = 30.0) -> LlmResponse:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LlmApiError("Missing ANTHROPIC_API_KEY")

    payload = json.dumps(
        {
            "model": LLM_MODEL,
            "max_tokens": LLM_MAX_TOKENS,
            "system": prompt.system,
            "messages": [{"role": "user", "content": prompt.user_message}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise LlmApiError(f"Anthropic API error: {exc.code}", exc.code) from exc
    except urllib.error.URLError as exc:
        raise LlmApiError(f"Network error: {exc.reason}") from exc

    data = json.loads(raw)
    text_block = next((block for block in data.get("content", []) if block.get("type") == "text"), None)
    if not text_block:
        raise LlmApiError("LLM returned no text content")
    usage = data.get("usage", {})
    return LlmResponse(
        content=str(text_block.get("text", "")),
        model=str(data.get("model", "")),
        input_tokens=int(usage.get("input_tokens", 0)),
        output_tokens=int(usage.get("output_tokens", 0)),
    )
