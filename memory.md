```md
# memory.md — Tech Review Scraper (Agent Forge Hackathon)

## Goal
Build an **evidence-based tech review assistant**:
- Scrape live web data from **curated YouTube reviewers** + **Reddit**
- Use **VideoDB transcripts** + **Bright Data scraping** to gather evidence
- Aggregate recurring **pros/cons** (volume/evidence recurrence) to recommend products
- Output: **Top 3 picks + Not recommended** with **citations** (links + timestamps)

## User-defined product scope
- Tech hardware categories: **phones, laptops, cameras**
- Hackathon MVP: **Option A** → demo **all 3 products within one category**
- **Curated sources (fixed reviewers)**
  - MKBHD (Marques Brownlee) — smartphones/consumer tech/EVs
  - Mrwhosetheboss (Arun Maini) — phone comparisons & buying guides
  - Dave2D — laptops/monitors/productivity gear
  - Linus Sebastian (Linus Tech Tips) — PCs/hardware/networking/labs
  - JerryRigEverything (Zack Nelson) — durability/repairability (not traditional reviewer)

## Reliability approach (no fragile sponsorship detection)
- Do **not** dynamically infer “trustworthiness” via sponsorship detection (brittle).
- Instead, rely on **evidence recurrence**:
  - Claims supported by **multiple independent videos** from the allowlisted reviewers
  - And/or supported by **multiple Reddit threads**
- Sponsored posts may exist, but recurrence across curated sources is treated as stronger evidence.

## Evidence sources
- **VideoDB**: get transcript text + timestamps from relevant YouTube videos.
- **Bright Data**: scrape/discover **YouTube metadata** and **Reddit mentions** relevant to products.
- Process once: **scrape once, process fast** (cache locally; then analyze quickly).

## Agents & pipeline (matches diagram)
1. **Brain Agent**
   - Choose product list + set job config (products, channels, date range, limits)
2. **Research Agents**
   - **VideoDB agent**: per product + channel → retrieve candidate videos → fetch transcript → output transcript chunks/timestamps
   - **Bright Data agent**: scrape/discover YouTube/Reddit context → output relevant Reddit snippets/links + extra candidates
3. **Evidence Aggregator**
   - Normalize claims into PRO/CON categories
   - Merge evidence instances across transcripts/reddit
   - Compute recurrence scores
4. **Recommendation Agent**
   - Rank products: **Top pick / Runner-ups / Not recommended**
   - Provide confidence (High/Med/Low)
5. **Explainability Layer**
   - Provide claim-to-evidence bullets with citations:
     - transcript timestamps
     - and/or Reddit URLs

## Scoring rule (simple + explainable)
For each normalized claim:
- `v` = number of **unique video sources** (from curated channels)
- `r` = number of **unique Reddit threads/posts**
- `claim_score = 2*v + 1*r`

For each product:
- `product_score = sum(top PRO claim_scores) - sum(top CON claim_scores)`

Confidence:
- **High** if at least one major PRO has `v>=3` and one major CON has `r>=2`
- **Med** if evidence is partial
- **Low** if evidence is thin (`v<2` and `r<1`)

## Outputs (Results format)
For each of the 3 products (and final ranking):
- Top Pros (recurring) + Top Cons (recurring)
- Evidence list (2–5 citations)
- Recommendation bucket: Top pick / Runner-up / Not recommended
- Confidence level

## Decisions locked (2026-06-13)
- **Category:** Phones (best curated-source overlap: MKBHD, Mrwhosetheboss, JerryRig)
- **Price scope:** Best across tiers (one product per tier: flagship / mid / budget)
- **Stack:** Python + Anthropic SDK (`claude-opus-4-8`, adaptive thinking, structured outputs)
- **Demo products (edit in `config.py`):** iPhone 17 Pro (flagship), Google Pixel 9a (mid), Nothing Phone (3a) (budget)

## Build status
- Scaffold created: agents (brain/videodb/brightdata/aggregator/recommender), scoring, pipeline, CLI
- **VideoDB: LIVE & working** — youtube_search → upload → index_spoken_words → search(aspect); real timestamped transcript evidence (MKBHD/Mrwhosetheboss). ~45-60s/video.
- **Bright Data: LIVE & working** — SERP API zone named `aiforge` (set `BRIGHTDATA_ZONE=aiforge` in .env); `POST api.brightdata.com/request` with Bearer token + brd_json=1; returns real Reddit threads (URL + snippet) via `site:reddit.com "<product>" review`.
- Aggregator + recommender require `ANTHROPIC_API_KEY` (working)
- **Parallelized**: products + per-product videos ingest concurrently (ThreadPoolExecutor); full `--no-cache` run ~2 min (was ~5-8 min). Bottleneck is I/O wait on VideoDB cloud, not local compute — Nosana/GPU wouldn't help unless self-hosting ASR/LLM.
- **Aggregator guard**: drops junk/placeholder claims + retries once on degenerate output (fixes the Nothing Phone "placeholder" glitch).
- Known limitation: simple scoring (Σtop pros − Σtop cons) can rank a flagship below budget; tune TOP_N / weights or add per-tier normalization
- Run: `python main.py --no-cache` (first time / after enabling Bright Data)
```
