from __future__ import annotations

import re

SENIOR_TERMS = {"senior", "lead", "principal", "head", "manager", "director", "architect", "chief", "vp"}
JUNIOR_TERMS = {"intern", "internship", "trainee", "fresher", "entry", "junior", "apprentice"}


def _years_required(text: str) -> int | None:
    nums = [int(n) for n in re.findall(r"(\d+)\s*(?:\+|to|-|year)", (text or "").lower())]
    return min(nums) if nums else None


def score_job(raw: dict, profile: dict) -> tuple[int, bool, list[str], str]:
    """Return (score 0-100, overqualified, matched_skills, why_text)."""
    title = (raw.get("title") or "")
    desc = (raw.get("description") or "")
    exp = (raw.get("experience") or "")
    location = (raw.get("location") or "")
    title_l, tl_low = title, title.lower()
    # weight the title heavily by repeating it
    blob = f"{title_l} {title_l} {title_l} {exp} {desc}".lower()

    skills = [s.lower() for s in profile.get("skills", [])]
    roles = [r.lower() for r in profile.get("target_roles", [])]
    locs = [loc.lower() for loc in profile.get("locations_preferred", [])]

    matched = sorted({s for s in skills if s in blob}, key=len, reverse=True)
    role_hit = any(r in tl_low for r in roles)
    role_words = {w for r in roles for w in r.split() if len(w) > 2}
    title_words = set(re.findall(r"[a-z]+", tl_low))

    # Title relevance is the strongest signal (descriptions on bdjobs are sparse).
    if role_hit:
        score = 50.0
    elif role_words & title_words:
        score = 24.0  # partial: shares words like "data"/"analyst"/"ml" with a target role
    else:
        score = 0.0
    score += min(len(matched), 8) / 8 * 40  # up to 40 from skill coverage
    if any(loc in location.lower() for loc in locs):
        score += 5

    is_senior = any(s in tl_low for s in SENIOR_TERMS)
    is_junior = any(j in tl_low for j in JUNIOR_TERMS)
    yrs = _years_required(exp)
    my_years = int(profile.get("seniority_years", 3))

    overqualified = bool((is_junior or (yrs is not None and yrs <= 1)) and (role_hit or len(matched) >= 3))
    if overqualified:
        score += 8
    if is_senior and my_years < 5:
        score -= 15  # likely needs more seniority than you have

    score = max(0, min(100, round(score)))
    why = _why(title, matched, role_hit, overqualified, is_senior, yrs)
    return score, overqualified, matched, why


def _why(title, matched, role_hit, overq, is_senior, yrs) -> str:
    bits: list[str] = []
    if role_hit:
        bits.append("title matches a target role")
    if matched:
        bits.append("matches your skills: " + ", ".join(matched[:6]))
    if overq:
        bits.append("you're likely overqualified (entry/low-experience) — fast win")
    if is_senior:
        bits.append("senior-level — may want more years than you have")
    if yrs is not None:
        bits.append(f"asks ~{yrs}+ yrs experience")
    if not bits:
        bits.append("weak match — review the description before applying")
    return "; ".join(bits).capitalize() + "."
