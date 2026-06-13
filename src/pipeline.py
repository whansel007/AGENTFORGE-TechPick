"""Orchestrates the full pipeline (matches the diagram in memory.md):

  Brain -> Research (VideoDB + Bright Data) -> Aggregator -> Scoring -> Recommender

Products are processed CONCURRENTLY — each product's work is dominated by I/O
waits on VideoDB / Bright Data / Claude, so a thread pool collapses the wall-clock
to roughly the slowest single product instead of the sum of all three.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from src.agents import aggregator, brain, brightdata_agent, recommender, videodb_agent
from src.schemas import ProductClaims, Recommendation


def _process(product: dict, job: dict, verbose: bool) -> tuple[ProductClaims, str]:
    vids = videodb_agent.gather(product, job["channels"], job)
    reddit = brightdata_agent.gather(product, job)
    if verbose:
        print(f"[research] {product['name']}: {len(vids)} video + "
              f"{len(reddit)} reddit evidence items")

    claims = aggregator.aggregate(product["name"], vids + reddit)
    if verbose:
        print(f"[aggregate] {product['name']}: "
              f"{len(claims.pros)} pros / {len(claims.cons)} cons")
    return claims, product["tier"]


def run(verbose: bool = True, question: str | None = None) -> list[Recommendation]:
    from src import priorities

    job = brain.build_job()
    products = job["products"]
    prefs = priorities.parse(question) if question else []
    if verbose:
        print(f"[brain] category={job['category']} scope={job['price_scope']} "
              f"products={[p['name'] for p in products]}")
        if prefs:
            print(f"[brain] priorities={prefs}")

    # Fan out across products; ex.map preserves input order.
    with ThreadPoolExecutor(max_workers=max(1, len(products))) as ex:
        scored = list(ex.map(lambda p: _process(p, job, verbose), products))

    return recommender.recommend(scored, priorities=prefs or None)
