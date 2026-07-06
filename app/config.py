from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def load_profile() -> dict:
    # Prefer the user's own profile.yaml; fall back to the shipped example so a
    # fresh clone runs out of the box before you've personalised it.
    path = ROOT / "profile.yaml"
    if not path.exists():
        path = ROOT / "profile.example.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


PROFILE = load_profile()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
TAILOR_MODEL = os.environ.get("RAG_TAILOR_MODEL", "claude-sonnet-4-6").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
DB_PATH = ROOT / "data" / "jobs.db"
