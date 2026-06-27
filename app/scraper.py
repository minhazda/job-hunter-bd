from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

from . import matching, salary
from .config import PROFILE

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"

SOURCES = ["bdjobs", "linkedin"]


@dataclass
class RawJob:
    source: str
    ext_id: str
    title: str
    company: str = ""
    location: str = ""
    deadline: str = ""
    deadline_db: str = ""
    salary_raw: str = ""
    experience: str = ""
    description: str = ""
    url: str = ""


# --------------------------------------------------------------------------- #
# Source: bdjobs (public JSON API)
# --------------------------------------------------------------------------- #
_BDJOBS_API = "https://api.bdjobs.com/Jobs/api/JobSearch/GetJobSearch"
_BDJOBS_BLANK = [
    "Icat", "industry", "category", "org", "jobNature", "Fcat", "location", "Qot",
    "jobType", "jobLevel", "postedWithin", "deadline", "qAge", "Salary", "experience",
    "gender", "MExp", "genderB", "MPostings", "MCat", "version", "Newspaper", "armyp",
    "QDisablePerson", "pwd", "workplace", "facilitiesForPWD", "SaveFilterList",
    "UserFilterName", "HUserFilterName", "earlyJobAccess",
]


def _bdjobs_params(keyword: str, pg: int, rpp: int) -> dict:
    p = {k: "" for k in _BDJOBS_BLANK}
    p.update(keyword=keyword, pg=pg, rpp=rpp, isPro="0", ToggleJobs="true", isFresher="false")
    return p


def bdjobs_fetch(keyword: str, rpp: int = 40, pages: int = 1) -> list[RawJob]:
    out: list[RawJob] = []
    with httpx.Client(timeout=40, headers={"User-Agent": UA, "Accept": "application/json"}) as cl:
        for pg in range(1, pages + 1):
            r = cl.get(_BDJOBS_API, params=_bdjobs_params(keyword, pg, rpp))
            r.raise_for_status()
            data = r.json().get("data") or []
            if not data:
                break
            for raw in data:
                jid = str(raw.get("Jobid") or "").strip()
                if not jid or jid == "None":
                    continue
                out.append(RawJob(
                    source="bdjobs", ext_id=jid, title=raw.get("jobTitle") or "",
                    company=raw.get("companyName") or "", location=raw.get("location") or "",
                    deadline=raw.get("deadline") or "", deadline_db=raw.get("deadlineDB") or "",
                    salary_raw=raw.get("Salary") or "", experience=raw.get("experience") or "",
                    description=(raw.get("jobDescription") or raw.get("eduRec") or "").strip(),
                    url=f"https://bdjobs.com/h/details/{jid}?ln=1",
                ))
    return out


# --------------------------------------------------------------------------- #
# Source: LinkedIn (public guest job-search endpoint, no login)
# --------------------------------------------------------------------------- #
_LI_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def linkedin_fetch(keyword: str, location: str = "Bangladesh", pages: int = 2) -> list[RawJob]:
    out: list[RawJob] = []
    with httpx.Client(timeout=40, headers={"User-Agent": UA}, follow_redirects=True) as cl:
        for p in range(pages):
            r = cl.get(_LI_URL, params={"keywords": keyword, "location": location, "start": p * 25})
            if r.status_code != 200 or not r.text.strip():
                break
            soup = BeautifulSoup(r.text, "html.parser")
            cards = soup.select("li")
            if not cards:
                break
            for li in cards:
                a = li.select_one("a[href*='/jobs/view/']")
                title = li.select_one(".base-search-card__title")
                if not (a and title):
                    continue
                comp = li.select_one(".base-search-card__subtitle")
                loc = li.select_one(".job-search-card__location")
                when = li.select_one("time")
                href = (a.get("href") or "").split("?")[0]
                m = re.search(r"-(\d+)$", href) or re.search(r"(\d+)$", href)
                ext = m.group(1) if m else href
                posted = ("posted " + when.get("datetime")) if (when and when.get("datetime")) else ""
                out.append(RawJob(
                    source="linkedin", ext_id=str(ext), title=title.get_text(strip=True),
                    company=comp.get_text(strip=True) if comp else "",
                    location=loc.get_text(strip=True) if loc else "",
                    deadline=posted,  # LinkedIn guest gives a posted date, not a deadline
                    url=href,
                ))
    return out


# --------------------------------------------------------------------------- #
# Normalisation + aggregation
# --------------------------------------------------------------------------- #
def _build(r: RawJob, profile: dict) -> dict:
    score, overq, matched, why = matching.score_job(
        {"title": r.title, "description": r.description, "experience": r.experience, "location": r.location},
        profile,
    )
    sal, approx = salary.resolve(r.salary_raw, r.title)
    return {
        "id": f"{r.source}:{r.ext_id}",
        "source": r.source,
        "title": r.title,
        "company": r.company,
        "location": r.location,
        "deadline": r.deadline,
        "deadline_db": r.deadline_db,
        "publish_date": "",
        "salary": sal,
        "salary_approx": 1 if approx else 0,
        "experience": r.experience,
        "description": (r.description or "")[:1500],
        "url": r.url,
        "score": score,
        "overqualified": 1 if overq else 0,
        "why": why,
        "matched": json.dumps(matched),
        "created_at": dt.datetime.utcnow().isoformat(),
    }


def scrape_all(
    keywords: list[str],
    profile: dict | None = None,
    rpp: int = 40,
    sources: list[str] | None = None,
    location: str = "Bangladesh",
) -> tuple[list[dict], list[str]]:
    profile = profile or PROFILE
    sources = sources or SOURCES
    seen: dict[str, dict] = {}
    errors: list[str] = []
    for kw in keywords:
        if "bdjobs" in sources:
            try:
                for r in bdjobs_fetch(kw, rpp=rpp):
                    seen[f"{r.source}:{r.ext_id}"] = _build(r, profile)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"bdjobs/{kw}: {exc}")
        if "linkedin" in sources:
            try:
                for r in linkedin_fetch(kw, location=location):
                    seen[f"{r.source}:{r.ext_id}"] = _build(r, profile)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"linkedin/{kw}: {exc}")
    return list(seen.values()), errors
