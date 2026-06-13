"""Thin TokenRouter wrapper. Centralizes model routing and structured output so
agents stay declarative.
"""
from __future__ import annotations

import json
import os
import threading
from typing import Any, Type, TypeVar

from pydantic import BaseModel

import config

_T = TypeVar("_T", bound=BaseModel)

_client = None
_client_lock = threading.Lock()


def _api_key() -> str:
    key = os.environ.get("TOKENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise RuntimeError(
            "TOKENROUTER_API_KEY is not set. Copy .env.example to .env and add your "
            "TokenRouter key (the aggregator and recommender need it)."
        )
    return key


def _model() -> str:
    model = os.environ.get("TOKENROUTER_MODEL", config.MODEL)
    mode = os.environ.get("TOKENROUTER_MODE", "quality")
    if ":" in model or model.startswith("auto:"):
        return model
    return f"{model}:{mode}"


def _get_client():
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                from tokenrouter import Tokenrouter  # lazy import for --help without dep

                _client = Tokenrouter(api_key=_api_key(), timeout=120.0)
    return _client


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


def _output_text(resp) -> str:
    parts: list[str] = []
    for msg in resp.output or []:
        for block in msg.content or []:
            if getattr(block, "type", None) == "text" and block.text:
                parts.append(block.text)
    text = "".join(parts).strip()
    if not text:
        raise RuntimeError(f"Model returned no text (status={resp.status})")
    return text


def _create(*, system: str, user: str, max_tokens: int, text: dict | None = None):
    kwargs: dict[str, Any] = {
        "model": _model(),
        "instructions": system,
        "input": user,
        "max_output_tokens": max_tokens,
        "router_provider": os.environ.get("TOKENROUTER_PROVIDER", "anthropic"),
    }
    if text is not None:
        kwargs["text"] = text
    resp = _get_client().responses.create(**kwargs)
    if resp.status == "failed":
        err = resp.error
        msg = err.message if err and err.message else "unknown error"
        raise RuntimeError(f"TokenRouter request failed: {msg}")
    if resp.status == "incomplete":
        raise RuntimeError("Model hit max_output_tokens before completing — raise max_tokens.")
    return resp


def parse(system: str, user: str, schema: Type[_T], max_tokens: int = 8000) -> _T:
    """Structured output: returns a validated instance of `schema`."""
    resp = _create(
        system=system,
        user=user,
        max_tokens=max_tokens,
        text={
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "schema": _strict_json_schema(schema),
                "strict": True,
            },
        },
    )
    raw = _output_text(resp)
    try:
        return schema.model_validate_json(raw)
    except Exception:
        # Some providers wrap JSON in fences despite schema mode.
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
        return schema.model_validate_json(cleaned.strip())


def text(system: str, user: str, max_tokens: int = 1500) -> str:
    """Free-form text (used for short rationales)."""
    return _output_text(_create(system=system, user=user, max_tokens=max_tokens))
