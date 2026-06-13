"""Parse user questions into scoring/display priorities."""
from __future__ import annotations

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "battery": ["battery", "battery life", "endurance", "charge", "charging", "lasting", "power"],
    "camera": ["camera", "photo", "photos", "selfie", "video", "zoom", "portrait", "pictures"],
    "performance": ["performance", "speed", "fast", "gaming", "game", "games", "processor", "chip", "smooth", "lag"],
    "display": ["display", "screen", "oled", "refresh", "brightness", "panel"],
    "build": ["build", "durability", "premium", "design", "rugged", "glass", "feel"],
    "software": ["software", "android", "ios", "updates", "ai", "assistant", "ui"],
    "value": ["value", "price", "cheap", "budget", "affordable", "cost", "deal", "money"],
}

LABELS: dict[str, str] = {
    "battery": "battery life",
    "camera": "camera",
    "performance": "performance",
    "display": "display",
    "build": "build quality",
    "software": "software",
    "value": "value",
}


def parse(question: str) -> list[str]:
    q = question.lower()
    found: list[str] = []
    for cat, words in CATEGORY_KEYWORDS.items():
        if any(w in q for w in words):
            found.append(cat)
    return found


def labels(categories: list[str]) -> list[str]:
    return [LABELS.get(c, c) for c in categories]
