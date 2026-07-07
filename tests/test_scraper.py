from app import scraper


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None):
        return _FakeResponse(200, {"data": [{
            "JobDescription": "<p>Build <b>APIs</b>.</p>",
            "SkillsRequired": "Python, SQL",
            "AdditionJobRequirements": "",
            "EducationRequirements": "<ul><li>BSc</li></ul>",
        }]})


class _Fake404Client(_FakeClient):
    def get(self, url, params=None):
        return _FakeResponse(404, {})


def test_bdjobs_detail_strips_html_and_joins_fields(monkeypatch):
    monkeypatch.setattr(scraper.httpx, "Client", _FakeClient)
    text = scraper.bdjobs_detail("123")
    assert "Build APIs" in text
    assert "Python, SQL" in text
    assert "BSc" in text
    assert "<" not in text


def test_bdjobs_detail_returns_empty_on_non_200(monkeypatch):
    monkeypatch.setattr(scraper.httpx, "Client", _Fake404Client)
    assert scraper.bdjobs_detail("x") == ""


def test_enrich_dispatches_bdjobs_detail_for_thin_listings(monkeypatch):
    calls = []

    def fake_bdjobs_fetch(kw, rpp=40, pages=1):
        return [scraper.RawJob(source="bdjobs", ext_id="1", title="T", description="short")]

    def fake_bdjobs_detail(jid):
        calls.append(jid)
        return "x" * 300

    monkeypatch.setattr(scraper, "bdjobs_fetch", fake_bdjobs_fetch)
    monkeypatch.setattr(scraper, "bdjobs_detail", fake_bdjobs_detail)

    jobs, errors = scraper.scrape_all(["kw"], sources=["bdjobs"], enrich=True)
    assert calls == ["1"]
    assert errors == []
    assert len(jobs[0]["description"]) > 200
