"""Job configuration: products under review + curated reviewer allowlist.

Edit PRODUCTS to change what the demo compares. Category = phones, scope = best
across tiers (one product per tier). See memory.md for the decision record.
"""

# --- Products (best across tiers) -------------------------------------------
PRODUCTS = [
    {"name": "iPhone 17 Pro",        "tier": "flagship", "aliases": ["iphone 17 pro", "17 pro"]},
    {"name": "Google Pixel 9a",      "tier": "mid",      "aliases": ["pixel 9a", "9a"]},
    {"name": "Nothing Phone (3a)",   "tier": "budget",   "aliases": ["nothing phone 3a", "phone (3a)", "phone 3a"]},
]

# --- Curated reviewers (fixed allowlist) ------------------------------------
# Phone demo leans on MKBHD / Mrwhosetheboss / JerryRig; Dave2D + LTT kept for
# cross-category reuse. Evidence recurrence across these = stronger signal.
CHANNELS = [
    {"name": "MKBHD",              "handle": "@mkbhd",               "phone_focus": True},
    {"name": "Mrwhosetheboss",    "handle": "@Mrwhosetheboss",      "phone_focus": True},
    {"name": "JerryRigEverything","handle": "@JerryRigEverything",  "phone_focus": True},
    {"name": "Dave2D",            "handle": "@Dave2D",              "phone_focus": False},
    {"name": "Linus Tech Tips",   "handle": "@LinusTechTips",       "phone_focus": False},
]

# --- Job limits -------------------------------------------------------------
JOB = {
    "category": "phones",
    "price_scope": "best-across-tiers",
    "max_videos_per_product": 2,            # phone-focused channels only; keep runs sane
    "max_reddit_threads_per_product": 6,
    "date_range_days": 540,                  # ~18 months of reviews
}

# Aspects the VideoDB agent semantically searches inside each review video.
# Each hit becomes one timestamped EvidenceItem.
VIDEO_ASPECTS = [
    "battery life",
    "camera quality and photos",
    "performance and speed",
    "build quality and durability",
    "display and screen",
    "price and value for money",
]

# --- Model ------------------------------------------------------------------
MODEL = "anthropic/claude-opus-4.8-fast"
