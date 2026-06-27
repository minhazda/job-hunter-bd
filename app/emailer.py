from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText


def configured() -> bool:
    return bool(os.environ.get("GMAIL_USER") and os.environ.get("GMAIL_APP_PASSWORD"))


def send(subject: str, html: str) -> None:
    user = os.environ.get("GMAIL_USER")
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    to = os.environ.get("DIGEST_TO") or user
    if not (user and pw):
        raise RuntimeError("Set GMAIL_USER and GMAIL_APP_PASSWORD in .env")
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    recipients = [a.strip() for a in to.split(",") if a.strip()]
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.sendmail(user, recipients, msg.as_string())
