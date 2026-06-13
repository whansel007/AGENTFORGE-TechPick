"""TokenRouter (.com) wrapper — OpenAI-compatible chat completions API."""
from __future__ import annotations

import os
from typing import Any, Type, TypeVar

import requests
from pydantic import BaseModel

import config

_T = TypeVar("_T", bound=BaseModel)

_BASE_URL = os.environ.get("TOKENROUTER_BASE_URL", "https://api.tokenrouter.com").rstrip("/")
_TIMEOUT = 120


def _api_key() -> str:
    key = os.environ.get("TOKENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "TOKENROUTER_API_KEY is not set. Copy .env.example to .env and add your "
            "TokenRouter key from https://tokenrouter.com"
        )
    return key


def _model() -> str:
    return os.environ.get("TOKENROUTER_MODEL", config.MODEL)


def _chat(*, messages: list[dict], max_tokens: int, response_format: dict | None = None) -> str:
    payload: dict[str, Any] = {
        "model": _model(),
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if response_format is not None:
        payload["response_format"] = response_format

    try:
        resp = requests.post(
            f"{_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {_api_key()}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=_TIMEOUT,
        )
    except requests.RequestException as e:
        raise RuntimeError(f"TokenRouter request failed: {e}") from e

    if resp.status_code == 401:
        raise RuntimeError(
            "TokenRouter authentication failed. Check TOKENROUTER_API_KEY in .env "
            f"(from https://tokenrouter.com, not tokenrouter.io)."
        )
    if resp.status_code == 403:
        err = resp.json().get("error", {}).get("message", resp.text)
        raise RuntimeError(
            f"TokenRouter access denied for model '{_model()}': {err}. "
            "Set TOKENROUTER_MODEL to a model your key can access."
        )
    if not resp.ok:
        err = resp.json().get("error", {}).get("message", resp.text) if resp.text else resp.reason
        raise RuntimeError(f"TokenRouter error {resp.status_code}: {err}")

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    if not content or not str(content).strip():
        raise RuntimeError("Model returned empty content.")
    return str(content).strip()


def _strict_json_schema(model: Type[BaseModel]) -> dict[str, Any]:
    schema = model.model_json_schema()
    _apply_strict(schema)
    for defn in schema.get("$defs", {}).values():
        _apply_strict(defn)
    return schema


def _apply_strict(node: Any) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object":
            node["additionalProperties"] = False
            props = node.get("properties")
            if props and "required" not in node:
                node["required"] = list(props.keys())
        for value in node.values():
            _apply_strict(value)
    elif isinstance(node, list):
        for item in node:
            _apply_strict(item)


def parse(system: str, user: str, schema: Type[_T], max_tokens: int = 8000) -> _T:
    """Structured output: returns a validated instance of `schema`."""
    raw = _chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "schema": _strict_json_schema(schema),
                "strict": True,
            },
        },
    )
    try:
        return schema.model_validate_json(raw)
    except Exception:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
        return schema.model_validate_json(cleaned.strip())


def text(system: str, user: str, max_tokens: int = 1500) -> str:
    """Free-form text (used for short rationales)."""
    return _chat(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
    )
