# TechPick — Agent Forge Hackathon Submission

## One-liner

**Evidence-based phone recommendations** from curated YouTube reviewers + Reddit — every claim cited, every score explainable.

## Problem

Buying a phone means drowning in biased ads, affiliate reviews, and Reddit noise. Shoppers need **aggregated, cited pros/cons** across trusted sources — weighted by what *they* care about (battery, camera, value).

## Solution

TechPick runs a **5-stage agent pipeline**:

```
Brain → Research → Aggregator → Scoring → Recommender
         ├─ VideoDB (YouTube transcripts + timestamps)
         └─ Bright Data (Reddit SERP + optional scrape)
```

1. **Brain** — job config from `config.py` (products, curated channels, aspects).
2. **Research** — parallel per-product I/O; scrape-once disk cache; offline mock fallback.
3. **Aggregator** — Claude (TokenRouter) normalizes raw evidence into deduplicated PRO/CON claims.
4. **Scoring** — deterministic, auditable: `claim_score = 2×videos + 1×reddit`; question-aware priority boost.
5. **Recommender** — Top pick / Runner-up / Not recommended + confidence + citation-grounded bullets.

## Sponsor integrations

| Sponsor | How we use it |
|---------|----------------|
| **TokenRouter** | OpenAI-compatible Claude for structured aggregation + natural-language verdicts |
| **VideoDB** | Ingest curated channels; semantic search inside review transcripts; timestamped citations |
| **Bright Data** | SERP search for Reddit threads; optional unlocker scrape for richer quotes |

Patterns follow official skills repos: [brightdata/skills](https://github.com/brightdata/skills), [video-db/skills](https://github.com/video-db/skills).

## Differentiators (why this stands out)

- **Citations everywhere** — YouTube links with timestamps; Reddit permalinks.
- **Explainable scoring** — collapsible points breakdown (pros Σ − cons Σ = net).
- **Question-aware ranking** — user priorities (battery, camera, etc.) get 3× weight in scoring.
- **Curated trust layer** — fixed reviewer allowlist (MKBHD, Mrwhosetheboss, JerryRig, …), not random web scrape.
- **Production-shaped** — concurrent pipeline, disk cache, Pydantic schemas, CLI + Web UI, works offline with mock data.
- **Multi-agent architecture** — thin agents per concern; orchestration in `pipeline.py`.

## Demo script (recommended evaluation flow)

### 1. Web UI (fastest — ~30s with cache)

```bash
cd AGENTFORGE-TechPick
source .venv/bin/activate
uvicorn app:app --reload
```

Open http://127.0.0.1:8000

**Try these questions** (shows priority-aware ranking):

| Question | What it demonstrates |
|----------|---------------------|
| `What's the best phone for battery life?` | Battery priority → re-weighted scores |
| `I care most about camera and photos` | Camera category boost |
| `Best value phone across budget and mid tier?` | Tier-aware comparison + verdict bullets |

Toggle **Fresh scrape** to bypass `.cache/` and hit live VideoDB / Bright Data.

### 2. CLI (full pipeline logs)

```bash
python main.py
python main.py --no-cache
```

### 3. API (machine-readable)

```bash
curl -s http://127.0.0.1:8000/api/about | python -m json.tool
curl -s -X POST http://127.0.0.1:8000/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Best phone for battery life?"}' | python -m json.tool
```

## Architecture map

```
app.py / main.py          entry points (web + CLI)
config.py                 products, channels, aspects, limits
src/pipeline.py           concurrent orchestration
src/agents/               brain, videodb, brightdata, aggregator, recommender
src/brightdata/           SERP search + scrape (skills patterns)
src/videodb/              ingest + semantic search (skills patterns)
src/scoring.py            deterministic + breakdown()
src/priorities.py         NL question → category weights
src/answer.py             citation-grounded verdict bullets
static/index.html         bento comparison UI with points dropdown
```

## Rubric alignment

| Criterion | Evidence in repo |
|-----------|------------------|
| Multi-agent design | 5 named agents + orchestrator; diagram in README |
| Real-world utility | Phone buyer use case; natural-language questions |
| Sponsor tool usage | TokenRouter LLM, VideoDB transcripts, Bright Data Reddit |
| Explainability | Score breakdown UI, deterministic formula in `scoring.py` |
| Citations / grounding | Every claim links to source video/thread |
| Runnable demo | Mock data offline; one-command web + CLI |
| Code quality | Pydantic models, typed pipeline, modular agents |

## Environment

Copy `.env.example` → `.env`. Minimum: `TOKENROUTER_API_KEY`. Optional live data: `VIDEO_DB_API_KEY`, `BRIGHTDATA_API_KEY`.

## Team / project

**TechPick** — Agent Forge hackathon · evidence-based tech review assistant.
