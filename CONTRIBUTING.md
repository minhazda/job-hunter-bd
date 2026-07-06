# Contributing to Job Hunter BD

Thanks for helping make job hunting easier for people in Bangladesh. 🙌

## Ways to contribute

- **Add a job source.** Write a `*_fetch(keyword, ...) -> list[RawJob]` function in
  `app/scraper.py` and add its name to `SOURCES`. Normalisation, scoring, dedup and the
  UI all pick it up automatically. Good candidates: Skill.jobs, Shomvob, company career pages.
- **Improve scoring** for fields beyond data/IT (accounting, marketing, engineering, teaching).
- **Fix bugs / improve the UI** in `app/static/index.html`.
- **Docs & translations** (Bangla README welcome).

## Setup

```bash
git clone https://github.com/minhazda/job-hunter-bd.git
cd job-hunter-bd
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp profile.example.yaml profile.yaml
python -m uvicorn app.main:app --port 8077
```

## Pull requests

1. Fork, branch, make your change.
2. Keep it focused — one feature/fix per PR.
3. Test that a scrape still runs and the UI loads.
4. Open the PR with a short description of what and why.

## Ground rules

- Only scrape **public** endpoints; don't add anything that needs someone's login credentials.
- The tool must never auto-submit an application — keep the human in the loop.
- Be kind in reviews and issues.

Questions? Open an issue.
