"""Web Unlocker scrape — brightdata/skills `scrape` skill (legacy REST path)."""
from __future__ import annotations

import re

from src.brightdata import client

_BLOCK_MARKERS = (
    "access denied",
    "just a moment",
    "attention required",
    "checking your browser",
    "captcha",
    "cf-browser-verification",
)


def is_blocked(content: str) -> bool:
    """Verification gate from skills/scrape/SKILL.md."""
    if not content or not content.strip():
        return True
    lower = content.lower()
    if any(marker in lower for marker in _BLOCK_MARKERS):
        return True
    if "cloudflare" in lower and len(content) < 2048:
        return True
    return False


def scrape_raw(url: str, *, timeout: int = 60) -> str | None:
    """Fetch a URL through Web Unlocker; None on failure or block page."""
    zone = client.unlocker_zone()
    if not zone:
        return None
    try:
        resp = client.post_request(zone=zone, url=url, fmt="raw", timeout=timeout)
        resp.raise_for_status()
        body = resp.text
    except Exception:
        return None
    return None if is_blocked(body) else body


def excerpt_from_page(body: str, *, max_len: int = 400) -> str:
    """Pull a short quote from HTML/markdown-ish unlocker output."""
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    # Skip boilerplate-y prefixes common on Reddit HTML shells.
    for marker in ("window.", "function ", "{"):
        if text.startswith(marker):
            parts = re.split(r"(?<=[.!?])\s+", text)
            text = next((p for p in parts if len(p) > 40), text)
            break
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"
