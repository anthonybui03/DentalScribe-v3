"""Provider management — SQLite-backed."""
import sqlite3
from dataclasses import dataclass
from app.core.config import notes_db_path


@dataclass
class Provider:
    id: int
    name: str
    title: str        # Dr., RDH, etc.
    credentials: str  # DDS, DMD, RDH, MS, etc.
    npi: str


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(notes_db_path()))
    c.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            title       TEXT NOT NULL DEFAULT '',
            credentials TEXT NOT NULL DEFAULT '',
            npi         TEXT NOT NULL DEFAULT ''
        )
    """)
    c.commit()
    return c


def list_providers() -> list[Provider]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, name, title, credentials, npi FROM providers ORDER BY name"
        ).fetchall()
    return [Provider(*r) for r in rows]


def add_provider(name: str, title: str = "", credentials: str = "", npi: str = "") -> Provider:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO providers (name, title, credentials, npi) VALUES (?, ?, ?, ?)",
            (name.strip(), title.strip(), credentials.strip(), npi.strip()),
        )
        return Provider(cur.lastrowid, name.strip(), title.strip(),
                        credentials.strip(), npi.strip())


def update_provider(provider_id: int, name: str, title: str,
                    credentials: str, npi: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE providers SET name=?, title=?, credentials=?, npi=? WHERE id=?",
            (name.strip(), title.strip(), credentials.strip(), npi.strip(), provider_id),
        )


def delete_provider(provider_id: int) -> None:
    with _conn() as c:
        c.execute("DELETE FROM providers WHERE id=?", (provider_id,))


def format_provider(p: Provider) -> str:
    """Return display string e.g. 'Dr. Jane Smith, DDS'"""
    parts = []
    if p.title:
        parts.append(p.title)
    parts.append(p.name)
    if p.credentials:
        parts.append(f", {p.credentials}")
    return " ".join(parts)
