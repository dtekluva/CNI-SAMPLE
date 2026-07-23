"""
Email delivery via Mailgun (real outbound for the notifications app).

Credentials come from the environment only (MAILGUN_API_KEY / MAILGUN_DOMAIN) —
never committed. Delivery is gated by EMAIL_DELIVERY_ENABLED so tests and dev
never send. Email bodies are link-only (P5); this function does not add content.
"""
import os

import requests


def is_configured():
    return bool(os.getenv("MAILGUN_API_KEY") and os.getenv("MAILGUN_DOMAIN"))


def send_email(*, to, subject, text):
    api_key = os.getenv("MAILGUN_API_KEY", "")
    domain = os.getenv("MAILGUN_DOMAIN", "")
    if not api_key or not domain:
        return None  # not configured — caller keeps the queued Notification record
    from_addr = os.getenv("DEFAULT_FROM_EMAIL", f"CNI Group <postmaster@{domain}>")
    return requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={"from": from_addr, "to": to, "subject": subject, "text": text},
        timeout=15,
    )
