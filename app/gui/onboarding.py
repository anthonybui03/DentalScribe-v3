"""First-run onboarding tutorial — v3."""
import customtkinter as ctk
from app.gui.theme import C, make_font
from app.core import config as cfg_module

STEPS = [
    {
        "icon": "🦷",
        "title": "Welcome to DentalScribe v3",
        "body": (
            "DentalScribe turns your spoken dictation into professional dental chart "
            "notes — completely on this computer.\n\n"
            "No patient data ever leaves this machine. No internet required after setup.\n\n"
            "This quick tour covers everything you need to know in about 2 minutes."
        ),
    },
    {
        "icon": "🎙",
        "title": "Set Up Your Microphone",
        "body": (
            "In the left sidebar, select the microphone you'll be speaking into — "
            "usually your headset or the built-in mic.\n\n"
            "Click ⟳ Refresh if your mic isn't showing in the list.\n\n"
            "Tip: a headset microphone gives much better transcription accuracy "
            "than a built-in laptop mic."
        ),
    },
    {
        "icon": "📋",
        "title": "Choose a Note Template",
        "body": (
            "DentalScribe includes 8 built-in templates:\n\n"
            "  •  Hygiene Recall\n"
            "  •  Limited Exam\n"
            "  •  Comprehensive Exam\n"
            "  •  Pediatric Restorative\n"
            "  •  Extraction\n"
            "  •  Fluoride / SDF\n"
            "  •  Referral Letter\n"
            "  •  Custom / Freeform\n\n"
            "Each template has a tailored AI prompt behind it — the AI knows exactly "
            "what sections to include. You can also create your own under Manage Templates."
        ),
    },
    {
        "icon": "⏺",
        "title": "Dictate Your Note",
        "body": (
            "1. Enter the Patient ID in the sidebar (optional but recommended for history).\n\n"
            "2. Click Start Dictation or press F2 and speak naturally — pretend you're "
            "describing the visit to a colleague.\n\n"
            "3. The transcript box shows a live preview as you speak.\n\n"
            "4. Click Stop Dictation or press F2 again when finished."
        ),
    },
    {
        "icon": "⚡",
        "title": "Generate the Note",
        "body": (
            "After stopping dictation, click Generate Note or press F5.\n\n"
            "The note appears word-by-word as the AI writes it in real time — "
            "you'll see it stream into the right panel.\n\n"
            "Generation usually takes 5–15 seconds depending on your computer speed "
            "and the selected AI model."
        ),
    },
    {
        "icon": "✏️",
        "title": "Review and Edit",
        "body": (
            "Always review the generated note before using it.\n\n"
            "The AI is highly accurate but may occasionally miss a detail or "
            "use slightly different wording than you prefer.\n\n"
            "Click directly in the note box to make edits. "
            "If the note isn't right, press F5 to regenerate.\n\n"
            "⚠  AI-generated notes require provider review before chart entry."
        ),
    },
    {
        "icon": "➤",
        "title": "Send to Open Dental",
        "body": (
            "When the note looks good, you have two options:\n\n"
            "📋  Copy Note — copies to clipboard so you can paste into Open Dental manually. "
            "This works with any dental software and requires no setup.\n\n"
            "➤  Send to Open Dental — if your office has the API configured in Settings, "
            "this searches for the patient and sends the note directly.\n\n"
            "The clipboard method is recommended for most offices."
        ),
    },
    {
        "icon": "🔒",
        "title": "Security and Privacy",
        "body": (
            "DentalScribe v3 is built with privacy first:\n\n"
            "  •  100% local — no cloud, no internet after setup\n"
            "  •  Notes and audit logs are encrypted on disk\n"
            "  •  Auto-locks after inactivity (configurable)\n"
            "  •  Every action is logged in the Audit Log\n"
            "  •  Note history stored in a local encrypted SQLite database\n\n"
            "Configure PIN lock, timeout, and encryption in Settings."
        ),
    },
    {
        "icon": "✅",
        "title": "You're All Set!",
        "body": (
            "You're ready to start using DentalScribe v3.\n\n"
            "Quick reference:\n\n"
            "  F2  —  Start / Stop dictation\n"
            "  F5  —  Generate note\n\n"
            "Your notes are automatically saved to history after each generation. "
            "Access them anytime from the History button in the sidebar.\n\n"
            "To see this tutorial again: Settings → Storage → Restart Onboarding Tutorial."
        ),
    },
]


class OnboardingWindow(ctk.CTkToplevel):

    def __init__(self, parent, cfg: dict, on_complete=None):
        super().__init__(parent)
        self.cfg = cfg
        self.on_complete = on_complete
        self._step = 0
        self.title("Welcome to DentalScribe v3")
        self.geometry("600x580")
        self.minsize(520, 520)
        self.resizable(True, True)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._finish)
        self._build_ui()
        self._show_step(0)

    def _build_ui(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Progress dots
        self._dots_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self._dots_frame.grid(row=0, column=0, sticky="ew", pady=(14, 0))

        # Content card
        card = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=14)
        card.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 8))
        card.grid_rowconfigure(3, weight=1)
        card.grid_columnconfigure(0, weight=1)

        self._icon_label = ctk.CTkLabel(card, text="",
                                         font=ctk.CTkFont("Segoe UI", 40))
        self._icon_label.grid(row=0, column=0, pady=(28, 4))

        self._title_label = ctk.CTkLabel(card, text="",
                                          font=make_font(17, bold=True),
                                          text_color=C["text"], wraplength=500)
        self._title_label.grid(row=1, column=0, pady=(0, 12))

        ctk.CTkFrame(card, fg_color=C["border"], height=1,
                     corner_radius=0).grid(row=2, column=0, sticky="ew",
                                           padx=24, pady=(0, 12))

        self._body = ctk.CTkTextbox(
            card, fg_color="transparent",
            text_color=C["text2"], font=make_font(12),
            wrap="word", border_width=0,
            scrollbar_button_color=C["border"],
            activate_scrollbars=True,
        )
        self._body.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 24))

        # Nav bar
        nav = ctk.CTkFrame(self, fg_color="transparent", height=56)
        nav.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 14))
        nav.grid_propagate(False)
        nav.grid_columnconfigure(1, weight=1)

        self._back_btn = ctk.CTkButton(
            nav, text="← Back", command=self._prev,
            fg_color="transparent", hover_color=C["border"],
            text_color=C["text2"], border_width=1, border_color=C["border"],
            corner_radius=8, font=make_font(12), width=90, height=36,
        )
        self._back_btn.grid(row=0, column=0, sticky="w")

        self._skip_btn = ctk.CTkButton(
            nav, text="Skip Tour", command=self._finish,
            fg_color="transparent", hover_color=C["border"],
            text_color=C["text3"], font=make_font(11),
            width=80, height=36,
        )
        self._skip_btn.grid(row=0, column=1, sticky="w", padx=8)

        self._next_btn = ctk.CTkButton(
            nav, text="Next →", command=self._next,
            fg_color=C["accent"], hover_color=C["accent_dark"],
            text_color="#ffffff", corner_radius=8,
            font=make_font(12, bold=True), width=130, height=36,
        )
        self._next_btn.grid(row=0, column=2, sticky="e")

    def _show_step(self, index: int) -> None:
        step = STEPS[index]
        self._icon_label.configure(text=step["icon"])
        self._title_label.configure(text=step["title"])
        self._body.configure(state="normal")
        self._body.delete("1.0", "end")
        self._body.insert("end", step["body"])
        self._body.configure(state="disabled")

        # Dots
        for w in self._dots_frame.winfo_children():
            w.destroy()
        dot_row = ctk.CTkFrame(self._dots_frame, fg_color="transparent")
        dot_row.pack(expand=True)
        for i in range(len(STEPS)):
            active = i == index
            size = 10 if active else 7
            ctk.CTkFrame(dot_row, fg_color=C["accent"] if active else C["border"],
                         width=size, height=size,
                         corner_radius=size).pack(side="left", padx=3)

        is_first = index == 0
        is_last  = index == len(STEPS) - 1
        self._back_btn.configure(state="disabled" if is_first else "normal")
        self._next_btn.configure(text="Get Started ✓" if is_last else "Next →")
        if is_last:
            self._skip_btn.grid_remove()
        else:
            self._skip_btn.grid()

    def _next(self) -> None:
        if self._step < len(STEPS) - 1:
            self._step += 1
            self._show_step(self._step)
        else:
            self._finish()

    def _prev(self) -> None:
        if self._step > 0:
            self._step -= 1
            self._show_step(self._step)

    def _finish(self) -> None:
        self.cfg["onboarding_complete"] = True
        try:
            cfg_module.save(self.cfg)
        except Exception:
            pass
        try:
            self.grab_release()
        except Exception:
            pass
        parent = self.master
        on_complete = self.on_complete
        self.destroy()
        try:
            parent.lift()
            parent.focus_force()
        except Exception:
            pass
        if on_complete:
            on_complete()


def should_show(cfg: dict) -> bool:
    return not cfg.get("onboarding_complete", False)
