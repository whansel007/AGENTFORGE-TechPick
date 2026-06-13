"""Scrape-once cache. Research agents are expensive (VideoDB transcripts, Bright
Data scrapes) so we cache their JSON output on disk keyed by product.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"


def _path(key: str) -> Path:
    h = hashlib.sha1(key.encode()).hexdigest()[:16]
    return _CACHE_DIR / f"{h}.json"


def get(key: str):
    p = _path(key)
    if p.exists():
        return json.loads(p.read_text())
    return None


def put(key: str, value) -> None:
    _CACHE_DIR.mkdir(exist_ok=True)
    _path(key).write_text(json.dumps(value, indent=2))
