"""CLI entry point for the tech-review assistant.

    python main.py            # run the pipeline, print ranked recommendations
    python main.py --no-cache # ignore the scrape cache and re-gather

Requires TOKENROUTER_API_KEY (from tokenrouter.com) in .env. VideoDB / Bright Data keys are optional —
without them the research agents use mock evidence so the demo runs offline.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src import pipeline
from src.schemas import Recommendation


def _print_report(recs: list[Recommendation]) -> None:
    print("\n" + "=" * 64)
    print("  TECH REVIEW ASSISTANT — PHONES (best across tiers)")
    print("=" * 64)
    for r in recs:
        print(f"\n[{r.bucket}]  {r.product}  ({r.tier})")
        print(f"  score={r.product_score:.0f}   confidence={r.confidence}")
        print(f"  {r.rationale}")
        if r.top_pros:
            print("  + Pros:")
            for c in r.top_pros:
                print(f"      • {c.text}  (videos={c.v}, reddit={c.r})")
                for e in c.evidence[:2]:
                    loc = f" @{e.timestamp}" if e.timestamp else ""
                    print(f"          ↳ {e.source}{loc}: {e.url}")
        if r.top_cons:
            print("  - Cons:")
            for c in r.top_cons:
                print(f"      • {c.text}  (videos={c.v}, reddit={c.r})")
                for e in c.evidence[:2]:
                    loc = f" @{e.timestamp}" if e.timestamp else ""
                    print(f"          ↳ {e.source}{loc}: {e.url}")
    print("\n" + "=" * 64)


def main() -> int:
    ap = argparse.ArgumentParser(description="Evidence-based tech review assistant")
    ap.add_argument("--no-cache", action="store_true", help="ignore the scrape cache")
    ap.add_argument("--quiet", action="store_true", help="suppress progress logs")
    args = ap.parse_args()

    if args.no_cache:
        cache_dir = Path(__file__).resolve().parent / ".cache"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)

    recs = pipeline.run(verbose=not args.quiet)
    _print_report(recs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
