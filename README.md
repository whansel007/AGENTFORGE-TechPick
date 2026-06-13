# AIFORGE — Evidence-Based Tech Review Assistant

Agent Forge hackathon project. Scrapes live opinions from **curated YouTube
reviewers** (via VideoDB transcripts) and **Reddit** (via Bright Data), aggregates
recurring **pros/cons** by evidence recurrence, and recommends phones with
**citations** (links + timestamps).

**Demo scope:** phones, best across tiers — iPhone 17 Pro (flagship) · Google
Pixel 9a (mid) · Nothing Phone (3a) (budget). Edit `config.py` to change.

## Pipeline (matches the design diagram)

```
Brain ─▶ Research ─▶ Aggregator ─▶ Scoring ─▶ Recommender
          ├─ VideoDB agent  (transcripts + timestamps)
          └─ Bright Data agent (Reddit mentions + links)
```

- **Brain** (`src/agents/brain.py`) — builds the job config from `config.py`.
- **Research** (`videodb_agent.py`, `brightdata_agent.py`) — gather evidence;
  **scrape-once** cached to `.cache/`. No API keys → realistic **mock evidence**
  so the pipeline runs offline.
- **Aggregator** (`aggregator.py`) — the LLM step: normalizes raw evidence into
  deduplicated PRO/CON claims (Claude, structured output).
- **Scoring** (`scoring.py`) — deterministic & explainable:
  `claim_score = 2·(unique videos) + 1·(unique reddit)`;
  `product_score = Σ top pros − Σ top cons`.
- **Recommender** (`recommender.py`) — buckets (Top pick / Runner-up / Not
  recommended) + High/Med/Low confidence + a citation-grounded rationale.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # add TOKENROUTER_API_KEY (required)
python main.py              # runs offline with mock evidence
```

LLM calls route through [TokenRouter](https://tokenrouter.io) (Anthropic provider
by default). Add your provider keys in the TokenRouter dashboard.

Add `VIDEODB_API_KEY` / `BRIGHTDATA_API_KEY` to `.env` to switch the research
agents to live data — wire-up points are marked `TODO` in
`src/agents/videodb_agent.py` and `src/agents/brightdata_agent.py`. Nothing else
in the pipeline changes.

```bash
python main.py --no-cache   # re-gather, ignore the scrape cache
python main.py --quiet      # report only, no progress logs
```

## Layout

```
config.py              products, curated channels, limits, model
main.py                CLI + report formatting
src/
  pipeline.py          orchestration
  schemas.py           Pydantic models (evidence, claims, recommendation)
  llm.py               TokenRouter wrapper (claude-opus-4-8, structured output)
  scoring.py           deterministic scoring + confidence
  cache.py             scrape-once disk cache
  mockdata.py          offline demo evidence
  agents/              brain, videodb, brightdata, aggregator, recommender
```

Model: `claude-opus-4-8` with adaptive thinking and structured outputs.
