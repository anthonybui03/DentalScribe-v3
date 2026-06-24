"""Main window — DentalScribe v3.

Responsibilities split by method group:
  _build_*        — UI construction
  _on_*           — user-triggered actions
  _recording_*    — audio capture lifecycle
  _transcribe_*   — Whisper transcription
  _generate_*     — Ollama note generation (streaming)
  _waveform_*     — live audio waveform visualizer
  _progress_*     — progress bar helpers
  _connectivity_* — offline indicator checks
  _inactivity_*   — auto-lock timer
"""
import queue
import threading
import tkinter as tk
import customtkinter as ctk
import numpy as np

import app.gui.theme as T
from app.gui.theme import C, make_font
from app.core import audio, config, note_history, audit_log
from app.core.note_templates import registry

_LIVE_INTERVAL_MS  = 3_000   # live transcription tick
_STREAM_POLL_MS    = 40      # streaming note update poll
_WAVEFORM_MS       = 50      # waveform redraw interval
_WAVEFORM_BARS     = 40      # number of bars in the visualizer
_MIC_TEST_SECS     = 3       # mic test recording duration


class MainWindow(ctk.CTkFrame):

    # ── Init ──────────────────────────────────────────────────────────────────

    def __init__(self, parent, cfg: dict):
        super().__init__(parent, fg_color=C["bg"])
        self.pack(fill="both", expand=True)
        self.cfg = cfg
        self.recorder = audio.AudioRecorder(
            device_index=cfg.get("mic_device_index", -1))

        self._wav_bytes: bytes = b""
        self._live_job: str | None = None
        self._live_running = False
        self._inactivity_job: str | None = None
        self._stream_queue: queue.Queue[str | None] = queue.Queue()
        self._waveform_job: str | None = None
        self._progress_job: str | None = None

        self._build_ui()
        self._refresh_template_combo()
        self._inactivity_reset()
        self._connectivity_check()

        parent.bind("<F2>", lambda _: self._on_toggle_recording())
        parent.bind("<F5>", lambda _: self._on_generate_note())
        parent.bind("<Motion>", lambda _: self._inactivity_reset())
        parent.bind("<Key>",    lambda _: self._inactivity_reset())

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._build_sidebar()
        self._build_main()
        self._build_statusbar()

    def _build_sidebar(self) -> None:
        sb = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0, width=224)
        sb.grid(row=0, column=0, rowspan=2, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(11, weight=1)

        # Logo
        ctk.CTkLabel(sb, text="DentalScribe", font=make_font(16, bold=True),
                     text_color=C["accent"]).grid(row=0, column=0, sticky="w",
                                                   padx=16, pady=(20, 2))
        ctk.CTkLabel(sb, text="v3", font=make_font(10),
                     text_color=C["text3"]).grid(row=1, column=0, sticky="w", padx=16)

        # Offline indicator row
        self._ollama_dot = ctk.CTkLabel(sb, text="● Ollama", font=make_font(9),
                                         text_color=C["text3"])
        self._ollama_dot.grid(row=2, column=0, sticky="w", padx=16, pady=(6, 0))
        self._whisper_dot = ctk.CTkLabel(sb, text="● Whisper", font=make_font(9),
                                          text_color=C["text3"])
        self._whisper_dot.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 4))

        T.divider(sb).grid(row=4, column=0, sticky="ew", padx=12, pady=8)

        # Patient ID
        T.section_label(sb, "Patient ID").grid(row=5, column=0, sticky="w", padx=16)
        self._patient_var = ctk.StringVar()
        T.make_entry(sb, textvariable=self._patient_var,
                     placeholder="Optional patient ID",
                     width=192).grid(row=6, column=0, padx=16, pady=(4, 10))

        # Template
        T.section_label(sb, "Template").grid(row=7, column=0, sticky="w", padx=16)
        self._template_var = ctk.StringVar()
        self._template_combo = T.make_combo(sb, width=192,
                                             command=self._on_template_change)
        self._template_combo.grid(row=8, column=0, padx=16, pady=(4, 2))
        T.ghost_btn(sb, "Manage Templates…",
                    command=self._on_manage_templates,
                    height=28, width=192).grid(row=9, column=0, padx=16, pady=(0, 10))

        # Microphone
        T.section_label(sb, "Microphone").grid(row=10, column=0, sticky="w", padx=16)
        self._mic_combo = T.make_combo(sb, width=192)
        self._mic_combo.grid(row=11, column=0, padx=16, pady=(4, 4))

        mic_btns = ctk.CTkFrame(sb, fg_color="transparent")
        mic_btns.grid(row=12, column=0, padx=16, sticky="ew")
        T.ghost_btn(mic_btns, "⟳", command=self._refresh_devices,
                    height=26, width=40).pack(side="left")
        T.ghost_btn(mic_btns, "Test Mic", command=self._on_mic_test,
                    height=26, width=100).pack(side="left", padx=(6, 0))

        self._mic_test_label = ctk.CTkLabel(sb, text="", font=make_font(9),
                                             text_color=C["text3"])
        self._mic_test_label.grid(row=13, column=0, padx=16, sticky="w")

        self._refresh_devices()

        T.divider(sb).grid(row=14, column=0, sticky="ew", padx=12, pady=8)

        # Nav buttons
        for row, (label, cmd) in enumerate([
            ("History",   self._on_history),
            ("Audit Log", self._on_audit),
            ("Settings",  self._on_settings),
        ], start=15):
            T.subtle_btn(sb, label, command=cmd, height=34,
                         width=192, anchor="w").grid(row=row, column=0, padx=12, pady=2)

    def _build_main(self) -> None:
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)
        main.grid_rowconfigure(3, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Toolbar
        toolbar = ctk.CTkFrame(main, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew")

        self._rec_btn = T.primary_btn(
            toolbar, "⏺   Start Dictation",
            command=self._on_toggle_recording,
            height=42, width=200,
        )
        self._rec_btn.pack(side="left")

        self._rec_indicator = ctk.CTkLabel(toolbar, text="",
                                            font=make_font(12, bold=True),
                                            text_color=C["record"])
        self._rec_indicator.pack(side="left", padx=10)

        T.ghost_btn(toolbar, "⚡ Generate Note (F5)",
                    command=self._on_generate_note,
                    height=42).pack(side="right")
        T.ghost_btn(toolbar, "Copy Note",
                    command=self._on_copy_note,
                    height=42).pack(side="right", padx=(0, 6))
        T.ghost_btn(toolbar, "Send to Open Dental",
                    command=self._on_send_od,
                    height=42).pack(side="right", padx=(0, 6))

        # Warning banner
        banner = ctk.CTkFrame(main, fg_color=C["warn_bg"], corner_radius=8, height=32)
        banner.grid(row=1, column=0, sticky="ew", pady=(8, 4))
        banner.grid_propagate(False)
        ctk.CTkLabel(banner,
                     text="⚠  AI-generated notes require provider review before chart entry",
                     font=ctk.CTkFont("Segoe UI", 11, slant="italic"),
                     text_color="#B45309").place(x=14, rely=0.5, anchor="w")

        # Waveform + progress bar row
        viz_row = ctk.CTkFrame(main, fg_color="transparent", height=36)
        viz_row.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        viz_row.grid_propagate(False)
        viz_row.grid_columnconfigure(0, weight=1)

        self._waveform_canvas = tk.Canvas(
            viz_row, height=36, bg=C["bg"],
            highlightthickness=0, bd=0,
        )
        self._waveform_canvas.grid(row=0, column=0, sticky="ew")

        self._progress_bar = ctk.CTkProgressBar(
            viz_row, height=4,
            fg_color=C["surface2"], progress_color=C["accent"],
            corner_radius=2,
        )
        self._progress_bar.set(0)
        # Hidden by default — shown during transcription / generation

        # Split panes
        panes = ctk.CTkFrame(main, fg_color="transparent")
        panes.grid(row=3, column=0, sticky="nsew")
        panes.grid_rowconfigure(1, weight=1)
        panes.grid_columnconfigure(0, weight=1)
        panes.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(panes, text="TRANSCRIPT", font=make_font(10, bold=True),
                     text_color=C["text3"]).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._transcript_box = T.make_textbox(panes)
        self._transcript_box.grid(row=1, column=0, sticky="nsew", padx=(0, 6))

        ctk.CTkLabel(panes, text="GENERATED NOTE", font=make_font(10, bold=True),
                     text_color=C["text3"]).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self._note_box = T.make_textbox(panes, fg_color=C["surface"])
        self._note_box.grid(row=1, column=1, sticky="nsew")

    def _build_statusbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0, height=28)
        bar.grid(row=1, column=1, sticky="ew")
        bar.grid_propagate(False)
        self._status_label = ctk.CTkLabel(bar, text="Ready",
                                           font=make_font(10), text_color=C["text2"])
        self._status_label.place(x=12, rely=0.5, anchor="w")

    # ── Connectivity indicator ────────────────────────────────────────────────

    def _connectivity_check(self) -> None:
        threading.Thread(target=self._connectivity_worker, daemon=True).start()

    def _connectivity_worker(self) -> None:
        from app.core.note_generator import check_ollama_health
        import importlib
        ollama_ok = check_ollama_health(self.cfg.get("ollama_host", "http://localhost:11434"))

        whisper_ok = False
        try:
            importlib.import_module("faster_whisper")
            whisper_ok = True
        except ImportError:
            try:
                importlib.import_module("whisper")
                whisper_ok = True
            except ImportError:
                pass

        self.after(0, self._connectivity_update, ollama_ok, whisper_ok)

    def _connectivity_update(self, ollama_ok: bool, whisper_ok: bool) -> None:
        self._ollama_dot.configure(
            text=f"{'●' if ollama_ok else '○'} Ollama",
            text_color=C["success"] if ollama_ok else C["danger"],
        )
        self._whisper_dot.configure(
            text=f"{'●' if whisper_ok else '○'} Whisper",
            text_color=C["success"] if whisper_ok else C["danger"],
        )
        if not ollama_ok:
            self._status("Ollama not reachable — note generation unavailable.", "warn")

    # ── Template helpers ──────────────────────────────────────────────────────

    def _refresh_template_combo(self) -> None:
        names = registry.names()
        self._template_combo.configure(values=names)
        current = self._template_var.get()
        if current not in names:
            first = names[0] if names else ""
            self._template_combo.set(first)
            self._template_var.set(first)

    def _on_template_change(self, _value: str = "") -> None:
        name = self._template_combo.get()
        tpl = registry.get(name)
        self._note_box.configure(state="normal")
        self._note_box.delete("1.0", "end")
        self._note_box.insert("end", tpl.skeleton)

    def _on_manage_templates(self) -> None:
        from app.gui.templates_window import TemplatesWindow
        TemplatesWindow(self, on_change=self._refresh_template_combo)

    # ── Device helpers ────────────────────────────────────────────────────────

    def _refresh_devices(self) -> None:
        devices = audio.list_input_devices()
        labels = [f"[{i}] {name}" for i, name in devices]
        self._mic_combo.configure(values=labels or ["No input devices found"])
        if labels:
            self._mic_combo.set(labels[0])

    def _selected_device_index(self) -> int:
        val = self._mic_combo.get()
        try:
            return int(val.split("]")[0].lstrip("["))
        except Exception:
            return -1

    # ── Mic test ──────────────────────────────────────────────────────────────

    def _on_mic_test(self) -> None:
        if self.recorder.is_recording:
            return
        self._mic_test_label.configure(text=f"Recording {_MIC_TEST_SECS}s…",
                                        text_color=C["record"])
        rec = audio.AudioRecorder(device_index=self._selected_device_index())
        try:
            rec.start()
        except Exception as e:
            self._mic_test_label.configure(text=f"Error: {e}", text_color=C["danger"])
            return

        def _finish():
            wav = rec.stop()
            if not wav:
                self.after(0, self._mic_test_label.configure,
                           {"text": "No audio detected.", "text_color": C["danger"]})
                return
            # Measure RMS amplitude
            import io, wave
            with wave.open(io.BytesIO(wav)) as wf:
                frames = wf.readframes(wf.getnframes())
            samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
            rms = float(np.sqrt(np.mean(samples ** 2)))
            if rms < 50:
                msg, color = "Very quiet — check mic.", C["warn"]
            elif rms < 500:
                msg, color = "Low signal — speak louder.", C["warn"]
            else:
                msg, color = f"✓ Mic OK (level {int(rms)})", C["success"]
            self.after(0, lambda: self._mic_test_label.configure(
                text=msg, text_color=color))

        threading.Thread(target=lambda: (
            __import__("time").sleep(_MIC_TEST_SECS), _finish()
        ), daemon=True).start()

    # ── Status bar ────────────────────────────────────────────────────────────

    def _status(self, msg: str, level: str = "normal") -> None:
        color = T.STATUS_COLORS.get(level, C["text2"])
        self._status_label.configure(text=msg, text_color=color)

    # ── Progress bar ──────────────────────────────────────────────────────────

    def _progress_start(self) -> None:
        self._progress_bar.grid(row=0, column=0, sticky="ew", pady=(32, 0))
        self._progress_bar.configure(mode="indeterminate")
        self._progress_bar.start()

    def _progress_stop(self) -> None:
        self._progress_bar.stop()
        self._progress_bar.grid_remove()

    # ── Waveform visualizer ───────────────────────────────────────────────────

    def _waveform_start(self) -> None:
        self._waveform_tick()

    def _waveform_stop(self) -> None:
        if self._waveform_job:
            self.after_cancel(self._waveform_job)
            self._waveform_job = None
        self._waveform_canvas.delete("all")

    def _waveform_tick(self) -> None:
        if not self.recorder.is_recording:
            self._waveform_stop()
            return
        snap = self.recorder.get_snapshot()
        if snap:
            self._waveform_draw(snap)
        self._waveform_job = self.after(_WAVEFORM_MS, self._waveform_tick)

    def _waveform_draw(self, wav_bytes: bytes) -> None:
        import io, wave as wavemod
        try:
            with wavemod.open(io.BytesIO(wav_bytes)) as wf:
                frames = wf.readframes(wf.getnframes())
            samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
        except Exception:
            return

        canvas = self._waveform_canvas
        canvas.update_idletasks()
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 2 or h < 2:
            return

        canvas.delete("all")
        n = _WAVEFORM_BARS
        chunk = max(1, len(samples) // n)
        bar_w = w / n
        mid = h / 2
        max_amp = 32768.0

        for i in range(n):
            seg = samples[i * chunk: (i + 1) * chunk]
            if len(seg) == 0:
                continue
            rms = float(np.sqrt(np.mean(seg ** 2)))
            bar_h = max(2, (rms / max_amp) * h * 2.5)
            bar_h = min(bar_h, h - 2)
            x0 = i * bar_w + 1
            x1 = x0 + bar_w - 2
            # Gradient: dim bars for low amplitude, bright for high
            intensity = min(1.0, rms / 3000)
            r = int(0x23 + intensity * (0xEF - 0x23))
            g = int(0x63 + intensity * (0x44 - 0x63))
            b = int(0xEB + intensity * (0x44 - 0xEB))
            color = f"#{r:02x}{max(0,g):02x}{max(0,b):02x}"
            canvas.create_rectangle(x0, mid - bar_h / 2,
                                     x1, mid + bar_h / 2,
                                     fill=color, outline="")

    # ── Recording ─────────────────────────────────────────────────────────────

    def _on_toggle_recording(self) -> None:
        self._inactivity_reset()
        if self.recorder.is_recording:
            self._recording_stop()
        else:
            self._recording_start()

    def _recording_start(self) -> None:
        self.recorder.device_index = self._selected_device_index()
        try:
            self.recorder.start()
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Microphone Error", str(e))
            return
        self._rec_btn.configure(text="⏹   Stop Dictation",
                                 fg_color=C["record"], hover_color=C["record_dark"])
        self._status("Recording — speak clearly.", "record")
        self._transcript_box.configure(state="normal")
        self._transcript_box.delete("1.0", "end")
        self._transcript_box.insert("end", "Listening…")
        self._transcript_box.configure(state="disabled")
        self._rec_indicator_animate()
        self._waveform_start()
        self._live_running = True
        self._live_job = self.after(_LIVE_INTERVAL_MS, self._live_tick)

    def _recording_stop(self) -> None:
        self._live_running = False
        if self._live_job:
            self.after_cancel(self._live_job)
            self._live_job = None
        self._waveform_stop()
        self._wav_bytes = self.recorder.stop()
        self._rec_btn.configure(text="⏺   Start Dictation",
                                 fg_color=C["accent"], hover_color=C["accent_dark"])
        self._rec_indicator.configure(text="")
        if not self._wav_bytes:
            self._status("No audio captured — check microphone.", "warn")
            return
        self._status("Transcribing…", "normal")
        self._progress_start()
        threading.Thread(target=self._transcribe_final, daemon=True).start()

    def _rec_indicator_animate(self) -> None:
        if not self.recorder.is_recording:
            self._rec_indicator.configure(text="")
            return
        cur = self._rec_indicator.cget("text")
        self._rec_indicator.configure(text="" if cur else "● REC")
        self.after(600, self._rec_indicator_animate)

    # ── Live transcription ────────────────────────────────────────────────────

    def _live_tick(self) -> None:
        if not self._live_running or not self.recorder.is_recording:
            return
        snap = self.recorder.get_snapshot()
        if snap:
            threading.Thread(target=self._live_worker, args=(snap,), daemon=True).start()
        self._live_job = self.after(_LIVE_INTERVAL_MS, self._live_tick)

    def _live_worker(self, wav_bytes: bytes) -> None:
        try:
            from app.core import transcriber
            text = transcriber.transcribe(
                wav_bytes,
                backend=self.cfg.get("whisper_backend", "faster-whisper"),
                model_size=self.cfg.get("whisper_model", "base.en"),
                device=self.cfg.get("whisper_device", "cpu"),
                compute_type=self.cfg.get("whisper_compute_type", "float32"),
                language=self.cfg.get("whisper_language", "en"),
            )
            if self._live_running and text:
                self.after(0, self._live_update, text)
        except Exception:
            pass

    def _live_update(self, text: str) -> None:
        if not self._live_running:
            return
        self._transcript_box.configure(state="normal")
        self._transcript_box.delete("1.0", "end")
        self._transcript_box.insert("end", text + " ▌")
        self._transcript_box.configure(state="disabled")

    # ── Final transcription ───────────────────────────────────────────────────

    def _transcribe_final(self) -> None:
        try:
            from app.core import transcriber
            text = transcriber.transcribe(
                self._wav_bytes,
                backend=self.cfg.get("whisper_backend", "faster-whisper"),
                model_size=self.cfg.get("whisper_model", "base.en"),
                device=self.cfg.get("whisper_device", "cpu"),
                compute_type=self.cfg.get("whisper_compute_type", "float32"),
                language=self.cfg.get("whisper_language", "en"),
            )
            self.after(0, self._transcribe_done, text)
        except Exception as e:
            self.after(0, self._progress_stop)
            self.after(0, self._status, f"Transcription error: {e}", "danger")

    def _transcribe_done(self, text: str) -> None:
        self._progress_stop()
        self._transcript_box.configure(state="normal")
        self._transcript_box.delete("1.0", "end")
        self._transcript_box.insert("end", text)
        self._status("Transcription complete. Click Generate Note or press F5.", "success")
        audit_log.log_event("transcribe", f"patient={self._patient_var.get()}",
                            self.cfg.get("_fernet"))

    # ── Note generation (streaming) ───────────────────────────────────────────

    def _on_generate_note(self) -> None:
        transcript = self._transcript_box.get("1.0", "end").strip()
        if not transcript or transcript in ("Listening…", ""):
            self._status("No transcript to generate from.", "warn")
            return
        tpl = registry.get(self._template_combo.get())
        self._note_box.configure(state="normal")
        self._note_box.delete("1.0", "end")
        self._status("Generating note…", "normal")
        self._progress_start()

        while not self._stream_queue.empty():
            try:
                self._stream_queue.get_nowait()
            except queue.Empty:
                break

        threading.Thread(
            target=self._generate_worker,
            args=(transcript, tpl.llm_instruction),
            daemon=True,
        ).start()
        self.after(_STREAM_POLL_MS, self._generate_poll)

    def _generate_worker(self, transcript: str, system_prompt: str) -> None:
        try:
            from app.core.note_generator import generate_note_stream
            for chunk in generate_note_stream(
                transcript, system_prompt,
                ollama_host=self.cfg.get("ollama_host", "http://localhost:11434"),
                model=self.cfg.get("ollama_model", "llama3"),
                temperature=self.cfg.get("ollama_temperature", 0.2),
            ):
                self._stream_queue.put(chunk)
            self._stream_queue.put(None)
        except Exception as e:
            self._stream_queue.put(None)
            self.after(0, self._progress_stop)
            self.after(0, self._status, str(e), "danger")

    def _generate_poll(self) -> None:
        try:
            while True:
                chunk = self._stream_queue.get_nowait()
                if chunk is None:
                    self._generate_done()
                    return
                self._note_box.insert("end", chunk)
                self._note_box.see("end")
        except queue.Empty:
            pass
        self.after(_STREAM_POLL_MS, self._generate_poll)

    def _generate_done(self) -> None:
        self._progress_stop()
        note = self._note_box.get("1.0", "end").strip()
        self._status("Note generated. Review before chart entry.", "success")
        if self.cfg.get("save_notes_locally", True):
            note_history.save_entry(
                patient_id=self._patient_var.get(),
                template=self._template_combo.get(),
                transcript=self._transcript_box.get("1.0", "end").strip(),
                note=note,
            )
        audit_log.log_event(
            "generate_note",
            f"patient={self._patient_var.get()} template={self._template_combo.get()}",
            self.cfg.get("_fernet"),
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_copy_note(self) -> None:
        note = self._note_box.get("1.0", "end").strip()
        if note:
            self.clipboard_clear()
            self.clipboard_append(note)
            self._status("Note copied to clipboard.", "success")

    def _on_send_od(self) -> None:
        note = self._note_box.get("1.0", "end").strip()
        if not note:
            self._status("No note to send.", "warn")
            return
        from app.gui.od_dialog import OdDialog
        OdDialog(self, self.cfg, note)

    def _on_history(self) -> None:
        from app.gui.history_window import HistoryWindow
        HistoryWindow(self)

    def _on_audit(self) -> None:
        from app.gui.audit_window import AuditWindow
        AuditWindow(self, self.cfg)

    def _on_settings(self) -> None:
        from app.gui.settings_window import SettingsWindow
        SettingsWindow(self, self.cfg)

    # ── Inactivity / auto-lock ────────────────────────────────────────────────

    def _inactivity_reset(self) -> None:
        if self._inactivity_job:
            self.after_cancel(self._inactivity_job)
        timeout_ms = self.cfg.get("inactivity_timeout_minutes", 10) * 60 * 1000
        self._inactivity_job = self.after(timeout_ms, self._inactivity_lock)

    def _inactivity_lock(self) -> None:
        if not self.cfg.get("pin_hash"):
            return
        from app.gui.login_window import LoginWindow
        top = self.winfo_toplevel()
        for w in top.winfo_children():
            if isinstance(w, ctk.CTkFrame):
                w.pack_forget()
        LoginWindow(top, self.cfg,
                    on_authenticated=lambda: self.pack(fill="both", expand=True))
