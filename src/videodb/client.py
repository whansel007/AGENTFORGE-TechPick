"""VideoDB client helpers — video-db/skills python skill patterns."""
from __future__ import annotations

import os


def api_key() -> str | None:
    """Skills use VIDEO_DB_API_KEY; keep VIDEODB_API_KEY alias for this repo."""
    return (
        os.environ.get("VIDEO_DB_API_KEY", "").strip()
        or os.environ.get("VIDEODB_API_KEY", "").strip()
        or None
    )


def connect():
    import videodb
    from videodb.exceptions import AuthenticationError

    key = api_key()
    if not key:
        raise AuthenticationError("VIDEO_DB_API_KEY / VIDEODB_API_KEY is not set")
    return videodb.connect(api_key=key)


def get_collection(conn):
    return conn.get_collection()
