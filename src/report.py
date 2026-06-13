"""Serialize pipeline output for CLI and web."""
from __future__ import annotations

from src.schemas import Claim, EvidenceItem, Recommendation


def evidence_dict(e: EvidenceItem) -> dict:
    return {
        "source_type": e.source_type,
        "source": e.source,
        "title": e.title,
        "url": e.url,
        "timestamp": e.timestamp,
        "quote": e.quote,
    }


def claim_dict(c: Claim) -> dict:
    return {
        "text": c.text,
        "polarity": c.polarity,
        "category": c.category,
        "v": c.v,
        "r": c.r,
        "score": c.score,
        "evidence": [evidence_dict(e) for e in c.evidence],
    }


def recommendation_dict(r: Recommendation) -> dict:
    return {
        "product": r.product,
        "tier": r.tier,
        "bucket": r.bucket,
        "confidence": r.confidence,
        "product_score": r.product_score,
        "rationale": r.rationale,
        "top_pros": [claim_dict(c) for c in r.top_pros],
        "top_cons": [claim_dict(c) for c in r.top_cons],
        "score_breakdown": r.score_breakdown,
    }


def to_api_response(
    *,
    question: str,
    summary_bullets: list[str],
    priorities: list[str],
    priority_categories: list[str],
    recommendations: list[Recommendation],
    products_compared: list[str],
) -> dict:
    return {
        "question": question,
        "summary_bullets": summary_bullets,
        "priorities": priorities,
        "priority_categories": priority_categories,
        "products_compared": products_compared,
        "recommendations": [recommendation_dict(r) for r in recommendations],
    }
