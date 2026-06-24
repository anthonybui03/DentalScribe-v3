"""Ambient voice activity detection — continuously listens and flushes speech segments.

Energy-based VAD (no extra dependencies):
  - Frame: 512 samples @ 16 kHz  (~32 ms)
  - Speech onset : RMS > threshold for ONSET_FRAMES consecutive frames
  - Speech end   : RMS < threshold for SILENCE_FRAMES consecutive frames
  - Minimum clip : MIN_SPEECH_FRAMES before a segment is flushed

When a segment is flushed it is put into the provided queue as raw WAV bytes.
A sentinel None is never put — callers just check is_running.
"""
import io
import queue
import threading
import wave

import numpy as np
import sounddevice as sd

SAMPLE_RATE   = 16_000
CHANNELS      = 1
DTYPE         = "int16"
FRAME_SAMPLES = 512          # ~32 ms per frame

# VAD thresholds (RMS units, range 0–32768)
DEFAULT_THRESHOLD   = 300    # above → speech, below → silence
ONSET_FRAMES        = 5      # ~160 ms of speech to start capture
SILENCE_FRAMES      = 60     # ~1.9 s of silence to end segment
MIN_SPEECH_FRAMES   = 10     # ~320 ms minimum — ignore short noise bursts


class AmbientListener:
    """Runs a continuous mic stream in a background thread.

    When a speech segment is detected it is pushed to `out_queue` as WAV bytes.
    """

    def __init__(self, out_queue: queue.Queue, device_index: int = -1,
                 threshold: int = DEFAULT_THRESHOLD):
        self.out_queue    = out_queue
        self.device_index = device_index
        self.threshold    = threshold
        self.is_running   = False
        self._thread: threading.Thread | None = None
        self._stop_event  = threading.Event()

    def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self.is_running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    # ── internal ──────────────────────────────────────────────────────────────

    def _run(self) -> None:
        device = None if self.device_index < 0 else self.device_index

        speech_frames:  list[np.ndarray] = []
        above_count  = 0   # consecutive frames above threshold
        below_count  = 0   # consecutive frames below threshold (during speech)
        in_speech    = False

        frame_buf: list[np.ndarray] = []
        frame_lock = threading.Lock()

        def _cb(indata, frames, time, status):
            with frame_lock:
                frame_buf.append(indata.copy())

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                            dtype=DTYPE, device=device,
                            blocksize=FRAME_SAMPLES, callback=_cb):
            while not self._stop_event.is_set():
                # Drain whatever the callback put in
                with frame_lock:
                    pending = frame_buf[:]
                    frame_buf.clear()

                for frame in pending:
                    rms = float(np.sqrt(np.mean(frame.astype(np.float32) ** 2)))
                    loud = rms > self.threshold

                    if not in_speech:
                        if loud:
                            above_count += 1
                            speech_frames.append(frame)
                            if above_count >= ONSET_FRAMES:
                                in_speech   = True
                                below_count = 0
                        else:
                            above_count = 0
                            speech_frames.clear()
                    else:
                        speech_frames.append(frame)
                        if loud:
                            below_count = 0
                        else:
                            below_count += 1
                            if below_count >= SILENCE_FRAMES:
                                # End of segment
                                if len(speech_frames) >= MIN_SPEECH_FRAMES:
                                    wav = _to_wav(speech_frames)
                                    self.out_queue.put(wav)
                                speech_frames = []
                                above_count   = 0
                                below_count   = 0
                                in_speech     = False

                self._stop_event.wait(timeout=0.02)  # 20 ms poll

        # Flush any trailing speech when stopped
        if in_speech and len(speech_frames) >= MIN_SPEECH_FRAMES:
            self.out_queue.put(_to_wav(speech_frames))


def _to_wav(frames: list[np.ndarray]) -> bytes:
    audio = np.concatenate(frames, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()
