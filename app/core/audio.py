"""Thread-safe audio recorder using sounddevice — supports pause/resume."""
import io
import threading
import wave
from typing import Optional

import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16_000
CHANNELS = 1
DTYPE = "int16"


class AudioRecorder:
    def __init__(self, device_index: int = -1):
        self.device_index: int = device_index
        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._stream: Optional[sd.InputStream] = None
        self.is_recording = False
        self.is_paused = False

    def start(self) -> None:
        if self.is_recording:
            return
        with self._lock:
            self._frames.clear()
        self.is_paused = False
        self._start_stream()
        self.is_recording = True

    def pause(self) -> None:
        """Pause recording — keeps accumulated audio, stops the stream."""
        if not self.is_recording or self.is_paused:
            return
        self.is_paused = True
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def resume(self) -> None:
        """Resume recording — appends new audio to existing frames."""
        if not self.is_recording or not self.is_paused:
            return
        self.is_paused = False
        self._start_stream()

    def stop(self) -> bytes:
        """Stop recording and return all accumulated audio as WAV bytes."""
        if not self.is_recording:
            return b""
        self.is_recording = False
        self.is_paused = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        with self._lock:
            frames = list(self._frames)
        return _frames_to_wav(frames) if frames else b""

    def get_snapshot(self) -> bytes:
        """Return WAV bytes of all audio captured so far without stopping."""
        with self._lock:
            frames = list(self._frames)
        return _frames_to_wav(frames) if frames else b""

    def _start_stream(self) -> None:
        device = None if self.device_index < 0 else self.device_index
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            device=device,
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata: np.ndarray, frames, time, status) -> None:
        with self._lock:
            self._frames.append(indata.copy())


def _frames_to_wav(frames: list[np.ndarray]) -> bytes:
    audio = np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()


def list_input_devices() -> list[tuple[int, str]]:
    try:
        devices = sd.query_devices()
        return [
            (i, d["name"])
            for i, d in enumerate(devices)
            if d["max_input_channels"] > 0
        ]
    except Exception:
        return []
