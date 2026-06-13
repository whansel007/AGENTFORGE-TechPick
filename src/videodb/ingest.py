"""YouTube ingest — upload + spoken-word index (video-db/skills)."""
from __future__ import annotations


def find_review_video(conn, *, channel_name: str, product_name: str) -> dict | None:
    """youtube_search → first result with a link."""
    query = f"{channel_name} {product_name} review"
    try:
        hits = conn.youtube_search(query, result_threshold=3)
    except Exception as e:  # noqa: BLE001
        print(f"  [videodb] youtube_search failed for '{query}': {e}")
        return None

    hit = next((h for h in hits if h.get("link")), None)
    if not hit:
        print(f"  [videodb] no YouTube result for '{query}'")
        return None

    return {
        "url": hit["link"],
        "title": hit.get("title", query),
        "channel": channel_name,
    }


def upload_and_index(coll, *, url: str, title: str, channel: str) -> object | None:
    """Upload YouTube URL and index spoken words (force=True per skill)."""
    print(f"  [videodb] ingesting '{title[:60]}' ({channel})")
    try:
        video = coll.upload(url=url)
        video.index_spoken_words(force=True)
    except Exception as e:  # noqa: BLE001
        print(f"  [videodb] skip {channel} (ingest/index failed: {e})")
        return None
    return video
