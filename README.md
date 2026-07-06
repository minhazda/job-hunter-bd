# Job Hunter BD 🇧🇩 — automate your job search, for free

**One command scrapes bdjobs and LinkedIn, scores every posting against *your* profile, tells you why each one fits (or doesn't), tailors a CV per job, and can email you a daily digest of only the new matches. Runs entirely on your own machine. The whole core loop costs ₹0 / $0 — no paid API required.**

Made for job seekers in Bangladesh who are tired of refreshing bdjobs and LinkedIn by hand. Instead of opening ten tabs every morning and re-reading the same listings, you run it once and get a ranked, deduplicated, explained shortlist — plus an Overleaf-ready tailored CV for any job with one click.

[![CI](https://github.com/minhazda/job-hunter-bd/actions/workflows/ci.yml/badge.svg)](https://github.com/minhazda/job-hunter-bd/actions/workflows/ci.yml) ![Python](https://img.shields.io/badge/python-3.11%E2%80%933.14-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Cost](https://img.shields.io/badge/core%20loop-%240-brightgreen)

> ⭐ If this helps your job hunt, please **star the repo** — it helps other job seekers find it.

---

## What you get

- **Two sources, one list** — bdjobs (public JSON API) + LinkedIn (public guest search), deduplicated.
- **A transparent match score (0–100)** for every job, with a plain-English *"why apply"* line — no black box.
- **Overqualified flag** so you don't waste time on entry-level roles, and **senior down-weighting** so you're not shown roles far above your level.
- **Real or estimated salary**, deadline, location, and the full JD inline.
- **One-click tailored CV** — reorders your CV's summary/projects for each job and gives you Copy / Download `.tex` / Open-in-Overleaf.
- **Optional daily email digest** of just the *new* matches above a score you choose.
- **100% local.** The only outbound traffic is the job-site requests and, if you opt in, your own CV-tailoring LLM and your own Gmail for the digest.

---

## Quickstart (free, ~3 minutes)

You need **Python 3.11–3.14** and **git**. Works on Windows, macOS, and Linux.

```bash
# 1. Get the code
git clone https://github.com/minhazda/job-hunter-bd.git
cd job-hunter-bd

# 2. Create a virtual environment and install
python -m venv .venv
# activate it:
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows PowerShell
pip install -r requirements.txt

# 3. Make it yours
cp profile.example.yaml profile.yaml     # copy … on Windows
#   then edit profile.yaml — your roles, skills, and locations

# 4. Run it
python -m uvicorn app.main:app --port 8077
```

Open **http://127.0.0.1:8077** and click **Scrape**. That's it — no API keys, no signup, no cost.

> **Windows shortcut:** instead of steps 2–4 you can just run `.\run.ps1`, which creates the venv, starts the server, and opens your browser. If PowerShell blocks it: `powershell -ExecutionPolicy Bypass -File .\run.ps1`.

### Using it
- **Scrape** pulls every keyword in your `profile.yaml` from both sources. Re-run anytime — new jobs are added, deleted ones stay hidden.
- Filter by **min score** or **hide applied**.
- Per job: **Apply** (opens the posting, marks it applied), **Generate tailored CV**, **Show JD**, **Delete**.

---

## It's free by default. Keys are optional.

The scraping, scoring, salary parsing, dedup and ranking are **plain Python — no key, no cost, ever.** You only add a key if you want the two optional extras:

| Want… | Add to `.env` | Cost |
|---|---|---|
| **AI-tailored CVs** (rewrites your summary/projects per job) | `GEMINI_API_KEY` — free tier at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | Free |
| …or via Claude instead | `ANTHROPIC_API_KEY` | Paid |
| **Daily email digest** | `GMAIL_USER` + `GMAIL_APP_PASSWORD` ([App Password](https://support.google.com/accounts/answer/185833), not your login) | Free |

Without a key, CV tailoring still works — it uses a template rewrite instead of an LLM. Copy `.env.example` to `.env` and fill in only what you want.

---

## Daily email digest (optional)

`digest.py` scrapes, stores, and emails you only the **new** matches above `DIGEST_MIN_SCORE` (default 45). Without Gmail creds it just prints them.

```bash
python digest.py            # test once
```

**Run it automatically every morning:**

<details>
<summary>Windows (Task Scheduler)</summary>

```powershell
schtasks /create /tn "JobHunterBD Digest" /sc daily /st 08:30 ^
  /tr "powershell -ExecutionPolicy Bypass -File %CD%\digest.ps1"
```
</details>

<details>
<summary>macOS / Linux (cron)</summary>

```bash
crontab -e
# add (adjust the path):
30 8 * * *  cd /path/to/job-hunter-bd && ./.venv/bin/python digest.py
```
</details>

---

## How the match score works (and why it's a rule engine, not a model)

`app/matching.py` returns `(score 0–100, overqualified, matched_skills, why)` — every number is explainable, because *you're* the one deciding whether to spend an evening on an application:

- **Title relevance is the strongest signal.** A title that hits one of your `target_roles` scores 50; one that just shares meaningful words scores 24.
- **Skill coverage** adds up to 40, scaled by how many of your `skills` appear in the posting.
- **Location match** adds 5.
- **Seniority correction:** senior/lead titles are down-weighted when you're below the bar; genuine entry-level roles get an *overqualified* "fast win" flag.

No training data, no model to retrain — just edit `profile.yaml` and the ranking changes instantly. Every job carries a `why` string so the ranking is auditable at a glance.

### Reproducible metrics

Run `python benchmark.py` after a scrape to print stats from your own store. From the author's run over **149 postings** across both sources (109 distinct companies): 38 surfaced above the digest threshold, 58 thin LinkedIn cards auto-enriched with their full JD, **$0 core-loop cost**.

---

## Configure it (`profile.yaml`)

| Field | What it does |
|---|---|
| `target_roles` | Job-title matching + overqualified detection |
| `skills` | Drives the score and the "why apply" line (lowercase) |
| `search_keywords` | One search query per line, per source |
| `seniority_years`, `locations_preferred` | Tune scoring and the overqualified flag |
| `base_cv_tex_url` | Raw URL of your LaTeX CV, used as the base for tailoring |

Your `profile.yaml` is **git-ignored** — your personal details never get committed.

---

## Contributing

PRs welcome — especially **new job sources** (add a `*_fetch()` returning `list[RawJob]` in `app/scraper.py` and list it in `SOURCES`; scoring, dedup and the UI pick it up unchanged) and better score tuning for other fields (accounting, marketing, engineering…). This started as data/IT-focused; it works for any field once you edit `profile.yaml`. See [CONTRIBUTING.md](CONTRIBUTING.md).

## How it's built

```
app/
  main.py        FastAPI routes + serves the UI
  scraper.py     bdjobs + linkedin -> normalised, deduped jobs
  matching.py    transparent 0-100 score + overqualified + "why"
  salary.py      real salary or role-based estimate
  cv_tailor.py   per-JD LaTeX (Gemini/Claude if key set, else template)
  emailer.py     Gmail digest sender
  db.py          SQLite store (idempotent upsert, soft delete)
  static/        single-page UI
benchmark.py     reproducible stats from your store
digest.py        scrape + email new matches (scheduler entry point)
```

Stack: Python · FastAPI · httpx · BeautifulSoup · SQLite. Optional: Gemini/Claude, Gmail SMTP.

---

## Notes & etiquette

- Scrapers hit **public** endpoints only; be reasonable with how often you scrape.
- The tool **never applies for you** — it ranks, explains, and drafts. You make every apply/skip call.
- Not affiliated with bdjobs or LinkedIn. Use responsibly and respect their terms.

## License

[MIT](LICENSE) — free to use, fork, and adapt. Built by [MD Minhazur Rahman](https://github.com/minhazda).
