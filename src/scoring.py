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
PRIORITY_BOOST = 3.0
NON_PRIORITY_WEIGHT = 0.6


def _round1(x: float) -> float:
    return round(x, 1)


def _weight(claim: Claim, priorities: list[str] | None) -> float:
    if not priorities:
        return 1.0
    return PRIORITY_BOOST if claim.category in priorities else NON_PRIORITY_WEIGHT


def _count_sources(claim: Claim) -> None:
    videos = {e.source for e in claim.evidence if e.source_type == "video"}
    reddit = {e.url for e in claim.evidence if e.source_type == "reddit"}
    claim.v = len(videos)
    claim.r = len(reddit)
    claim.score = 2 * claim.v + claim.r


def _weighted_score(claim: Claim, priorities: list[str] | None) -> float:
    return claim.score * _weight(claim, priorities)


def score_product(pc: ProductClaims, priorities: list[str] | None = None) -> float:
    for c in pc.pros + pc.cons:
        _count_sources(c)

    pc.pros.sort(key=lambda c: _weighted_score(c, priorities), reverse=True)
    pc.cons.sort(key=lambda c: _weighted_score(c, priorities), reverse=True)

    pro_sum = sum(_weighted_score(c, priorities) for c in pc.pros[:TOP_N])
    con_sum = sum(_weighted_score(c, priorities) for c in pc.cons[:TOP_N])
    return pro_sum - con_sum


def _claim_line(c: Claim, priorities: list[str] | None) -> dict:
    w = _weight(c, priorities)
    base = c.score
    weighted = _round1(base * w)
    return {
        "text": c.text,
        "category": c.category,
        "v": c.v,
        "r": c.r,
        "base_score": base,
        "weight": w,
        "weighted_score": weighted,
    }


def breakdown(pc: ProductClaims, priorities: list[str] | None = None) -> dict:
    """Explainable score math. Call after score_product (sources counted, lists sorted)."""
    pro_lines = [_claim_line(c, priorities) for c in pc.pros[:TOP_N]]
    con_lines = [_claim_line(c, priorities) for c in pc.cons[:TOP_N]]
    pro_total = _round1(sum(l["weighted_score"] for l in pro_lines))
    con_total = _round1(sum(l["weighted_score"] for l in con_lines))
    net_score = _round1(pro_total - con_total)
    return {
        "top_n": TOP_N,
        "pro_total": pro_total,
        "con_total": con_total,
        "net_score": net_score,
        "pro_lines": pro_lines,
        "con_lines": con_lines,
    }


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
