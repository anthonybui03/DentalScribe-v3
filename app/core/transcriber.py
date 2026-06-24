"""Local Whisper transcription — faster-whisper or openai-whisper backend."""
import tempfile
from pathlib import Path
from typing import Literal

Backend = Literal["faster-whisper", "openai-whisper"]

AVAILABLE_MODELS = ["tiny.en", "base.en", "small.en", "medium.en", "large-v3"]

_cache: dict = {}
_MAX_CACHED = 2


def _evict_if_needed() -> None:
    while len(_cache) >= _MAX_CACHED:
        _cache.pop(next(iter(_cache)))


def _load_faster_whisper(model: str, device: str, compute_type: str):
    from faster_whisper import WhisperModel
    key = ("fw", model, device)
    if key not in _cache:
        _evict_if_needed()
        _cache[key] = WhisperModel(model, device=device, compute_type=compute_type)
    return _cache[key]


def _load_openai_whisper(model: str):
    import whisper
    key = ("ow", model)
    if key not in _cache:
        _evict_if_needed()
        _cache[key] = whisper.load_model(model)
    return _cache[key]


def transcribe(
    wav_bytes: bytes,
    backend: Backend = "faster-whisper",
    model_size: str = "base.en",
    device: str = "cpu",
    compute_type: str = "float32",
    language: str = "en",
) -> str:
    if not wav_bytes:
        return ""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(wav_bytes)
        tmp_path = tmp.name
    try:
        if backend == "faster-whisper":
            model = _load_faster_whisper(model_size, device, compute_type)
            segments, _ = model.transcribe(tmp_path, language=language, beam_size=5)
            return " ".join(seg.text.strip() for seg in segments)
        else:
            import whisper
            model = _load_openai_whisper(model_size)
            result = model.transcribe(tmp_path, language=language)
            return result["text"].strip()
    finally:
        Path(tmp_path).unlink(missing_ok=True)
