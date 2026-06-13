"""Evidence aggregator — the one LLM-heavy step. Takes raw transcript + Reddit
evidence for a product and normalizes it into deduplicated PRO/CON claims.

The model only references evidence by index; we reattach the actual EvidenceItem
objects here, so source counts (used by scoring) can never be lost in the model's
output. Junk/empty claims are dropped, and a degenerate response (almost no claims
despite ample evidence) is retried once. Scoring itself is deterministic — see
scoring.py.
"""
from __future__ import annotations

from src import llm
from src.schemas import AggregatorOutput, Claim, EvidenceItem, ProductClaims

_SYSTEM = """You are an evidence aggregator for a tech-review assistant.

You receive numbered evidence about ONE phone: snippets from curated YouTube
reviewers (with timestamps) and Reddit threads. Normalize them into recurring PRO
and CON claims.

Rules:
- Merge snippets that say the same thing into ONE canonical claim (e.g. "great
  battery", "lasts all day", "battery is excellent" -> one PRO "Excellent battery
  life"). Recurrence across sources is the whole point — never emit the same claim
  twice.
- For each claim, list the indices of ALL supporting snippets in `evidence_ids`,
  using only indices that appear in the input. Every claim must cite >= 1 index.
- Give each claim a short category: battery, camera, performance, display, build,
  software, value, or other.
- Assign each snippet to the single claim it best supports.
- polarity must match sentiment: PRO = a strength/praise, CON = a weakness/
  criticism. A claim like "mediocre cameras" or "slow charging" is a CON even if
  it's the only thing notable. Never label a criticism as a PRO.
- Write a real, specific claim for each — never a placeholder. Never emit an empty
  claim text."""

_JUNK = {"placeholder", "none", "n/a", "na", "unknown", "tbd", "claim", "pro", "con"}


def _number(evidence: list[EvidenceItem]) -> str:
    lines = []
    for i, e in enumerate(evidence):
        ts = f" @{e.timestamp}" if e.timestamp else ""
        lines.append(f'[{i}] ({e.source_type}) {e.source}{ts}: "{e.quote}"  <{e.url}>')
    return "\n".join(lines)


def _build(out: AggregatorOutput, evidence: list[EvidenceItem]):
    """Route drafts to pros/cons by declared polarity, dropping empty/junk claims.

    Routing by the claim's own `polarity` (not which list it arrived in) means a
    criticism the model accidentally placed under `pros` still scores as a con.
    """
    pros: list[Claim] = []
    cons: list[Claim] = []
    for d in list(out.pros) + list(out.cons):
        text = d.text.strip()
        items = [evidence[i] for i in d.evidence_ids if 0 <= i < len(evidence)]
        if not items or len(text) < 5 or text.lower() in _JUNK:
            continue  # drop hallucinated / placeholder / empty claims
        claim = Claim(text=text, polarity=d.polarity, category=d.category, evidence=items)
        (pros if d.polarity == "PRO" else cons).append(claim)
    return pros, cons


def aggregate(product: str, evidence: list[EvidenceItem]) -> ProductClaims:
    user = f"Phone: {product}\n\nEvidence (cite by [index]):\n{_number(evidence)}"

    pros: list[Claim] = []
    cons: list[Claim] = []
    # Retry once if the model degenerates (almost no claims despite ample evidence).
    for attempt in range(2):
        out: AggregatorOutput = llm.parse(_SYSTEM, user, AggregatorOutput, max_tokens=6000)
        pros, cons = _build(out, evidence)
        degenerate = len(evidence) >= 4 and (len(pros) + len(cons)) <= 1
        if not degenerate:
            break
        print(f"  [aggregate] {product}: degenerate output, retrying ({attempt + 1})")

    return ProductClaims(product=product, pros=pros, cons=cons)
