"""Bright Data research agent — Reddit discovery via official skill patterns.

Pipeline (brightdata/skills `search` → `scrape`):
  1. SERP: Google `site:reddit.com "<product>" review opinion` via SERP API
  2. Filter: reddit allowlist + product relevance heuristic (skills/patterns.md)
  3. Scrape (optional): enrich top threads via Web Unlocker when
     BRIGHTDATA_UNLOCKER_ZONE is set

Based on ScrapeAlchemist/brightdata-hack-pack examples and brightdata/skills.
Falls back to mock evidence if keys are missing or live calls fail.
"""
from __future__ import annotations

from src import cache
from src.brightdata import client as bd_client
from src.brightdata import scrape as bd_scrape
from src.brightdata import search as bd_search
from src.mockdata import mock_reddit_evidence
from src.schemas import EvidenceItem

_REDDIT_QUERY = 'site:reddit.com "{product}" review opinion'
_ENRICH_TOP_N = 2  # scrape at most this many threads per product (keeps runs fast)


def gather(product: dict, limits: dict) -> list[EvidenceItem]:
    key = f"brightdata::{product['name']}"
    cached = cache.get(key)
    if cached is not None:
        return [EvidenceItem(**e) for e in cached]

    if bd_client.api_key():
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
    name = product["name"]
    limit = limits.get("max_reddit_threads_per_product", 6)
    query = _REDDIT_QUERY.format(product=name)

    print(f"  [brightdata] {name}: SERP reddit search (zone={bd_client.serp_zone()})")
    serp = bd_search.google_search(query, num=20)
    threads = bd_search.filter_reddit_threads(
        bd_search.organic_results(serp),
        product_name=name,
        limit=limit,
    )

    if not threads:
        print(f"  [brightdata] no reddit results for {name}; using mock")
        return mock_reddit_evidence(name)

    items: list[EvidenceItem] = []
    for idx, thread in enumerate(threads):
        quote = thread["snippet"]
        if idx < _ENRICH_TOP_N and bd_client.unlocker_zone():
            print(f"  [brightdata] {name}: scrape thread {thread['url']}")
            body = bd_scrape.scrape_raw(thread["url"])
            if body:
                enriched = bd_scrape.excerpt_from_page(body)
                if enriched and not bd_scrape.is_blocked(enriched):
                    quote = enriched

        items.append(EvidenceItem(
            source_type="reddit",
            source=thread["subreddit"],
            title=thread["title"],
            url=thread["url"],
            quote=quote,
        ))

    return items
