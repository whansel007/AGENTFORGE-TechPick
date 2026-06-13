"""Deterministic, explainable scoring (per memory.md spec).

For each normalized claim:
    v = number of unique video sources (curated channels)
    r = number of unique reddit threads/posts
    claim_score = 2*v + 1*r

For each product:
    product_score = sum(top PRO claim_scores) - sum(top CON claim_scores)

Confidence:
    High if some major PRO has v>=3 AND some major CON has r>=2
    Low  if evidence is thin (max v < 2 and max r < 1)
    Med  otherwise
"""
from __future__ import annotations

from src.schemas import Claim, ProductClaims

TOP_N = 5  # how many claims per polarity feed the product score


def _count_sources(claim: Claim) -> None:
    videos = {e.source for e in claim.evidence if e.source_type == "video"}
    reddit = {e.url for e in claim.evidence if e.source_type == "reddit"}
    claim.v = len(videos)
    claim.r = len(reddit)
    claim.score = 2 * claim.v + claim.r


def score_product(pc: ProductClaims) -> float:
    for c in pc.pros + pc.cons:
        _count_sources(c)

    pc.pros.sort(key=lambda c: c.score, reverse=True)
    pc.cons.sort(key=lambda c: c.score, reverse=True)

    pro_sum = sum(c.score for c in pc.pros[:TOP_N])
    con_sum = sum(c.score for c in pc.cons[:TOP_N])
    return pro_sum - con_sum


def confidence(pc: ProductClaims) -> str:
    max_pro_v = max((c.v for c in pc.pros), default=0)
    max_con_r = max((c.r for c in pc.cons), default=0)
    max_v = max((c.v for c in pc.pros + pc.cons), default=0)
    max_r = max((c.r for c in pc.pros + pc.cons), default=0)

    if max_pro_v >= 3 and max_con_r >= 2:
        return "High"
    if max_v < 2 and max_r < 1:
        return "Low"
    return "Med"
