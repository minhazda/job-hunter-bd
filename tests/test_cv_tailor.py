from app import cv_tailor

_BASE_TEX = "\\begin{document}\n\\section*{Summary}\nHi\n\\end{document}"


def test_strip_fence_extracts_latex_from_markdown_fence():
    raw = "Here you go:\n```latex\n\\documentclass{article}\n\\begin{document}\nHi\n\\end{document}\n```"
    out = cv_tailor._strip_fence(raw)
    assert out.startswith("\\documentclass")
    assert out.endswith("\\end{document}")


def test_template_tailor_inserts_objective_before_summary(monkeypatch):
    monkeypatch.setattr(cv_tailor, "base_tex", lambda: _BASE_TEX)
    job = {"title": "Data Scientist", "company": "Acme", "matched": '["Python", "SQL"]'}
    tex = cv_tailor._template_tailor(job)
    assert "Data Scientist" in tex
    assert "Acme" in tex
    assert tex.index("Objective") < tex.index("Summary")


def test_tailor_falls_back_to_template_when_gemini_fails(monkeypatch):
    def _boom(jd):
        raise RuntimeError("bad key")

    monkeypatch.setattr(cv_tailor, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(cv_tailor, "_gemini_tailor", _boom)
    monkeypatch.setattr(cv_tailor, "base_tex", lambda: _BASE_TEX)

    result = cv_tailor.tailor({"title": "X", "company": "Y", "matched": "[]"})
    assert result["mode"].startswith("template (Gemini failed")
    assert "Objective" in result["latex"]


def test_tailor_uses_gemini_when_available(monkeypatch):
    monkeypatch.setattr(cv_tailor, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(cv_tailor, "GEMINI_MODEL", "gemini-test")
    monkeypatch.setattr(cv_tailor, "_gemini_tailor", lambda jd: "\\documentclass{article}\\begin{document}ok\\end{document}")

    result = cv_tailor.tailor({"title": "X", "company": "Y", "matched": "[]"})
    assert result["mode"] == "gemini (gemini-test)"
