"""Thin Anthropic wrapper. Centralizes model, adaptive thinking, and structured
output so agents stay declarative.
"""
from __future__ import annotations

import os
import threading
from typing import Type, TypeVar

from pydantic import BaseModel

import config

_T = TypeVar("_T", bound=BaseModel)

_client = None
_client_lock = threading.Lock()


def _get_client():
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                import anthropic  # imported lazily so --help works without the dep

                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    raise RuntimeError(
                        "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key "
                        "(the aggregator and recommender need it)."
                    )
                _client = anthropic.Anthropic(api_key=api_key)
    return _client


def parse(system: str, user: str, schema: Type[_T], max_tokens: int = 8000) -> _T:
    """Structured output: returns a validated instance of `schema`.

    No thinking here — this is mechanical extraction/normalization, and leaving
    adaptive thinking on can consume the token budget before any JSON is emitted.
    """
    resp = _get_client().messages.parse(
        model=config.MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema,
    )
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("Aggregator hit max_tokens before completing — raise max_tokens.")
    if resp.parsed_output is None:
        raise RuntimeError(f"Model did not return parseable output (stop_reason={resp.stop_reason})")
    return resp.parsed_output


def text(system: str, user: str, max_tokens: int = 1500) -> str:
    """Free-form text (used for short rationales)."""
    resp = _get_client().messages.create(
        model=config.MODEL,
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()
