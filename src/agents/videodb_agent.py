"""VideoDB research agent — curated YouTube reviews via video-db/skills patterns.

Pipeline (index → search → evidence):
  1. youtube_search for each phone-focused reviewer channel
  2. upload + index_spoken_words(force=True)
  3. semantic search per aspect with InvalidRequestError handling

Based on https://github.com/video-db/skills (python skill).
Falls back to mock evidence if keys are missing or live calls fail.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import config
from src import cache
from src.mockdata import mock_video_evidence
from src.schemas import EvidenceItem
from src.videodb import client as vdb_client
from src.videodb import ingest as vdb_ingest
from src.videodb import search as vdb_search

_PHONE_CHANNELS = [c for c in config.CHANNELS if c.get("phone_focus")]


def gather(product: dict, channels: list[dict], limits: dict) -> list[EvidenceItem]:
    key = f"videodb::{product['name']}"
    cached = cache.get(key)
    if cached is not None:
        return [EvidenceItem(**e) for e in cached]

    if vdb_client.api_key():
        try:
            items = _gather_live(product, limits)
        except Exception as e:  # noqa: BLE001 — never let one source kill the run
            print(f"  [videodb] live fetch failed for {product['name']} ({e}); using mock")
            items = mock_video_evidence(product["name"])
    else:
        items = mock_video_evidence(product["name"])

    cache.put(key, [i.model_dump() for i in items])
    return items


def _ingest_channel(conn, coll, product: dict, ch: dict) -> list[EvidenceItem]:
    hit = vdb_ingest.find_review_video(
        conn,
        channel_name=ch["name"],
        product_name=product["name"],
    )
    if not hit:
        return []

    video = vdb_ingest.upload_and_index(
        coll,
        url=hit["url"],
        title=hit["title"],
        channel=hit["channel"],
    )
    if video is None:
        return []

    return vdb_search.aspect_evidence(
        video,
        aspects=config.VIDEO_ASPECTS,
        channel=ch["name"],
        title=hit["title"],
        url=hit["url"],
    )


def _gather_live(product: dict, limits: dict) -> list[EvidenceItem]:
    conn = vdb_client.connect()
    coll = vdb_client.get_collection(conn)

    max_videos = limits.get("max_videos_per_product", 2)
    channels = _PHONE_CHANNELS[:max_videos]

    items: list[EvidenceItem] = []
    with ThreadPoolExecutor(max_workers=max(1, len(channels))) as ex:
        for res in ex.map(lambda ch: _ingest_channel(conn, coll, product, ch), channels):
            items.extend(res)

    if not items:
        print(f"  [videodb] no live evidence for {product['name']}; using mock")
        return mock_video_evidence(product["name"])
    return items
