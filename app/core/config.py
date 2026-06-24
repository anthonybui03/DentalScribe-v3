"""Central config — single source of truth for paths and defaults."""
import json
import os
from pathlib import Path
from typing import TypedDict

# Single canonical data directory used by every module
DATA_DIR = Path(os.getenv("APPDATA", "~")).expanduser() / "DentalScribe-v3"


class AppConfig(TypedDict, total=False):
    # Transcription
    whisper_backend: str
    whisper_model: str
    whisper_device: str
    whisper_compute_type: str
    whisper_language: str
    # AI
    ollama_host: str
    ollama_model: str
    ollama_temperature: float
    # Security
    pin_hash: str
    inactivity_timeout_minutes: int
    encrypt_at_rest: bool
    save_raw_audio: bool
    # Open Dental
    od_api_url: str
    od_developer_key: str
    od_customer_key: str
    # Storage
    save_notes_locally: bool
    max_history_entries: int
    # UI
    theme: str
    onboarding_complete: bool
    mic_device_index: int


_DEFAULTS: AppConfig = {
    "whisper_backend":            "faster-whisper",
    "whisper_model":              "base.en",
    "whisper_device":             "cpu",
    "whisper_compute_type":       "float32",
    "whisper_language":           "en",
    "ollama_host":                "http://localhost:11434",
    "ollama_model":               "llama3",
    "ollama_temperature":         0.2,
    "inactivity_timeout_minutes": 10,
    "encrypt_at_rest":            True,
    "save_raw_audio":             False,
    "od_api_url":                 "",
    "od_developer_key":           "",
    "od_customer_key":            "",
    "save_notes_locally":         True,
    "max_history_entries":        1000,
    "theme":                      "dark",
    "onboarding_complete":        False,
    "mic_device_index":           -1,
}

_CONFIG_FILE = DATA_DIR / "config.json"


def load() -> AppConfig:
    cfg = dict(_DEFAULTS)
    if _CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(_CONFIG_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg  # type: ignore[return-value]


def save(cfg: AppConfig) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe = {k: v for k, v in cfg.items() if not k.startswith("_")}
    _CONFIG_FILE.write_text(json.dumps(safe, indent=2), encoding="utf-8")


def audio_dir() -> Path:
    p = DATA_DIR / "audio"
    p.mkdir(parents=True, exist_ok=True)
    return p


def notes_db_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / "notes.db"


def audit_log_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / "audit.log"


def salt_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / "salt.bin"


def templates_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / "templates.json"
