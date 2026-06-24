"""AI note generation via local Ollama with streaming support."""
import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Optional


_ANTI_HALLUCINATION = (
    "CRITICAL RULES — follow without exception:\n"
    "1. Use ONLY information explicitly stated in the dictation provided by the user.\n"
    "2. Do NOT invent, assume, or infer any clinical findings, measurements, medications, "
    "tooth numbers, diagnoses, or procedures that were not spoken.\n"
    "3. If a required section has no corresponding dictation, write exactly: "
    "'Not dictated.' — never leave a section blank or fill it with guessed content.\n"
    "4. If the dictation is too short or unclear to produce a complete note, write a brief "
    "note from what was said and mark unclear sections as 'Not dictated.'\n\n"
)


def generate_note_stream(
    transcript: str,
    system_prompt: str,
    ollama_host: str = "http://localhost:11434",
    model: str = "llama3",
    temperature: float = 0.2,
) -> Iterator[str]:
    """Yield text chunks as they stream from Ollama."""
    url = f"{ollama_host.rstrip('/')}/api/chat"
    full_system = _ANTI_HALLUCINATION + system_prompt
    payload = json.dumps({
        "model": model,
        "temperature": temperature,
        "stream": True,
        "messages": [
            {"role": "system", "content": full_system},
            {"role": "user",   "content": transcript},
        ],
    }).encode()
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw in resp:
                line = raw.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    chunk = obj.get("message", {}).get("content", "")
                    if chunk:
                        yield chunk
                except json.JSONDecodeError:
                    continue
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Cannot reach Ollama at {ollama_host}. Is it running?"
        ) from e


def generate_note(
    transcript: str,
    system_prompt: str,
    ollama_host: str = "http://localhost:11434",
    model: str = "llama3",
    temperature: float = 0.2,
) -> str:
    return "".join(generate_note_stream(transcript, system_prompt,
                                        ollama_host, model, temperature))


def check_ollama_health(host: str = "http://localhost:11434") -> bool:
    try:
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/tags", timeout=3):
            return True
    except Exception:
        return False


def list_ollama_models(host: str = "http://localhost:11434") -> list[str]:
    try:
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/tags", timeout=5) as r:
            data = json.loads(r.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []
