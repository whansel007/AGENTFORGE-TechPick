"""Bright Data client helpers.

Implements the REST patterns from brightdata/skills (search + scrape) and
ScrapeAlchemist/brightdata-hack-pack when the `bdata` CLI isn't available in
the Python pipeline runtime.
"""
from __future__ import annotations

import os

import requests

_ENDPOINT = "https://api.brightdata.com/request"


def api_key() -> str | None:
    return os.environ.get("BRIGHTDATA_API_KEY", "").strip() or None


def serp_zone() -> str:
    """SERP zone — skills prefer BRIGHTDATA_SERP_ZONE, we keep BRIGHTDATA_ZONE alias."""
    return (
        os.environ.get("BRIGHTDATA_SERP_ZONE", "").strip()
        or os.environ.get("BRIGHTDATA_ZONE", "").strip()
        or "serp_api"
    )


def unlocker_zone() -> str | None:
    zone = os.environ.get("BRIGHTDATA_UNLOCKER_ZONE", "").strip()
    return zone or None


def post_request(*, zone: str, url: str, fmt: str = "raw", timeout: int = 90) -> requests.Response:
    key = api_key()
    if not key:
        raise RuntimeError("BRIGHTDATA_API_KEY is not set")

    return requests.post(
        _ENDPOINT,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json={"zone": zone, "url": url, "format": fmt},
        timeout=timeout,
    )
