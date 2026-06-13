"""Recommendation agent — ranks scored products into buckets and writes a short,
citation-grounded rationale.

Buckets and confidence are deterministic (per the scoring spec); the LLM only
writes the human rationale so the numeric ranking stays explainable.
"""
from __future__ import annotations

from src import llm, scoring
from src.schemas import ProductClaims, Recommendation

_SYSTEM = """You write a one-paragraph recommendation rationale for a phone, for a
buyer. You are given the product, its bucket, its top recurring pros and cons, and
how many independent sources back each. Be concrete and reference the recurring
evidence (e.g. "called out by 3 reviewers"). 2-4 sentences. No fluff, no markdown."""


def recommend(scored: list[tuple[ProductClaims, str]]) -> list[Recommendation]:
    """scored: list of (ProductClaims, tier)."""
    # Compute scores + confidence, then order by product_score desc.
    enriched = []
    for pc, tier in scored:
        ps = scoring.score_product(pc)
        conf = scoring.confidence(pc)
        enriched.append((pc, tier, ps, conf))
    enriched.sort(key=lambda x: x[2], reverse=True)

    recs: list[Recommendation] = []
    for idx, (pc, tier, ps, conf) in enumerate(enriched):
        bucket = _bucket(idx, ps, conf)
        top_pros = pc.pros[:3]
        top_cons = pc.cons[:3]
        rationale = _rationale(pc.product, bucket, top_pros, top_cons)
        recs.append(Recommendation(
            product=pc.product, tier=tier, bucket=bucket, confidence=conf,
            product_score=ps, rationale=rationale,
            top_pros=top_pros, top_cons=top_cons,
        ))
    return recs


def _bucket(idx: int, score: float, conf: str) -> str:
    if score <= 0:
        return "Not recommended"
    if idx == 0:
        return "Top pick"
    return "Runner-up"


def _rationale(product, bucket, pros, cons) -> str:
    def fmt(claims):
        return "; ".join(f"{c.text} (v={c.v}, r={c.r})" for c in claims) or "none"
    user = (
        f"Phone: {product}\nBucket: {bucket}\n"
        f"Top pros: {fmt(pros)}\nTop cons: {fmt(cons)}"
    )
    try:
        return llm.text(_SYSTEM, user, max_tokens=400)
    except Exception as e:  # never let rationale failure kill the run
        return f"({bucket}; rationale unavailable: {e})"
