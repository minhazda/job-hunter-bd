from app import db


def _job(**overrides):
    base = {
        "id": "bdjobs:1", "source": "bdjobs", "title": "T", "company": "C", "location": "L",
        "deadline": "", "deadline_db": "", "publish_date": "", "salary": "", "salary_approx": 0,
        "experience": "", "description": "short", "url": "", "score": 10, "overqualified": 0,
        "why": "", "matched": "[]", "created_at": "2026-01-01T00:00:00",
    }
    base.update(overrides)
    return base


def test_upsert_updates_description_on_conflict(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "jobs.db")
    db.init()
    db.upsert_job(_job())
    assert db.get_job("bdjobs:1")["description"] == "short"

    db.upsert_job(_job(description="a much longer enriched description fetched on rescan", score=20))
    updated = db.get_job("bdjobs:1")
    assert updated["description"] == "a much longer enriched description fetched on rescan"
    assert updated["score"] == 20


def test_upsert_does_not_resurrect_deleted_jobs(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "jobs.db")
    db.init()
    db.upsert_job(_job())
    db.set_status("bdjobs:1", "deleted")

    db.upsert_job(_job(score=99))
    reloaded = db.get_job("bdjobs:1")
    assert reloaded["status"] == "deleted"
    assert reloaded["score"] == 10
