from __future__ import annotations

# Approximate monthly gross BDT ranges by role (used only when the posting hides salary).
RANGES: dict[str, tuple[int, int]] = {
    "machine learning": (70000, 170000),
    "ml engineer": (70000, 170000),
    "ai engineer": (70000, 170000),
    "data scientist": (60000, 150000),
    "data engineer": (60000, 140000),
    "data analyst": (35000, 90000),
    "software engineer": (45000, 130000),
    "python": (40000, 110000),
    "research": (40000, 100000),
}
DEFAULT = (30000, 80000)
_HIDDEN = {"", "--", "-", "n/a", "na", "negotiable", "negotiable.", "as per company policy"}


def resolve(raw_salary: str | None, title: str) -> tuple[str, bool]:
    """Return (salary_text, is_approximate)."""
    s = (raw_salary or "").strip()
    if s.lower() not in _HIDDEN and any(ch.isdigit() for ch in s):
        return s, False
    tl = (title or "").lower()
    for key, (lo, hi) in RANGES.items():
        if key in tl:
            return f"~BDT {lo // 1000}k-{hi // 1000}k/mo (est.)", True
    lo, hi = DEFAULT
    return f"~BDT {lo // 1000}k-{hi // 1000}k/mo (est.)", True
