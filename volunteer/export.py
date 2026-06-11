#!/usr/bin/env python3
"""Dump volunteer signups to CSV on stdout.  Usage: python3 export.py"""
import csv
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "volunteers.db"
HELP_LABELS = {
    "setup": "Set up chairs / tables",
    "cook": "Cook",
    "fliers": "Distribute fliers",
    "teardown": "Tear down",
    "pickup": "Pick up food day before",
    "foodprep": "Food prep day before",
    "other": "Other",
}

with sqlite3.connect(DB_PATH) as conn:
    rows = conn.execute(
        "SELECT id, name, phone, email, help, other_text, created_at FROM volunteers ORDER BY id"
    ).fetchall()

writer = csv.writer(sys.stdout)
writer.writerow(
    ["id", "name", "phone", "email", "can help with", "other (specify)", "signed up (UTC)"]
)
for r in rows:
    help_keys = json.loads(r[4] or "[]")
    help_str = "; ".join(HELP_LABELS.get(k, k) for k in help_keys)
    writer.writerow([r[0], r[1], r[2], r[3], help_str, r[5], r[6]])
