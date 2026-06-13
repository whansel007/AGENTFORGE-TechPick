"""Web UI for the tech review assistant.

    uvicorn app:app --reload
    open http://127.0.0.1:8000
"""
from __future__ import annotations

import shutil
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

import config  # noqa: E402
from src import answer, pipeline, priorities, report  # noqa: E402

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
CACHE = ROOT / ".cache"


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    no_cache: bool = False


app = FastAPI(
    title="TechPick",
    description=(
        "Agent Forge hackathon — evidence-based phone recommendations. "
        "Multi-agent pipeline: Brain → Research (VideoDB + Bright Data) → "
        "Aggregator → Scoring → Recommender. Citations, explainable scores, "
        "question-aware priority weighting."
    ),
    version="1.0",
)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/about")
def about():
    """Structured project metadata for evaluators and tooling."""
    return {
        "name": "TechPick",
        "event": "Agent Forge Hackathon",
        "tagline": "Evidence-based phone recommendations with citations and explainable scores",
        "problem": "Phone buyers need aggregated, cited pros/cons from trusted reviewers — not ads or noise.",
        "solution": "Five-agent pipeline gathers VideoDB + Reddit evidence, aggregates claims via Claude, scores deterministically, and recommends with citations.",
        "agents": ["brain", "videodb", "brightdata", "aggregator", "recommender"],
        "pipeline": "Brain → Research → Aggregator → Scoring → Recommender",
        "sponsor_integrations": {
            "tokenrouter": "Claude LLM for aggregation and verdict summaries",
            "videodb": "YouTube transcript ingest and semantic search with timestamps",
            "bright_data": "Reddit SERP search and optional thread scrape",
        },
        "features": [
            "Citation-grounded pros and cons (YouTube timestamps, Reddit permalinks)",
            "Deterministic explainable scoring with collapsible points breakdown",
            "Question-aware priority weighting (battery, camera, value, etc.)",
            "Curated reviewer allowlist (MKBHD, Mrwhosetheboss, JerryRig, …)",
            "Concurrent per-product research with scrape-once disk cache",
            "Offline demo via realistic mock evidence",
            "Web UI and CLI entry points",
        ],
        "demo_questions": [
            "What's the best phone for battery life?",
            "I care most about camera and photos",
            "Best value phone across budget and mid tier?",
        ],
        "products_compared": [p["name"] for p in config.PRODUCTS],
        "docs": {"readme": "README.md", "submission": "SUBMISSION.md"},
        "run": {
            "web": "uvicorn app:app --reload",
            "cli": "python main.py",
            "url": "http://127.0.0.1:8000",
        },
    }


@app.post("/api/ask")
def ask(req: AskRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(400, "Question cannot be empty")

    if req.no_cache and CACHE.exists():
        shutil.rmtree(CACHE)

    try:
        recs = pipeline.run(verbose=False, question=question)
    except Exception as e:
        raise HTTPException(500, f"Pipeline failed: {e}") from e

    prefs = priorities.parse(question)
    bullets = answer.summarize(question, recs, priority_categories=prefs)
    products = [p["name"] for p in config.PRODUCTS]
    return report.to_api_response(
        question=question,
        summary_bullets=bullets,
        priorities=priorities.labels(prefs),
        priority_categories=prefs,
        recommendations=recs,
        products_compared=products,
    )
