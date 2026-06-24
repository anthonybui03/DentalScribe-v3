"""Template manager window — v3."""
import customtkinter as ctk
from app.gui.theme import C, make_font, primary_btn, ghost_btn, danger_btn, make_entry, make_textbox
from app.core.note_templates import registry


class TemplatesWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_change=None):
        super().__init__(parent)
        self.on_change = on_change
        self.title("Manage Templates — DentalScribe v3")
        self.geometry("820x580")
        self.resizable(True, True)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._selected: str | None = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, minsize=240)
        self.grid_columnconfigure(1, weight=1)

        # Left — list
        left = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Templates", font=make_font(13, bold=True),
                     text_color=C["text"]).grid(row=0, column=0, sticky="w",
                                                 padx=12, pady=(12, 6))
        self._list_frame = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                                   scrollbar_button_color=C["border"])
        self._list_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self._list_frame.grid_columnconfigure(0, weight=1)

        ghost_btn(left, "+ New Template", command=self._new_template,
                  height=32).grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 10))

        # Right — editor
        right = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        right.grid_rowconfigure(3, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Template Name", font=make_font(11),
                     text_color=C["text2"]).grid(row=0, column=0, sticky="w",
                                                  padx=14, pady=(14, 2))
        self._name_var = ctk.StringVar()
        self._name_entry = make_entry(right, textvariable=self._name_var,
                                      placeholder="Template name")
        self._name_entry.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        ctk.CTkLabel(right, text="Skeleton / Body", font=make_font(11),
                     text_color=C["text2"]).grid(row=2, column=0, sticky="w",
                                                  padx=14, pady=(0, 2))
        self._body = make_textbox(right)
        self._body.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 8))

        btn_bar = ctk.CTkFrame(right, fg_color="transparent")
        btn_bar.grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 12))
        self._delete_btn = danger_btn(btn_bar, "Delete", command=self._delete, height=32)
        self._delete_btn.pack(side="left")
        primary_btn(btn_bar, "Save Template", command=self._save_template,
                    height=32).pack(side="right")

        self._status = ctk.CTkLabel(right, text="", font=make_font(11),
                                     text_color=C["text2"])
        self._status.grid(row=5, column=0, pady=(0, 6))

        self._set_editor_enabled(False)

    def _refresh_list(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()
        for name, tpl in registry.all().items():
            label = f"{name}  {'(built-in)' if tpl.builtin else ''}"
            btn = ctk.CTkButton(
                self._list_frame, text=label, anchor="w",
                fg_color="transparent", hover_color=C["border"],
                text_color=C["text2"], font=make_font(11),
                height=32, corner_radius=6,
                command=lambda n=name: self._select(n),
            )
            btn.grid(sticky="ew", padx=4, pady=2)

    def _select(self, name: str) -> None:
        self._selected = name
        tpl = registry.get(name)
        self._name_var.set(name)
        self._body.configure(state="normal")
        self._body.delete("1.0", "end")
        self._body.insert("end", tpl.skeleton)
        self._set_editor_enabled(not tpl.builtin)
        if tpl.builtin:
            self._body.configure(state="disabled")
            self._status.configure(text="Built-in templates cannot be edited.",
                                   text_color=C["text3"])
        else:
            self._status.configure(text="")

    def _set_editor_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._name_entry.configure(state=state)
        self._body.configure(state=state)
        self._delete_btn.configure(state=state)

    def _new_template(self) -> None:
        self._selected = None
        self._name_var.set("")
        self._body.configure(state="normal")
        self._body.delete("1.0", "end")
        self._body.insert("end",
            "Chief Complaint:\n\nClinical Findings:\n\nTreatment Provided:\n\nPlan:\n\n"
            "Provider Review: Required before chart entry.\n")
        self._set_editor_enabled(True)
        self._status.configure(text="Enter a name and edit the skeleton, then save.",
                               text_color=C["text3"])
        self._name_entry.focus()

    def _save_template(self) -> None:
        name = self._name_var.get().strip()
        if not name:
            self._status.configure(text="Please enter a template name.", text_color=C["warn"])
            return
        body = self._body.get("1.0", "end").rstrip("\n")
        registry.save_custom(name, body)
        self._selected = name
        self._refresh_list()
        self._status.configure(text=f"'{name}' saved.", text_color=C["success"])
        if self.on_change:
            self.on_change()

    def _delete(self) -> None:
        if not self._selected:
            return
        registry.delete_custom(self._selected)
        self._selected = None
        self._name_var.set("")
        self._body.configure(state="normal")
        self._body.delete("1.0", "end")
        self._set_editor_enabled(False)
        self._refresh_list()
        self._status.configure(text="Template deleted.", text_color=C["text2"])
        if self.on_change:
            self.on_change()
