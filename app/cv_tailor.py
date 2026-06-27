from __future__ import annotations

import functools
import json

import httpx

from .config import ANTHROPIC_API_KEY, GEMINI_API_KEY, GEMINI_MODEL, PROFILE, TAILOR_MODEL

_FALLBACK_TEX = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2cm]{geometry}\usepackage{hyperref}\usepackage{enumitem}
\setlength{\parindent}{0pt}\pagestyle{empty}
\begin{document}
{\Large\textbf{MD Minhazur Rahman}}\\
Data Scientist / Machine Learning Engineer\\
\href{mailto:minhazurrahman.ds@gmail.com}{minhazurrahman.ds@gmail.com} \textbar\
\href{https://github.com/minhazda}{github.com/minhazda} \textbar\
\href{https://www.linkedin.com/in/mohammadminhaz/}{linkedin.com/in/mohammadminhaz}
\section*{Summary}
MSc Data Science (Greenwich), 3+ years industry data/IT experience. Production ML on GCP Cloud Run.
\section*{Selected Projects}
\begin{itemize}[leftmargin=1.2em]
  \item Demand forecasting MLOps (LightGBM, FastAPI, Terraform, Cloud Run) -- MAE -40.8\%.
  \item Card-fraud detection (imbalanced) -- ROC-AUC 0.90, PR-AUC 0.49.
  \item Real-data forecasting (UCI Online Retail II, DuckDB) -- +26.3\% MAE.
  \item Privacy-preserving RAG agent (LangGraph, LLM-as-judge).
\end{itemize}
\end{document}
"""

_SYSTEM = (
    "You tailor a candidate's LaTeX CV to one specific job. Return ONLY compilable LaTeX "
    "(no commentary, no markdown fences). Rules: keep every real fact, link, and metric; "
    "reorder and reword the Summary and Selected Projects to foreground what the job asks for; "
    "keep it to at most two pages; do not invent experience."
)


@functools.lru_cache(maxsize=1)
def base_tex() -> str:
    url = PROFILE.get("base_cv_tex_url")
    if url:
        try:
            r = httpx.get(url, timeout=20)
            if r.status_code == 200 and r.text.lstrip().startswith("\\documentclass"):
                return r.text
        except Exception:  # noqa: BLE001
            pass
    return _FALLBACK_TEX


def _prompt(jd: str) -> str:
    return f"BASE CV (LaTeX):\n{base_tex()}\n\nJOB:\n{jd}\n\nReturn the tailored LaTeX only."


def tailor(job: dict) -> dict:
    jd = (
        f"Title: {job.get('title')}\nCompany: {job.get('company')}\n"
        f"Location: {job.get('location')}\nExperience: {job.get('experience')}\n"
        f"Description:\n{job.get('description')}"
    )
    if GEMINI_API_KEY:
        try:
            return {"latex": _gemini_tailor(jd), "mode": f"gemini ({GEMINI_MODEL})"}
        except Exception as exc:  # noqa: BLE001
            return {"latex": _template_tailor(job), "mode": f"template (Gemini failed: {exc})"}
    if ANTHROPIC_API_KEY:
        try:
            return {"latex": _claude_tailor(jd), "mode": "claude"}
        except Exception as exc:  # noqa: BLE001
            return {"latex": _template_tailor(job), "mode": f"template (Claude failed: {exc})"}
    return {"latex": _template_tailor(job), "mode": "template"}


def _gemini_tailor(jd: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    body = {
        "system_instruction": {"parts": [{"text": _SYSTEM}]},
        "contents": [{"parts": [{"text": _prompt(jd)}]}],
        "generationConfig": {
            "maxOutputTokens": 8192,
            "temperature": 0.3,
            "thinkingConfig": {"thinkingBudget": 0},  # no "thinking" parts in the reply
        },
    }
    r = httpx.post(url, params={"key": GEMINI_API_KEY}, json=body, timeout=90)
    r.raise_for_status()
    data = r.json()
    parts = data["candidates"][0]["content"]["parts"]
    # ignore any thought parts; keep only real output text
    txt = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    return _strip_fence(txt)


def _claude_tailor(jd: str) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=TAILOR_MODEL,
        max_tokens=4000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": _prompt(jd)}],
    )
    txt = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text").strip()
    return _strip_fence(txt)


def _strip_fence(txt: str) -> str:
    import re

    txt = txt.strip()
    if "```" in txt:
        m = re.search(r"```(?:latex)?\s*(.*?)```", txt, re.DOTALL)
        if m:
            txt = m.group(1).strip()
    # If the model added any prose around it, keep just the LaTeX document.
    start = txt.find("\\documentclass")
    if start > 0:
        txt = txt[start:]
    end = txt.rfind("\\end{document}")
    if end != -1:
        txt = txt[: end + len("\\end{document}")]
    return txt.strip()


def _template_tailor(job: dict) -> str:
    tex = base_tex()
    try:
        matched = json.loads(job.get("matched") or "[]")
    except Exception:  # noqa: BLE001
        matched = []
    focus = ", ".join(matched[:8]) or "production ML, Python, data analysis"
    objective = (
        f"\\section*{{Objective}}\n"
        f"Applying for \\textbf{{{_tex_escape(job.get('title',''))}}} at "
        f"{_tex_escape(job.get('company',''))}. Most relevant strengths for this role: {_tex_escape(focus)}. "
        f"Full project links and metrics below.\n\n"
    )
    for marker in ("\\section{Summary}", "\\section*{Summary}"):
        if marker in tex:
            return tex.replace(marker, objective + marker, 1)
    return tex.replace("\\begin{document}", "\\begin{document}\n" + objective, 1)


def _tex_escape(s: str) -> str:
    for a, b in [("&", "\\&"), ("%", "\\%"), ("$", "\\$"), ("#", "\\#"), ("_", "\\_")]:
        s = s.replace(a, b)
    return s
