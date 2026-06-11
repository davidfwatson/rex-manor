#!/usr/bin/env python3
"""
One-off: import the organizers' master volunteer roster (Google Sheet) into the
volunteers SQLite DB, merging with existing website signups.

- Parses only the people-tables from sheet_snapshot.md (the main roster, the
  Barron/Lambert mini-table, and the veg-prep assignment table). Ignores the
  job-definition, prep-checklist and shopping-list tables.
- Dedups within the sheet by email -> phone(last10) -> normalized name.
- Merges into the DB: if a sheet person matches an existing row (by email, phone
  or name) the existing row is kept and only its EMPTY fields are filled in;
  otherwise a new row is inserted with source='sheet'.
"""
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "volunteers.db"
SNAP = BASE / "sheet_snapshot.md"

# Rows in the main table that are section headers / non-people, not volunteers.
SKIP_NAMES = {"cut up fruit and vegetables", "name(s)", ""}


def norm_name(n):
    return re.sub(r"\s+", " ", (n or "").strip().lower())


def norm_phone(p):
    d = re.sub(r"\D", "", p or "")
    return d[-10:] if len(d) >= 10 else ""


def norm_email(e):
    e = (e or "").strip().lower()
    return e if "@" in e else ""


def split_row(line):
    # "| a | b | c |" -> ["a","b","c"]
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return cells


class Person:
    def __init__(self, name):
        self.name = name.strip()
        self.address = ""
        self.phone = ""
        self.email = ""
        self.jobs = []   # "jobs taken previously" + prep tasks
        self.notes = []  # free-form notes

    def absorb(self, address="", phone="", email="", job="", note=""):
        if address and not self.address:
            self.address = address
        if phone and not self.phone:
            self.phone = phone
        if email and not self.email:
            self.email = email
        if job and job not in self.jobs:
            self.jobs.append(job)
        if note and note not in self.notes:
            self.notes.append(note)

    def key(self):
        return norm_email(self.email) or norm_phone(self.phone) or norm_name(self.name)


def parse():
    text = SNAP.read_text()
    people = {}  # key -> Person

    def get(person_name):
        # find existing person by identity, else create
        return person_name  # placeholder; resolved in upsert()

    pending = []  # (name, address, phone, email, job, note)

    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = split_row(line)
        if not cells or all(c == "" or set(c) <= {":", "-"} for c in cells):
            continue
        name = cells[0].strip()
        if norm_name(name) in SKIP_NAMES:
            continue
        if set(cells[0]) <= {":", "-"}:  # separator row
            continue

        address = phone = email = job = note = ""
        n = len(cells)
        if n >= 6:                       # main roster table
            address, c2, c3, job = cells[1], cells[2], cells[3], cells[4]
            note = cells[5]
            # c2 is "Cell Number", c3 is "email" -- but data is sometimes misaligned
            email_field = c3
            if "@" in email_field:
                email = email_field
            elif email_field:           # not an email -> it's really a note
                note = (note + "; " + email_field).strip("; ")
            phone = c2
        elif n == 5:                     # veg-prep assignment table
            address, phone, email, job = cells[1], cells[2], cells[3], cells[4]
        elif n == 3:                     # Barron / Lambert mini-table
            address, phone = cells[1], cells[2]
        else:
            continue
        pending.append((name, address, phone, email, job, note))

    # Build deduped people, resolving identity progressively.
    for name, address, phone, email, job, note in pending:
        ek, pk, nk = norm_email(email), norm_phone(phone), norm_name(name)
        match = None
        for k, p in people.items():
            if (ek and norm_email(p.email) == ek) or \
               (pk and norm_phone(p.phone) == pk) or \
               (nk and norm_name(p.name) == nk):
                match = p
                break
        if match is None:
            match = Person(name)
            people[match.key() or nk or name] = match
        match.absorb(address, phone, email, job, note)
    return list(people.values())


def main():
    people = parse()
    conn = sqlite3.connect(DB)

    # schema: add columns used by the sheet import (safe if already present)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(volunteers)")}
    for col in ("address", "notes", "source"):
        if col not in cols:
            conn.execute(f"ALTER TABLE volunteers ADD COLUMN {col} TEXT")
    conn.execute("UPDATE volunteers SET source='web' WHERE source IS NULL")
    conn.commit()

    existing = conn.execute(
        "SELECT id, name, phone, email, address, notes FROM volunteers"
    ).fetchall()

    def find_match(p):
        ek, pk, nk = norm_email(p.email), norm_phone(p.phone), norm_name(p.name)
        for row in existing:
            rid, rname, rphone, remail, raddr, rnotes = row
            if (ek and norm_email(remail) == ek) or \
               (pk and norm_phone(rphone) == pk) or \
               (nk and norm_name(rname) == nk):
                return row
        return None

    inserted, enriched, matched_clean = [], [], []
    now = datetime.now(timezone.utc).isoformat()

    for p in people:
        notes_str = "; ".join(p.jobs + p.notes).strip("; ")
        row = find_match(p)
        if row:
            rid, rname, rphone, remail, raddr, rnotes = row
            fills = {}
            if p.email and not norm_email(remail):
                fills["email"] = p.email
            if p.phone and not norm_phone(rphone):
                fills["phone"] = p.phone
            if p.address and not (raddr or ""):
                fills["address"] = p.address
            # append sheet jobs/notes to whatever notes exist
            if notes_str:
                merged = "; ".join(x for x in [(rnotes or ""), notes_str] if x).strip("; ")
                fills["notes"] = merged
            if fills:
                sets = ", ".join(f"{k}=?" for k in fills)
                conn.execute(f"UPDATE volunteers SET {sets} WHERE id=?",
                             (*fills.values(), rid))
                enriched.append((rname, p.name, list(fills)))
            else:
                matched_clean.append((rname, p.name))
        else:
            conn.execute(
                "INSERT INTO volunteers (name, phone, email, help, other_text, "
                "address, notes, source, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (p.name, p.phone, p.email, "[]", "", p.address, notes_str, "sheet", now),
            )
            inserted.append(p.name)
    conn.commit()

    print(f"Parsed {len(people)} unique people from the sheet.\n")
    print(f"INSERTED as new (source=sheet): {len(inserted)}")
    for n in inserted:
        print(f"   + {n}")
    print(f"\nMATCHED existing web signup & filled in blanks: {len(enriched)}")
    for web, sheet, fields in enriched:
        print(f"   ~ web '{web}'  <-  sheet '{sheet}'  (filled: {', '.join(fields)})")
    print(f"\nMATCHED existing web signup, nothing to add: {len(matched_clean)}")
    for web, sheet in matched_clean:
        print(f"   = web '{web}'  ==  sheet '{sheet}'")
    total = conn.execute("SELECT COUNT(*) FROM volunteers").fetchone()[0]
    print(f"\nTotal rows in DB now: {total}")


if __name__ == "__main__":
    if "--go" not in sys.argv:
        print("Dry run not implemented separately; pass --go to write. (DB is backed up.)")
        sys.exit(1)
    main()
