from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def load_profile() -> dict:
    with open(ROOT / "profile.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


PROFILE = load_profile()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
TAILOR_MODEL = os.environ.get("RAG_TAILOR_MODEL", "claude-sonnet-4-6").strip()
DB_PATH = ROOT / "data" / "jobs.db"
