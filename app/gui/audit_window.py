"""Audit log viewer — v3."""
import customtkinter as ctk
from app.gui.theme import C, make_font, ghost_btn, make_entry
from app.core import audit_log


class AuditWindow(ctk.CTkToplevel):
    def __init__(self, parent, cfg: dict):
        super().__init__(parent)
        self.cfg = cfg
        self.title("Audit Log — DentalScribe v3")
        self.geometry("820x540")
        self.resizable(True, True)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))

        self._search_var = ctk.StringVar()
        make_entry(top, textvariable=self._search_var,
                   placeholder="Filter by action or user…",
                   width=240).pack(side="left", padx=(0, 6))
        ghost_btn(top, "Filter", command=self._load, height=30).pack(side="left")
        ghost_btn(top, "Export…", command=self._export, height=30).pack(side="left", padx=6)

        self._count_label = ctk.CTkLabel(top, text="", font=make_font(10),
                                          text_color=C["text3"])
        self._count_label.pack(side="right")

        frame = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=10)
        frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self._box = ctk.CTkScrollableFrame(frame, fg_color="transparent",
                                            scrollbar_button_color=C["border"])
        self._box.grid(row=0, column=0, sticky="nsew")
        self._box.grid_columnconfigure(0, weight=1)

    def _load(self) -> None:
        events = audit_log.load_events(self.cfg.get("_fernet"), limit=500)
        q = self._search_var.get().lower()
        if q:
            events = [e for e in events
                      if q in e.get("action", "").lower() or q in e.get("user", "").lower()]
        for w in self._box.winfo_children():
            w.destroy()
        self._count_label.configure(text=f"{len(events)} events")
        for e in events:
            ts   = e.get("ts", "")
            user = e.get("user", "")
            act  = e.get("action", "")
            det  = e.get("detail", "")
            line = f"[{ts}]  {user}  —  {act}"
            if det:
                line += f"  ·  {det}"
            ctk.CTkLabel(self._box, text=line, font=make_font(10),
                         text_color=C["text2"], anchor="w",
                         wraplength=760, justify="left").grid(
                sticky="ew", padx=8, pady=1)

    def _export(self) -> None:
        from tkinter import filedialog, messagebox
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Audit Log",
        )
        if not path:
            return
        text = audit_log.export_plaintext(self.cfg.get("_fernet"))
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        messagebox.showinfo("Exported", f"Audit log saved to:\n{path}")
