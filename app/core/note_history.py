"""SQLite-backed note history — replaces the 500-entry JSON store from v2."""
import sqlite3
import datetime
from dataclasses import dataclass
from typing import Optional
from app.core.config import notes_db_path


@dataclass
class HistoryEntry:
    id: int
    timestamp: str
    patient_id: str
    template: str
    transcript: str
    note: str


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(notes_db_path()))
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            patient_id  TEXT NOT NULL DEFAULT '',
            template    TEXT NOT NULL DEFAULT '',
            transcript  TEXT NOT NULL DEFAULT '',
            note        TEXT NOT NULL DEFAULT ''
        )
    """)
    c.commit()
    return c


def save_entry(patient_id: str, template: str, transcript: str, note: str) -> int:
    ts = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO notes (timestamp, patient_id, template, transcript, note) "
            "VALUES (?, ?, ?, ?, ?)",
            (ts, patient_id, template, transcript, note),
        )
        return cur.lastrowid


def load_entries(
    patient_id: str = "",
    search: str = "",
    limit: int = 200,
    offset: int = 0,
) -> list[HistoryEntry]:
    query = "SELECT id, timestamp, patient_id, template, transcript, note FROM notes WHERE 1=1"
    params: list = []
    if patient_id:
        query += " AND patient_id LIKE ?"
        params.append(f"%{patient_id}%")
    if search:
        query += " AND (transcript LIKE ? OR note LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with _conn() as c:
        rows = c.execute(query, params).fetchall()
    return [HistoryEntry(*r) for r in rows]


def delete_entry(entry_id: int) -> None:
    with _conn() as c:
        c.execute("DELETE FROM notes WHERE id = ?", (entry_id,))


def count_entries() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
