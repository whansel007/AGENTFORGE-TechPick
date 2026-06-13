"""Semantic search inside indexed videos — video-db/skills reference/search.md."""
from __future__ import annotations

from src.schemas import EvidenceItem


def mmss(seconds: float) -> str:
    s = int(seconds or 0)
    return f"{s // 60:02d}:{s % 60:02d}"


def search_spoken(video, query: str, *, result_threshold: int = 1) -> list:
    """Search with skill error handling — empty results, not exceptions."""
    from videodb import SearchType
    from videodb.exceptions import InvalidRequestError

    try:
        return video.search(
            query,
            search_type=SearchType.semantic,
            result_threshold=result_threshold,
        ).get_shots()
    except InvalidRequestError as e:
        if "No results found" in str(e):
            return []
        raise


def aspect_evidence(
    video,
    *,
    aspects: list[str],
    channel: str,
    title: str,
    url: str,
) -> list[EvidenceItem]:
    """Run aspect queries and dedupe timestamped transcript hits."""
    items: list[EvidenceItem] = []
    seen: set[tuple[str, int]] = set()

    for aspect in aspects:
        for shot in search_spoken(video, aspect, result_threshold=1):
            text = (shot.text or "").strip()
            start = int(shot.start or 0)
            key = (text[:60], start)
            if not text or key in seen:
                continue
            seen.add(key)
            items.append(EvidenceItem(
                source_type="video",
                source=channel,
                title=getattr(shot, "video_title", None) or title,
                url=url,
                timestamp=mmss(shot.start),
                quote=text,
            ))
    return items
