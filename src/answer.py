"""Turn ranked recommendations into bullet-point answers."""
from __future__ import annotations

import re

from src import llm, priorities
from src.schemas import Claim, Recommendation

_SYSTEM = """You answer a phone-buying question using ranked evidence (YouTube reviewers + Reddit).

Return exactly 3–4 bullet points. Rules:
- One bullet per line, start each line with "- "
- Max 16 words per bullet
- Compare ALL phones on the user's stated priorities
- Bullet 1: best phone for their priority + one evidence-backed reason
- Bullets 2–3: how the other phones rank on that same priority
- Bullet 4: key tradeoff or who should pick a runner-up
- Ground only in the ranked results — no invented specs
- No intro, no prose paragraphs, no markdown beyond the dash bullets"""

_GENERAL_SYSTEM = """You answer a phone-buying question using ranked evidence (YouTube reviewers + Reddit).

Return exactly 3–4 bullet points. Rules:
- One bullet per line, start each line with "- "
- Max 14 words per bullet
- Bullet 1: direct answer + top pick
- Bullet 2: runner-up in one line
- Bullet 3–4: key tradeoff or who should skip the top pick
- Ground only in the ranked results — no invented specs
- No intro, no prose paragraphs, no markdown beyond the dash bullets"""


def _parse_bullets(text: str) -> list[str]:
    bullets: list[str] = []
    for line in text.strip().splitlines():
        line = re.sub(r"^[-•*]\s*", "", line.strip())
        if line:
            bullets.append(line)
    return bullets[:5]


def _claim_line(c: Claim) -> str:
    return f"{c.text} [{c.category}]"


def _focus_claims(claims: list[Claim], prefs: list[str]) -> list[Claim]:
    if not prefs:
        return claims[:2]
    matched = [c for c in claims if c.category in prefs]
    return (matched or claims)[:2]


def _fallback_bullets(recs: list[Recommendation], prefs: list[str]) -> list[str]:
    if prefs:
        labels = priorities.labels(prefs)
        focus = ", ".join(labels)
        bullets = [f"Compared for {focus}:"]
        for r in recs:
            pro = _focus_claims(r.top_pros, prefs)
            con = _focus_claims(r.top_cons, prefs)
            pro_txt = pro[0].text if pro else "no strong pro"
            con_txt = con[0].text if con else "no major con"
            bullets.append(f"{r.product} ({r.bucket}): + {pro_txt}; − {con_txt}")
        return bullets[:4]

    top = recs[0]
    bullets = [f"Top pick: {top.product} ({top.tier}, {top.confidence} confidence)"]
    if len(recs) > 1 and recs[1].bucket == "Runner-up":
        bullets.append(f"Runner-up: {recs[1].product}")
    pro = top.top_pros[0].text if top.top_pros else None
    con = top.top_cons[0].text if top.top_cons else None
    if pro:
        bullets.append(f"Main strength: {pro}")
    if con:
        bullets.append(f"Main weakness: {con}")
    return bullets


def summarize(
    question: str,
    recs: list[Recommendation],
    priority_categories: list[str] | None = None,
) -> list[str]:
    if not recs:
        return ["Not enough reviewer or Reddit evidence to recommend a phone."]

    prefs = priority_categories or []
    lines = []
    for r in recs:
        pros = "; ".join(_claim_line(c) for c in _focus_claims(r.top_pros, prefs)) or "none"
        cons = "; ".join(_claim_line(c) for c in _focus_claims(r.top_cons, prefs)) or "none"
        lines.append(
            f"{r.bucket}: {r.product} ({r.tier}, score={r.product_score:.0f}, "
            f"{r.confidence}). Focus pros: {pros}. Focus cons: {cons}."
        )

    focus = ", ".join(priorities.labels(prefs)) if prefs else "general comparison"
    user = f"Question: {question}\nUser priorities: {focus}\n\nResults:\n" + "\n".join(lines)
    system = _SYSTEM if prefs else _GENERAL_SYSTEM
    try:
        raw = llm.text(system, user, max_tokens=300)
        bullets = _parse_bullets(raw)
        return bullets or _fallback_bullets(recs, prefs)
    except Exception:
        return _fallback_bullets(recs, prefs)
