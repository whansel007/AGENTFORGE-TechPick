"""VideoDB research agent — per product, find curated-reviewer videos on YouTube,
ingest + transcribe them, then semantically search each for the aspects we care
about. Every hit becomes a timestamped, transcript-backed EvidenceItem.

Videos for a product are ingested CONCURRENTLY (each upload+index is I/O-bound,
waiting on VideoDB's cloud), so wall-clock is ~one video rather than the sum.

If VIDEODB_API_KEY is absent (or a live call fails) the agent falls back to mock
evidence so the pipeline never hard-stops.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import config
from src import cache
from src.mockdata import mock_video_evidence
from src.schemas import EvidenceItem

# Only reviewers whose channel covers phones are queried for the phone demo.
_PHONE_CHANNELS = [c for c in config.CHANNELS if c.get("phone_focus")]


def gather(product: dict, channels: list[dict], limits: dict) -> list[EvidenceItem]:
    key = f"videodb::{product['name']}"
    cached = cache.get(key)
    if cached is not None:
        return [EvidenceItem(**e) for e in cached]

    if os.environ.get("VIDEODB_API_KEY"):
        try:
            items = _gather_live(product, limits)
        except Exception as e:  # noqa: BLE001 — never let one source kill the run
            print(f"  [videodb] live fetch failed for {product['name']} ({e}); using mock")
            items = mock_video_evidence(product["name"])
    else:
        items = mock_video_evidence(product["name"])

    cache.put(key, [i.model_dump() for i in items])
    return items


def _mmss(seconds: float) -> str:
    s = int(seconds or 0)
    return f"{s // 60:02d}:{s % 60:02d}"


def _ingest_channel(conn, coll, product: dict, ch: dict) -> list[EvidenceItem]:
    """Find, ingest, index, and aspect-search one reviewer's video for a product."""
    query = f"{ch['name']} {product['name']} review"
    try:
        hits = conn.youtube_search(query, result_threshold=3)
    except Exception as e:  # noqa: BLE001
        print(f"  [videodb] youtube_search failed for '{query}': {e}")
        return []
    hit = next((h for h in hits if h.get("link")), None)
    if not hit:
        print(f"  [videodb] no YouTube result for '{query}'")
        return []

    url, title = hit["link"], hit.get("title", query)
    print(f"  [videodb] {product['name']} ← {ch['name']}: ingesting '{title[:60]}'")
    try:
        video = coll.upload(url=url)
        video.index_spoken_words()
    except Exception as e:  # noqa: BLE001
        print(f"  [videodb] skip {ch['name']} (ingest/index failed: {e})")
        return []

    items: list[EvidenceItem] = []
    seen: set[tuple[str, int]] = set()
    for aspect in config.VIDEO_ASPECTS:
        try:
            shots = video.search(aspect, result_threshold=1).get_shots()
        except Exception:  # noqa: BLE001
            continue
        for shot in shots:
            text = (shot.text or "").strip()
            k = (text[:60], int(shot.start or 0))
            if not text or k in seen:
                continue
            seen.add(k)
            items.append(EvidenceItem(
                source_type="video",
                source=ch["name"],
                title=getattr(shot, "video_title", None) or title,
                url=url,
                timestamp=_mmss(shot.start),
                quote=text,
            ))
    return items


def _gather_live(product: dict, limits: dict) -> list[EvidenceItem]:
    import videodb

    conn = videodb.connect(api_key=os.environ["VIDEODB_API_KEY"])
    coll = conn.get_collection()

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
