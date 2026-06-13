"""Shared data models for the tech-review pipeline."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# --- Raw evidence (output of research agents) -------------------------------
class EvidenceItem(BaseModel):
    source_type: Literal["video", "reddit"]
    source: str = Field(description="Channel name (video) or subreddit/thread (reddit)")
    title: str
    url: str
    timestamp: Optional[str] = Field(default=None, description="mm:ss into the video, if applicable")
    quote: str = Field(description="The exact supporting snippet")


class ProductEvidence(BaseModel):
    product: str
    items: list[EvidenceItem] = Field(default_factory=list)


# --- Normalized claims (output of the aggregator) ---------------------------
class Claim(BaseModel):
    text: str = Field(description="Canonical, deduplicated claim, e.g. 'Excellent battery life'")
    polarity: Literal["PRO", "CON"]
    category: str = Field(description="e.g. battery, camera, performance, build, software, value")
    evidence: list[EvidenceItem] = Field(default_factory=list)

    # populated by scoring.py
    v: int = 0  # unique video sources
    r: int = 0  # unique reddit threads
    score: float = 0.0


class ProductClaims(BaseModel):
    product: str
    pros: list[Claim] = Field(default_factory=list)
    cons: list[Claim] = Field(default_factory=list)


# --- Final recommendation ---------------------------------------------------
class Recommendation(BaseModel):
    product: str
    tier: str
    bucket: Literal["Top pick", "Runner-up", "Not recommended"]
    confidence: Literal["High", "Med", "Low"]
    product_score: float
    rationale: str
    top_pros: list[Claim] = Field(default_factory=list)
    top_cons: list[Claim] = Field(default_factory=list)
    score_breakdown: dict = Field(default_factory=dict)


# Schemas used by the aggregator's structured-output call. The model references
# evidence by index (cheap + lossless); aggregator.py reattaches the real
# EvidenceItem objects, so the v/r counts can never be dropped by the model.
class ClaimDraft(BaseModel):
    text: str = Field(description="Canonical, deduplicated claim")
    polarity: Literal["PRO", "CON"]
    category: str = Field(description="battery, camera, performance, display, build, software, value, or other")
    evidence_ids: list[int] = Field(description="0-based indices into the provided evidence list")


class AggregatorOutput(BaseModel):
    pros: list[ClaimDraft]
    cons: list[ClaimDraft]
