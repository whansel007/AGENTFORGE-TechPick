"""SERP search — brightdata/skills `search` skill (legacy REST path).

Pattern: Google keyword SERP → parse `.organic[]` → filter before scraping.
"""
from __future__ import annotations

import json
import re
import urllib.parse

from src.brightdata import client

_REDDIT_PATH_RE = re.compile(r"reddit\.com/r/([A-Za-z0-9_]+)")


def google_search(
    query: str,
    *,
    num: int = 20,
    country: str = "us",
    language: str = "en",
) -> dict:
    """Run a Google SERP query via Bright Data Web Unlocker / SERP zone."""
    params = {
        "q": query,
        "hl": language,
        "gl": country,
        "num": str(num),
        "brd_json": "1",
    }
    google_url = "https://www.google.com/search?" + urllib.parse.urlencode(params)
    resp = client.post_request(zone=client.serp_zone(), url=google_url, fmt="raw", timeout=90)
    resp.raise_for_status()
    return json.loads(resp.text)


def organic_results(data: dict) -> list[dict]:
    """Normalize SERP payload — skills expect `.organic[]`."""
    organic = data.get("organic") or data.get("organic_results") or []
    return organic if isinstance(organic, list) else []


def filter_reddit_threads(
    organic: list[dict],
    *,
    product_name: str,
    limit: int,
) -> list[dict]:
    """SERP → filter pipeline from skills/search/references/patterns.md."""
    items: list[dict] = []
    seen_urls: set[str] = set()
    product_lc = product_name.lower()

    for row in organic:
        link = (row.get("link") or row.get("url") or "").strip()
        if "reddit.com/r/" not in link or link in seen_urls:
            continue

        title = (row.get("title") or "").strip()
        snippet = (row.get("description") or row.get("snippet") or "").strip()
        if not snippet:
            continue

        # Relevance heuristic: product name in title or snippet.
        blob = f"{title} {snippet}".lower()
        if product_lc not in blob and not any(a in blob for a in _product_aliases(product_name)):
            continue

        seen_urls.add(link)
        sub = _REDDIT_PATH_RE.search(link)
        items.append({
            "url": link,
            "title": title or "Reddit thread",
            "snippet": snippet,
            "subreddit": f"r/{sub.group(1)}" if sub else "reddit",
        })
        if len(items) >= limit:
            break
    return items


def _product_aliases(name: str) -> list[str]:
    aliases = [name.lower()]
    if "(" in name:
        aliases.append(name.split("(", 1)[0].strip().lower())
    return aliases
