"""Scrape all sources, store, and email a digest of NEW high-match jobs.

Run on a schedule (see README -> Daily digest). Safe to run repeatedly: only jobs
not already in the database are emailed.
"""
from __future__ import annotations

import os
import sys

from app import db, emailer, scraper
from app.config import PROFILE

try:  # keep console output safe under Windows Task Scheduler (cp1252)
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


def build_html(jobs: list[dict], app_url: str) -> str:
    rows = []
    for j in jobs:
        color = "#16a34a" if j["score"] >= 70 else "#d97706" if j["score"] >= 45 else "#64748b"
        over = " &middot; OVERQUALIFIED" if j["overqualified"] else ""
        rows.append(
            f'<tr>'
            f'<td style="font-size:20px;font-weight:700;color:{color};padding:8px 10px;vertical-align:top">{j["score"]}</td>'
            f'<td style="padding:8px 10px;border-bottom:1px solid #e2e8f0">'
            f'<div style="font-weight:600">{j["title"]} <span style="color:#64748b;font-weight:400">&mdash; {j["company"]}</span></div>'
            f'<div style="color:#475569;font-size:13px">{j["source"]}{over} &middot; {j["location"] or "&mdash;"} &middot; '
            f'deadline: {j["deadline"] or "&mdash;"} &middot; {j["salary"]}</div>'
            f'<div style="color:#334155;font-size:13px;margin-top:2px">{j["why"]}</div>'
            f'<div style="margin-top:4px"><a href="{j["url"]}">Apply / view &rarr;</a></div>'
            f'</td></tr>'
        )
    return (
        '<div style="font-family:system-ui,Arial,sans-serif;max-width:700px">'
        f'<h2>Job Hunter BD &mdash; {len(jobs)} new matches</h2>'
        f'<p style="color:#475569">Open the app to generate a tailored CV per job: <a href="{app_url}">{app_url}</a></p>'
        f'<table style="border-collapse:collapse;width:100%">{"".join(rows)}</table>'
        '</div>'
    )


def main() -> None:
    db.init()
    known = db.all_ids()
    found, errors = scraper.scrape_all(PROFILE.get("search_keywords", []), PROFILE, rpp=40)
    new = [j for j in found if j["id"] not in known]
    for j in found:
        db.upsert_job(j)

    min_score = int(os.environ.get("DIGEST_MIN_SCORE", "45"))
    digest = sorted((j for j in new if j["score"] >= min_score), key=lambda x: -x["score"])
    print(f"scraped={len(found)} new={len(new)} digest={len(digest)} errors={errors}")

    if not digest:
        print("No new jobs above threshold; no email sent.")
        return
    if not emailer.configured():
        print("Email not configured (set GMAIL_USER / GMAIL_APP_PASSWORD in .env). Showing here instead:")
        for j in digest[:25]:
            print(f"  [{j['score']}] {j['title']} — {j['company']} ({j['source']})")
        return

    app_url = os.environ.get("APP_URL", "http://127.0.0.1:8077")
    emailer.send(f"Job Hunter BD: {len(digest)} new matches", build_html(digest, app_url))
    print(f"Emailed {len(digest)} new jobs to {os.environ.get('DIGEST_TO') or os.environ.get('GMAIL_USER')}.")


if __name__ == "__main__":
    main()
