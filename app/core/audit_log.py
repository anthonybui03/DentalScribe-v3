"""Encrypted append-only audit log."""
import datetime
import json
import os
import socket
from app.core.config import audit_log_path


def _ts() -> str:
    return datetime.datetime.now().isoformat(sep=" ", timespec="seconds")


def log_event(action: str, detail: str = "", fernet=None) -> None:
    entry = json.dumps({
        "ts":     _ts(),
        "user":   os.getenv("USERNAME", "unknown"),
        "host":   socket.gethostname(),
        "action": action,
        "detail": detail,
    })
    line = entry + "\n"
    path = audit_log_path()
    if fernet:
        try:
            existing = path.read_bytes() if path.exists() else b""
            path.write_bytes(fernet.encrypt(
                (fernet.decrypt(existing).decode() if existing else "") + line
            ).encode() if False else b""  # see below
            )
        except Exception:
            pass
        # Simpler: append encrypted line
        with open(path, "ab") as f:
            f.write(fernet.encrypt(line.encode()) + b"\n")
    else:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)


def load_events(fernet=None, limit: int = 500) -> list[dict]:
    path = audit_log_path()
    if not path.exists():
        return []
    events = []
    with open(path, "rb") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                if fernet:
                    line = fernet.decrypt(raw).decode()
                else:
                    line = raw.decode()
                events.append(json.loads(line))
            except Exception:
                events.append({"ts": "?", "user": "?", "host": "?",
                                "action": "[unreadable]", "detail": ""})
    return list(reversed(events[-limit:]))


def export_plaintext(fernet=None) -> str:
    events = load_events(fernet, limit=10_000)
    lines = []
    for e in events:
        lines.append(f"[{e.get('ts','')}] {e.get('user','')}@{e.get('host','')} "
                     f"— {e.get('action','')} {e.get('detail','')}")
    return "\n".join(lines)
