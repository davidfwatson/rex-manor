#!/usr/bin/env python3
"""
Push website volunteer signups (source='web' rows in the SQLite DB) up to the
organizers' Google Sheet, into a dedicated "Website Signups" tab so the master
roster layout is never touched.

Auth: a Google service-account key. Point SA_KEY at the JSON file (default:
./service-account.json) and share the spreadsheet with the service account's
email (as Editor).

Run:  ./sheets-venv/bin/python db_to_sheet.py
"""
import json
import os
import sqlite3
import sys
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "volunteers.db"
# Reuses the existing "linode-mv-yimby" service account (shared with james-form);
# the block party sheet must be shared with its client_email as Editor.
SA_KEY = Path(os.environ.get("SA_KEY", "/home/david/james-form/service-account.json"))
SPREADSHEET_ID = "1UPkPZF2vvvV1WHP1XKYBWRUF3bFPTs0dnauwELL4Aiw"
TAB = "Website Signups"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HELP_LABELS = {
    "setup": "Set up chairs / tables",
    "cook": "Cook",
    "fliers": "Distribute fliers",
    "teardown": "Tear down",
    "pickup": "Pick up food day before",
    "foodprep": "Food prep day before",
    "other": "Other",
}


def rows_from_db():
    conn = sqlite3.connect(DB)
    out = []
    for r in conn.execute(
        "SELECT name, COALESCE(address,''), phone, email, help, "
        "COALESCE(other_text,''), created_at "
        # 'web' and 'web+sheet' = signed up via the website (latter also in the
        # master roster after a merge). Pure 'sheet' rows are excluded.
        "FROM volunteers WHERE COALESCE(source,'web') LIKE 'web%' ORDER BY id"
    ):
        name, addr, phone, email, help_json, other, created = r
        keys = json.loads(help_json or "[]")
        can_help = "; ".join(HELP_LABELS.get(k, k) for k in keys)
        notes = other.strip()
        out.append([name, addr, phone, email, can_help, notes, created])
    return out


def get_service():
    if not SA_KEY.exists():
        sys.exit(f"Service-account key not found at {SA_KEY}. "
                 f"Set SA_KEY or place the JSON there.")
    creds = Credentials.from_service_account_file(str(SA_KEY), scopes=SCOPES)
    sa_email = json.load(open(SA_KEY)).get("client_email", "?")
    print(f"Authenticating as service account: {sa_email}")
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def ensure_tab(svc):
    meta = svc.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    titles = [s["properties"]["title"] for s in meta["sheets"]]
    if TAB not in titles:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": [{"addSheet": {"properties": {"title": TAB}}}]},
        ).execute()
        print(f"Created tab '{TAB}'.")
    else:
        print(f"Tab '{TAB}' already exists; refreshing it.")


def main():
    svc = get_service()
    ensure_tab(svc)
    rows = rows_from_db()
    header = ["Name", "Address", "Cell Number", "email",
              "Can help with", "Notes / other", "Signed up (UTC)"]
    values = [header] + rows
    # Clear then write, so re-runs stay idempotent.
    svc.spreadsheets().values().clear(
        spreadsheetId=SPREADSHEET_ID, range=f"'{TAB}'!A1:Z10000"
    ).execute()
    svc.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"'{TAB}'!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()
    print(f"Wrote {len(rows)} website signups to the '{TAB}' tab.")
    print(f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")


if __name__ == "__main__":
    main()
