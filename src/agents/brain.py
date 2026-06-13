"""Brain agent — builds the job config (products, channels, limits).

For the hackathon MVP this is deterministic (reads config.py). The seam is here
so you can later let the model pick products dynamically.
"""
from __future__ import annotations

import config


def build_job() -> dict:
    return {
        **config.JOB,
        "products": config.PRODUCTS,
        "channels": config.CHANNELS,
    }
