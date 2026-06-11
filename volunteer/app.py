#!/usr/bin/env python3
"""
Rex Manor Block Party — Volunteer signup service.

Collects volunteer signups (name, phone, email, and optional "I can help with"
checkboxes) from the rexmanor.org website and stores them in a local SQLite DB.

The signup form itself is a static Hugo page at /volunteer/ on rexmanor.org.
That form POSTs to /volunteer/submit, which nginx proxies to this app via a
uWSGI unix socket.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, request, Response
from markupsafe import escape

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "volunteers.db"

# Canonical list of help options. Keys are stored; labels are shown on the form.
HELP_OPTIONS = [
    ("setup", "Set up chairs / tables"),
    ("cook", "Cook"),
    ("fliers", "Distribute fliers"),
    ("teardown", "Tear down"),
    ("pickup", "Pick up food day before"),
    ("foodprep", "Food prep day before"),
    ("other", "Other"),
]
VALID_HELP_KEYS = {key for key, _ in HELP_OPTIONS}

app = Flask(__name__)


def init_db():
    """Create the volunteers table if it does not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS volunteers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                help TEXT,
                other_text TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        # Migrate older DBs that predate the free-text "Other" field.
        cols = {row[1] for row in conn.execute("PRAGMA table_info(volunteers)")}
        if "other_text" not in cols:
            conn.execute("ALTER TABLE volunteers ADD COLUMN other_text TEXT")
        conn.commit()


init_db()


def page(title, body):
    """Wrap a fragment of HTML in a minimal styled response page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} — Rex Manor Block Party</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
           max-width: 640px; margin: 4rem auto; padding: 0 1.25rem; line-height: 1.6; color: #1f2937; }}
    h1 {{ font-size: 1.6rem; }}
    a.button {{ display: inline-block; margin-top: 1.5rem; padding: 0.6rem 1.2rem;
               background: #2563eb; color: #fff; border-radius: 0.5rem; text-decoration: none; }}
    .card {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 0.75rem; padding: 1.5rem 1.75rem; }}
  </style>
</head>
<body>
  <div class="card">
    {body}
  </div>
</body>
</html>"""


@app.route("/volunteer/submit", methods=["POST"])
def submit():
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    email = (request.form.get("email") or "").strip()
    help_keys = [k for k in request.form.getlist("help") if k in VALID_HELP_KEYS]
    other_text = (request.form.get("other_text") or "").strip()
    # If they typed something in the "Other" blank, treat that as opting in.
    if other_text and "other" not in help_keys:
        help_keys.append("other")

    # Validation: a name plus at least one way to reach them.
    errors = []
    if not name:
        errors.append("Please enter your name.")
    if not phone and not email:
        errors.append("Please provide a phone number or an email address so we can reach you.")

    if errors:
        items = "".join(f"<li>{escape(e)}</li>" for e in errors)
        body = (
            "<h1>Hold on a sec…</h1>"
            f"<ul>{items}</ul>"
            '<a class="button" href="/volunteer/">Back to the form</a>'
        )
        return Response(page("Please fix a couple things", body), status=400, mimetype="text/html")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO volunteers (name, phone, email, help, other_text, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                name,
                phone,
                email,
                json.dumps(help_keys),
                other_text,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()

    body = (
        f"<h1>Thank you, {escape(name)}! 🎉</h1>"
        "<p>You're signed up to help with the Rex Manor neighborhood block party. "
        "We'll be in touch with details closer to the event.</p>"
        '<a class="button" href="https://rexmanor.org/">Back to the website</a>'
    )
    return Response(page("Thank you!", body), mimetype="text/html")


@app.route("/volunteer/health", methods=["GET"])
def health():
    return Response("ok", mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5099, debug=True)
