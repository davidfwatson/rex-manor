# Block Party Volunteer Signup Service

Small Flask/uWSGI app behind nginx that backs the **Volunteer** page on the
Hugo site (`content/volunteer/_index.md`). The form POSTs to `/volunteer/submit`;
nginx proxies that to this app over a unix socket, and signups are stored in a
local SQLite DB.

## Layout

| File | Purpose |
|------|---------|
| `app.py` | Flask app: validates and stores signups (`/volunteer/submit`). |
| `volunteer.ini` | uWSGI config (socket at `volunteer/volunteer.sock`). |
| `rex-manor-volunteer.service` | systemd unit (copy to `/etc/systemd/system/`). |
| `export.py` | Dump signups to CSV on stdout. |
| `import_sheet.py` | One-off: import the organizers' Google Sheet roster into the DB. |
| `db_to_sheet.py` | Push website signups up to a "Website Signups" tab in the sheet. |

## Not in git (gitignored — this repo is public)

- `venv/`, `sheets-venv/` — virtualenvs (rebuild from `requirements.txt`).
- `data/` — the SQLite DB and backups (**real signups, PII**).
- `sheet_snapshot.md` — copy of the roster sheet (**PII**).

## Common tasks

```bash
# Export signups to CSV
./venv/bin/python export.py > signups.csv

# Refresh the "Website Signups" tab in the Google Sheet (manual, not automated)
./sheets-venv/bin/python db_to_sheet.py

# Service control
sudo systemctl {status,restart} rex-manor-volunteer.service
```

## Google Sheets auth

`db_to_sheet.py` reuses the existing `linode-mv-yimby@…` service account key at
`/home/david/james-form/service-account.json`. The target sheet must be shared
with that service account's `client_email` as Editor.
