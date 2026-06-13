"""Bright Data research agent — discover Reddit discussion of each product via the
Bright Data SERP API (a Google `site:reddit.com` query), and turn each organic
result into a Reddit-sourced EvidenceItem (thread URL + snippet).

Needs BRIGHTDATA_API_KEY and a BRIGHTDATA_ZONE (your SERP/Unlocker zone name from
the dashboard). If either is missing or the call fails, falls back to mock so the
pipeline never hard-stops.

Deeper comment scraping (Web Unlocker on each thread URL) is a natural extension;
the SERP snippet is already a real Reddit-sourced excerpt, enough for the MVP.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse

from src import cache
from src.mockdata import mock_reddit_evidence
from src.schemas import EvidenceItem

_ENDPOINT = "https://api.brightdata.com/request"
_SUBREDDIT_RE = re.compile(r"reddit\.com/r/([A-Za-z0-9_]+)")


def gather(product: dict, limits: dict) -> list[EvidenceItem]:
    key = f"brightdata::{product['name']}"
    cached = cache.get(key)
    if cached is not None:
        return [EvidenceItem(**e) for e in cached]

    if os.environ.get("BRIGHTDATA_API_KEY"):
        try:
            items = _gather_live(product, limits)
        except Exception as e:  # noqa: BLE001 — never let one source kill the run
            print(f"  [brightdata] live fetch failed for {product['name']} ({e}); using mock")
            items = mock_reddit_evidence(product["name"])
    else:
        items = mock_reddit_evidence(product["name"])

    cache.put(key, [i.model_dump() for i in items])
    return items


def _gather_live(product: dict, limits: dict) -> list[EvidenceItem]:
    import requests

    zone = os.environ.get("BRIGHTDATA_ZONE", "serp_api")
    q = f'site:reddit.com "{product["name"]}" review opinion'
    google_url = "https://www.google.com/search?" + urllib.parse.urlencode(
        {"q": q, "hl": "en", "gl": "us", "num": "20", "brd_json": "1"}
    )
    payload = {"zone": zone, "url": google_url, "format": "raw"}
    headers = {
        "Authorization": f"Bearer {os.environ['BRIGHTDATA_API_KEY']}",
        "Content-Type": "application/json",
    }

    print(f"  [brightdata] {product['name']}: SERP reddit search (zone={zone})")
    resp = requests.post(_ENDPOINT, headers=headers, json=payload, timeout=90)
    resp.raise_for_status()

    data = json.loads(resp.text)  # brd_json=1 → parsed SERP JSON
    organic = data.get("organic") or data.get("organic_results") or []

    limit = limits.get("max_reddit_threads_per_product", 6)
    items: list[EvidenceItem] = []
    seen_urls: set[str] = set()
    for o in organic:
        link = o.get("link") or o.get("url") or ""
        if "reddit.com/r/" not in link or link in seen_urls:
            continue
        snippet = (o.get("description") or o.get("snippet") or "").strip()
        if not snippet:
            continue
        seen_urls.add(link)
        m = _SUBREDDIT_RE.search(link)
        items.append(EvidenceItem(
            source_type="reddit",
            source=f"r/{m.group(1)}" if m else "reddit",
            title=(o.get("title") or "").strip() or "Reddit thread",
            url=link,
            quote=snippet,
        ))
        if len(items) >= limit:
            break

    if not items:
        print(f"  [brightdata] no reddit results for {product['name']}; using mock")
        return mock_reddit_evidence(product["name"])
    return items
