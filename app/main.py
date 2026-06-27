from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import cv_tailor, db, scraper
from .config import ANTHROPIC_API_KEY, PROFILE

app = FastAPI(title="Job Hunter BD")
db.init()
STATIC = Path(__file__).parent / "static"


class ScrapeReq(BaseModel):
    keywords: list[str] | None = None
    sources: list[str] | None = None
    rpp: int = 40


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.get("/api/profile")
def profile() -> dict:
    return {
        "name": PROFILE.get("name"),
        "title": PROFILE.get("title"),
        "keywords": PROFILE.get("search_keywords", []),
        "sources": scraper.SOURCES,
        "llm_enabled": bool(ANTHROPIC_API_KEY),
    }


@app.get("/api/jobs")
def jobs(min_score: int = 0, include_applied: bool = True) -> list[dict]:
    return db.list_jobs(min_score=min_score, include_applied=include_applied)


@app.post("/api/scrape")
def scrape_jobs(req: ScrapeReq) -> dict:
    kws = req.keywords or PROFILE.get("search_keywords", [])
    found, errors = scraper.scrape_all(kws, PROFILE, rpp=req.rpp, sources=req.sources)
    for j in found:
        db.upsert_job(j)
    return {
        "scraped": len(found),
        "keywords": kws,
        "sources": req.sources or scraper.SOURCES,
        "errors": errors,
    }


@app.delete("/api/jobs/{jid}")
def delete_job(jid: str) -> dict:
    db.set_status(jid, "deleted")
    return {"ok": True}


@app.post("/api/jobs/{jid}/applied")
def mark_applied(jid: str) -> dict:
    db.set_status(jid, "applied")
    return {"ok": True}


@app.post("/api/jobs/{jid}/tailor")
def tailor_cv(jid: str) -> dict:
    job = db.get_job(jid)
    if not job:
        raise HTTPException(404, "job not found")
    return cv_tailor.tailor(job)
