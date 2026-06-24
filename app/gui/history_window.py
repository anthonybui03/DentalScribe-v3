"""Note history viewer — SQLite-backed, full-text search, paginated."""
import customtkinter as ctk
from app.gui.theme import C, make_font, ghost_btn, make_entry
from app.core import note_history


PAGE_SIZE = 50


class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Note History — DentalScribe v3")
        self.geometry("900x620")
        self.resizable(True, True)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._offset = 0
        self._entries: list[note_history.HistoryEntry] = []
        self._selected_idx: int | None = None
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Search bar
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))

        self._patient_var  = ctk.StringVar()
        self._provider_var = ctk.StringVar()
        self._search_var   = ctk.StringVar()

        make_entry(top, textvariable=self._patient_var, placeholder="Patient ID",
                   width=130).pack(side="left", padx=(0, 6))
        make_entry(top, textvariable=self._provider_var, placeholder="Provider",
                   width=130).pack(side="left", padx=(0, 6))
        make_entry(top, textvariable=self._search_var,
                   placeholder="Search notes/transcripts…",
                   width=200).pack(side="left", padx=(0, 6))
        ghost_btn(top, "Search", command=self._search, height=30).pack(side="left")
        ghost_btn(top, "Clear", command=self._clear_search, height=30).pack(side="left", padx=4)

        self._count_label = ctk.CTkLabel(top, text="", font=make_font(10), text_color=C["text3"])
        self._count_label.pack(side="right")

        # Split: list | detail
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, minsize=280)
        body.grid_columnconfigure(1, weight=1)

        # List
        list_frame = ctk.CTkFrame(body, fg_color=C["surface"], corner_radius=10)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self._list_box = ctk.CTkScrollableFrame(list_frame, fg_color="transparent",
                                                 scrollbar_button_color=C["border"])
        self._list_box.grid(row=0, column=0, sticky="nsew")
        self._list_box.grid_columnconfigure(0, weight=1)

        page_bar = ctk.CTkFrame(list_frame, fg_color="transparent")
        page_bar.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        ghost_btn(page_bar, "◀ Prev", command=self._prev_page,
                  height=28, width=80).pack(side="left")
        ghost_btn(page_bar, "Next ▶", command=self._next_page,
                  height=28, width=80).pack(side="right")

        # Detail
        detail = ctk.CTkFrame(body, fg_color=C["surface"], corner_radius=10)
        detail.grid(row=0, column=1, sticky="nsew")
        detail.grid_rowconfigure(1, weight=1)
        detail.grid_columnconfigure(0, weight=1)

        self._detail_header = ctk.CTkLabel(detail, text="Select an entry to view",
                                            font=make_font(11), text_color=C["text2"])
        self._detail_header.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        self._detail_box = make_textbox(detail)
        self._detail_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 4))
        self._detail_box.configure(state="disabled")

        detail_btns = ctk.CTkFrame(detail, fg_color="transparent")
        detail_btns.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        ghost_btn(detail_btns, "Copy Note", command=self._copy_note,
                  height=30).pack(side="left")
        ghost_btn(detail_btns, "Delete Entry", command=self._delete_entry,
                  height=30, text_color=C["danger"],
                  border_color=C["danger"]).pack(side="right")

    def _load(self) -> None:
        self._entries = note_history.load_entries(
            patient_id=self._patient_var.get(),
            search=self._search_var.get(),
            provider=self._provider_var.get(),
            limit=PAGE_SIZE,
            offset=self._offset,
        )
        total = note_history.count_entries()
        self._count_label.configure(text=f"{total} total entries")
        self._render_list()

    def _render_list(self) -> None:
        for w in self._list_box.winfo_children():
            w.destroy()
        if not self._entries:
            ctk.CTkLabel(self._list_box, text="No entries found.",
                         font=make_font(11), text_color=C["text3"]).grid(padx=8, pady=8)
            return
        for i, e in enumerate(self._entries):
            provider_str = f"  ·  {e.provider}" if e.provider else ""
            text = f"{e.timestamp[:16]}\n{e.patient_id or '—'}  ·  {e.template}{provider_str}"
            btn = ctk.CTkButton(
                self._list_box, text=text, anchor="w",
                fg_color="transparent", hover_color=C["border"],
                text_color=C["text2"], font=make_font(10),
                height=48, corner_radius=6,
                command=lambda idx=i: self._select(idx),
            )
            btn.grid(sticky="ew", padx=4, pady=2)

    def _select(self, idx: int) -> None:
        self._selected_idx = idx
        e = self._entries[idx]
        provider_str = f"  ·  {e.provider}" if e.provider else ""
        self._detail_header.configure(
            text=f"{e.timestamp}  ·  {e.patient_id or 'No patient'}  ·  {e.template}{provider_str}")
        self._detail_box.configure(state="normal")
        self._detail_box.delete("1.0", "end")
        self._detail_box.insert("end", f"── TRANSCRIPT ──\n{e.transcript}\n\n── NOTE ──\n{e.note}")
        self._detail_box.configure(state="disabled")

    def _copy_note(self) -> None:
        if self._selected_idx is None:
            return
        note = self._entries[self._selected_idx].note
        self.clipboard_clear()
        self.clipboard_append(note)

    def _delete_entry(self) -> None:
        if self._selected_idx is None:
            return
        from tkinter import messagebox
        if messagebox.askyesno("Delete", "Delete this history entry?", parent=self):
            note_history.delete_entry(self._entries[self._selected_idx].id)
            self._selected_idx = None
            self._detail_box.configure(state="normal")
            self._detail_box.delete("1.0", "end")
            self._detail_box.configure(state="disabled")
            self._load()

    def _search(self) -> None:
        self._offset = 0
        self._load()

    def _clear_search(self) -> None:
        self._patient_var.set("")
        self._provider_var.set("")
        self._search_var.set("")
        self._offset = 0
        self._load()

    def _prev_page(self) -> None:
        if self._offset >= PAGE_SIZE:
            self._offset -= PAGE_SIZE
            self._load()

    def _next_page(self) -> None:
        if len(self._entries) == PAGE_SIZE:
            self._offset += PAGE_SIZE
            self._load()
