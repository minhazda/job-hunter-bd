"""Reproducible metrics for the README case study.

Reads the local SQLite store the app has already populated and prints the
numbers quoted in README.md. Nothing here is hand-typed into the docs — run
this after a scrape and the figures regenerate from real data.

    .\\.venv\\Scripts\\python.exe benchmark.py
"""

from __future__ import annotations

from collections import Counter

from app.config import DB_PATH
from app import db


def main() -> None:
    if not DB_PATH.exists():
        print(f"No store yet at {DB_PATH}. Run a scrape first (.\\run.ps1 -> Scrape).")
        return

    db.init()
    with db.conn() as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM jobs").fetchall()]

    live = [r for r in rows if r["status"] != "deleted"]
    scores = [r["score"] for r in live if r["score"] is not None]
    by_source = Counter(r["source"] for r in live)

    def pct(n: int) -> str:
        return f"{100 * n / len(live):.0f}%" if live else "0%"

    print(f"Postings in store (live):        {len(live)}")
    print(f"  from bdjobs:                   {by_source.get('bdjobs', 0)}")
    print(f"  from linkedin:                 {by_source.get('linkedin', 0)}")
    print(f"Distinct companies:              {len({r['company'] for r in live if r['company']})}")
    print(f"Score range (min / avg / max):   {min(scores)} / {sum(scores) / len(scores):.1f} / {max(scores)}")
    print(f"Above digest threshold (>=45):   {sum(s >= 45 for s in scores)}  ({pct(sum(s >= 45 for s in scores))})")
    print(f"Strong matches (>=60):           {sum(s >= 60 for s in scores)}")
    print(f"Thin LinkedIn listings enriched: {sum(bool(r['description']) and len(r['description']) > 200 for r in live if r['source'] == 'linkedin')}")
    print(f"Postings with a real salary:     {sum(bool(r['salary']) and r['salary_approx'] == 0 for r in live)}")
    print(f"Flagged overqualified:           {sum(bool(r['overqualified']) for r in live)}")
    print()
    print("Core loop LLM cost: $0 (scoring, salary, dedup, ranking are all deterministic Python).")


if __name__ == "__main__":
    main()
