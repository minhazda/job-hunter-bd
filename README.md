# Job Hunter BD

A personal job-search cockpit for the Bangladesh market. Scrapes **bdjobs** and **LinkedIn**,
scores every posting against your profile, and for each job gives you: match score, overqualified
flag, salary (real or estimated), deadline, location, a "why apply" line, the full JD, a one-click
**tailored-CV LaTeX generator** (Overleaf-ready), an **Apply** button, and a **Delete** button.
Optionally emails you a **daily digest** of new matches.

Everything runs locally. The only outbound traffic is the job-site requests and (if enabled) the
Claude call for CV tailoring and the Gmail send for the digest.

---

## 1. First-time setup (once)

Requires Python 3.11-3.14.

```powershell
cd F:\Automation\job-hunter-bd
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env          # then edit .env (optional keys, see section 4)
```

## 2. Run the app (every time you want to job-hunt)

```powershell
cd F:\Automation\job-hunter-bd
.\run.ps1
```

`run.ps1` creates the venv on first use, starts the server, and opens your browser to
**http://127.0.0.1:8077**. Click **Scrape** to pull fresh jobs. Press **Ctrl+C** in the terminal to stop.

> If PowerShell blocks the script: `powershell -ExecutionPolicy Bypass -File .\run.ps1`
> Or run it manually: `.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8077`

### Using it
- **Scrape** — pulls every keyword in `profile.yaml` from both sources. Re-run anytime; new jobs
  are added, deleted ones stay hidden.
- **min score / hide applied** — filter the list.
- Per job: **Apply** (opens the posting, marks it applied), **Generate tailored CV** (LaTeX modal:
  Copy / Download `.tex` / Open in Overleaf), **Show JD**, **Delete**.

## 3. Daily email digest (optional, recommended for intensive use)

`digest.py` scrapes, stores, and emails you only the **new** matches above a score threshold.

Test it once:
```powershell
.\.venv\Scripts\python.exe digest.py
```
Without Gmail creds it just prints the new jobs. With them (section 4) it emails you.

**Schedule it daily (Windows Task Scheduler):**
```powershell
schtasks /create /tn "JobHunterBD Digest" /sc daily /st 08:30 ^
  /tr "powershell -ExecutionPolicy Bypass -File F:\Automation\job-hunter-bd\digest.ps1"
```
Runs every day at 08:30. Change `/st` for a different time, or `/sc hourly` for more frequent.
Remove it later with: `schtasks /delete /tn "JobHunterBD Digest" /f`.

## 4. Optional keys (`.env`)

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Turns on **Claude-tailored** CVs (rewrites Summary/Projects per JD). Without it, a template tailoring is used. |
| `GMAIL_USER`, `GMAIL_APP_PASSWORD` | Enable the email digest. Use a Gmail **App Password** (Google Account → Security → 2-Step Verification → App passwords), not your normal password. |
| `DIGEST_TO` | Where to send the digest (defaults to `GMAIL_USER`). |
| `DIGEST_MIN_SCORE` | Only email jobs at/above this match score (default 45). |

## 5. Tune it (`profile.yaml`)

- `search_keywords` — what to search for (each is one query per source).
- `skills`, `target_roles` — drive the match score and "why apply".
- `seniority_years`, `locations_preferred` — tune scoring + the overqualified flag.
- `base_cv_tex_url` — the CV the tailoring starts from.

## Sources & how scoring works

- **bdjobs** via its public JSON API; **LinkedIn** via the public guest job-search endpoint
  (no login). Add more sources by adding a `*_fetch()` function in `app/scraper.py` and listing it
  in `SOURCES`.
- Score = role/title match (strongest) + skill coverage + location, with senior roles down-weighted
  (you have ~3 yrs) and entry/low-experience roles flagged **overqualified**.
- Salary shows the posting's value when given, else a role-based estimate marked `est.`.

## Layout

```
run.ps1 / digest.ps1     launchers
profile.yaml             your profile (drives everything)
digest.py                scrape + email new matches (scheduler entry point)
app/
  main.py                FastAPI routes + serves the UI
  scraper.py             bdjobs + linkedin sources -> normalised jobs
  matching.py            transparent 0-100 score + overqualified + "why"
  salary.py              real salary or role-based estimate
  cv_tailor.py           per-JD LaTeX (Claude if key set, else template)
  emailer.py             Gmail digest sender
  db.py                  SQLite store (data/jobs.db)
  static/index.html      single-page UI
```
