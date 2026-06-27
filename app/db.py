from __future__ import annotations

import sqlite3

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  source TEXT,
  title TEXT, company TEXT, location TEXT,
  deadline TEXT, deadline_db TEXT, publish_date TEXT,
  salary TEXT, salary_approx INTEGER,
  experience TEXT, description TEXT,
  url TEXT, score INTEGER, overqualified INTEGER,
  why TEXT, matched TEXT, status TEXT DEFAULT 'new',
  created_at TEXT
);
"""


def conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init() -> None:
    with conn() as c:
        c.executescript(SCHEMA)
        cols = {r[1] for r in c.execute("PRAGMA table_info(jobs)").fetchall()}
        if "source" not in cols:
            c.execute("ALTER TABLE jobs ADD COLUMN source TEXT")


def all_ids() -> set[str]:
    with conn() as c:
        return {r[0] for r in c.execute("SELECT id FROM jobs").fetchall()}


def upsert_job(j: dict) -> None:
    with conn() as c:
        c.execute(
            """INSERT INTO jobs
            (id,source,title,company,location,deadline,deadline_db,publish_date,salary,salary_approx,
             experience,description,url,score,overqualified,why,matched,status,created_at)
            VALUES
            (:id,:source,:title,:company,:location,:deadline,:deadline_db,:publish_date,:salary,:salary_approx,
             :experience,:description,:url,:score,:overqualified,:why,:matched,'new',:created_at)
            ON CONFLICT(id) DO UPDATE SET
              score=excluded.score, why=excluded.why, salary=excluded.salary,
              salary_approx=excluded.salary_approx, overqualified=excluded.overqualified,
              matched=excluded.matched, deadline=excluded.deadline, deadline_db=excluded.deadline_db
            WHERE jobs.status <> 'deleted'""",
            j,
        )


def list_jobs(min_score: int = 0, include_applied: bool = True) -> list[dict]:
    q = "SELECT * FROM jobs WHERE score >= ? AND status <> 'deleted' "
    if not include_applied:
        q += "AND status <> 'applied' "
    q += "ORDER BY score DESC, deadline_db ASC"
    with conn() as c:
        return [dict(r) for r in c.execute(q, (min_score,)).fetchall()]


def get_job(jid: str) -> dict | None:
    with conn() as c:
        r = c.execute("SELECT * FROM jobs WHERE id = ?", (jid,)).fetchone()
        return dict(r) if r else None


def set_status(jid: str, status: str) -> None:
    with conn() as c:
        c.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, jid))
