"""Small Ollama chat client for local reviewer agents."""

from __future__ import annotations

import json
from typing import Any

import requests


OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"


def _parse_message_content(content: str) -> Any:
    """Parse a model message as JSON when possible."""

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_content": content}


def call_ollama_chat(
    model: str,
    messages: list[dict],
    temperature: float = 0.2,
    format_schema: dict | None = None,
) -> dict:
    """Call Ollama's local chat API and return parsed response content.

    When ``format_schema`` is provided, it is passed through Ollama's ``format``
    field for structured outputs.
    """

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if format_schema is not None:
        payload["format"] = format_schema

    try:
        response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=180)
    except requests.ConnectionError as exc:
        raise RuntimeError(
            "Could not connect to Ollama at http://localhost:11434. "
            "Start it with: ollama serve"
        ) from exc
    except requests.Timeout as exc:
        raise RuntimeError(
            f"Ollama request timed out while running model '{model}'. "
            "Try a smaller model or increase the timeout."
        ) from exc

    if response.status_code == 404:
        raise RuntimeError(
            f"Ollama model '{model}' was not found. "
            f"Install it with: ollama pull {model}"
        )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Ollama request failed with HTTP {response.status_code}: "
            f"{response.text[:1000]}"
        )

    data = response.json()
    content = data.get("message", {}).get("content", "")
    parsed_content = _parse_message_content(content)

    return {
        "model": model,
        "parsed": parsed_content,
        "raw": data,
    }

