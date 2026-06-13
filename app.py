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

from src import answer, pipeline, report  # noqa: E402

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
CACHE = ROOT / ".cache"


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    no_cache: bool = False


app = FastAPI(title="Tech Review Assistant", version="1.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.post("/api/ask")
def ask(req: AskRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(400, "Question cannot be empty")

    if req.no_cache and CACHE.exists():
        shutil.rmtree(CACHE)

    from src import priorities

    try:
        recs = pipeline.run(verbose=False, question=question)
    except Exception as e:
        raise HTTPException(500, f"Pipeline failed: {e}") from e

    import config

    products = [p["name"] for p in config.PRODUCTS]
    prefs = priorities.parse(question)
    bullets = answer.summarize(question, recs, priority_categories=prefs)
    return report.to_api_response(
        question=question,
        summary_bullets=bullets,
        priorities=priorities.labels(prefs),
        priority_categories=prefs,
        recommendations=recs,
        products_compared=products,
    )
