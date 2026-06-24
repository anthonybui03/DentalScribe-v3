"""Provider management window."""
import customtkinter as ctk
from app.gui.theme import C, make_font, primary_btn, ghost_btn, danger_btn, make_entry, make_combo
from app.core.providers import (
    Provider, list_providers, add_provider,
    update_provider, delete_provider, format_provider,
)

TITLES = ["", "Dr.", "RDH", "Mr.", "Ms.", "Mrs."]
CREDENTIALS = ["", "DDS", "DMD", "RDH", "MS", "PhD", "MD"]


class ProvidersWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        self.title("Manage Providers — DentalScribe v3")
        self.geometry("760x520")
        self.resizable(True, True)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._selected: Provider | None = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, minsize=240)
        self.grid_columnconfigure(1, weight=1)

        # ── Left: list ────────────────────────────────────────────────────────
        left = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Providers", font=make_font(13, bold=True),
                     text_color=C["text"]).grid(row=0, column=0, sticky="w",
                                                 padx=12, pady=(12, 6))

        self._list_frame = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                                   scrollbar_button_color=C["border"])
        self._list_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._list_frame.grid_columnconfigure(0, weight=1)

        ghost_btn(left, "+ Add Provider", command=self._new_provider,
                  height=32).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 10))

        # ── Right: editor ─────────────────────────────────────────────────────
        right = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        right.grid_columnconfigure(1, weight=1)

        def field(row, label, widget, **kw):
            ctk.CTkLabel(right, text=label, font=make_font(11),
                         text_color=C["text2"], anchor="e",
                         width=110).grid(row=row, column=0, sticky="e",
                                         padx=(14, 8), pady=6)
            w = widget(right, **kw)
            w.grid(row=row, column=1, sticky="ew", padx=(0, 14), pady=6)
            return w

        ctk.CTkLabel(right, text="Provider Details", font=make_font(13, bold=True),
                     text_color=C["text"]).grid(row=0, column=0, columnspan=2,
                                                 sticky="w", padx=14, pady=(14, 4))

        self._name_var  = ctk.StringVar()
        self._title_var = ctk.StringVar()
        self._cred_var  = ctk.StringVar()
        self._npi_var   = ctk.StringVar()

        self._name_entry = field(1, "Full Name *",
            make_entry, textvariable=self._name_var, placeholder="e.g. Jane Smith")

        self._title_combo = field(2, "Title",
            make_combo, values=TITLES, width=140)
        self._title_combo.set("")

        self._cred_combo = field(3, "Credentials",
            make_combo, values=CREDENTIALS, width=140)
        self._cred_combo.set("")

        self._npi_entry = field(4, "NPI (optional)",
            make_entry, textvariable=self._npi_var, placeholder="10-digit NPI")

        # Preview
        self._preview = ctk.CTkLabel(right, text="", font=make_font(12, bold=True),
                                      text_color=C["accent"])
        self._preview.grid(row=5, column=0, columnspan=2, padx=14, pady=(4, 12))

        for var in (self._name_var, self._title_var, self._npi_var):
            var.trace_add("write", lambda *_: self._update_preview())
        self._title_combo.configure(command=lambda _: self._update_preview())
        self._cred_combo.configure(command=lambda _: self._update_preview())

        # Buttons
        btn_bar = ctk.CTkFrame(right, fg_color="transparent")
        btn_bar.grid(row=6, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 14))

        self._delete_btn = danger_btn(btn_bar, "Delete", command=self._delete, height=32)
        self._delete_btn.pack(side="left")
        primary_btn(btn_bar, "Save Provider", command=self._save, height=32).pack(side="right")

        self._status = ctk.CTkLabel(right, text="", font=make_font(11),
                                     text_color=C["text2"])
        self._status.grid(row=7, column=0, columnspan=2, pady=(0, 8))

        self._set_enabled(False)

    def _update_preview(self) -> None:
        from app.core.providers import Provider, format_provider
        p = Provider(0, self._name_var.get(), self._title_combo.get(),
                     self._cred_combo.get(), self._npi_var.get())
        preview = format_provider(p)
        self._preview.configure(text=preview if preview.strip() else "")

    def _refresh_list(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()
        providers = list_providers()
        if not providers:
            ctk.CTkLabel(self._list_frame, text="No providers yet.\nClick + Add Provider.",
                         font=make_font(11), text_color=C["text3"],
                         justify="center").grid(padx=8, pady=16)
            return
        for p in providers:
            label = format_provider(p)
            if p.npi:
                label += f"\nNPI: {p.npi}"
            ctk.CTkButton(
                self._list_frame, text=label, anchor="w",
                fg_color="transparent", hover_color=C["border"],
                text_color=C["text2"], font=make_font(11),
                height=44, corner_radius=6,
                command=lambda prov=p: self._select(prov),
            ).grid(sticky="ew", padx=4, pady=2)

    def _select(self, p: Provider) -> None:
        self._selected = p
        self._name_var.set(p.name)
        self._title_combo.set(p.title)
        self._cred_combo.set(p.credentials)
        self._npi_var.set(p.npi)
        self._set_enabled(True)
        self._status.configure(text="")
        self._update_preview()

    def _new_provider(self) -> None:
        self._selected = None
        self._name_var.set("")
        self._title_combo.set("")
        self._cred_combo.set("")
        self._npi_var.set("")
        self._set_enabled(True)
        self._status.configure(text="Fill in the details and click Save.",
                               text_color=C["text3"])
        self._update_preview()
        self._name_entry.focus()

    def _set_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._name_entry.configure(state=state)
        self._npi_entry.configure(state=state)
        self._delete_btn.configure(state="normal" if (enabled and self._selected) else "disabled")

    def _save(self) -> None:
        name = self._name_var.get().strip()
        if not name:
            self._status.configure(text="Full name is required.", text_color=C["warn"])
            return
        title = self._title_combo.get()
        creds = self._cred_combo.get()
        npi   = self._npi_var.get().strip()

        if self._selected:
            update_provider(self._selected.id, name, title, creds, npi)
            self._status.configure(text="Provider updated.", text_color=C["success"])
        else:
            p = add_provider(name, title, creds, npi)
            self._selected = p
            self._status.configure(text="Provider added.", text_color=C["success"])

        self._refresh_list()
        if self.on_change:
            self.on_change()

    def _delete(self) -> None:
        if not self._selected:
            return
        from tkinter import messagebox
        if not messagebox.askyesno("Delete Provider",
                                   f"Delete {format_provider(self._selected)}?",
                                   parent=self):
            return
        delete_provider(self._selected.id)
        self._selected = None
        self._name_var.set("")
        self._title_combo.set("")
        self._cred_combo.set("")
        self._npi_var.set("")
        self._set_enabled(False)
        self._preview.configure(text="")
        self._status.configure(text="Provider deleted.", text_color=C["text2"])
        self._refresh_list()
        if self.on_change:
            self.on_change()
