"""Open Dental send dialog — patient lookup + confirmation."""
import customtkinter as ctk
from app.gui.theme import C, make_font, primary_btn, ghost_btn, make_entry
from app.core.open_dental import OpenDentalConnector


class OdDialog(ctk.CTkToplevel):
    def __init__(self, parent, cfg: dict, note_text: str):
        super().__init__(parent)
        self.cfg = cfg
        self.note_text = note_text
        self.title("Send to Open Dental — DentalScribe v3")
        self.geometry("520x420")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self._patient_num: int | None = None
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="Send Note to Open Dental",
                     font=make_font(15, bold=True),
                     text_color=C["text"]).pack(pady=(24, 4))
        ctk.CTkLabel(self,
                     text="Search for the patient, then confirm before sending.",
                     font=make_font(11), text_color=C["text2"]).pack(pady=(0, 16))

        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=24)

        self._search_var = ctk.StringVar()
        make_entry(search_frame, textvariable=self._search_var,
                   placeholder="Patient last name or ID…",
                   width=280).pack(side="left")
        ghost_btn(search_frame, "Search", command=self._search,
                  height=32).pack(side="left", padx=8)

        self._results_frame = ctk.CTkScrollableFrame(self, fg_color=C["surface"],
                                                      corner_radius=8, height=140)
        self._results_frame.pack(fill="x", padx=24, pady=(8, 0))
        self._results_frame.grid_columnconfigure(0, weight=1)

        self._selected_label = ctk.CTkLabel(self, text="No patient selected.",
                                             font=make_font(11), text_color=C["text3"])
        self._selected_label.pack(pady=(8, 0))

        self._status = ctk.CTkLabel(self, text="", font=make_font(11),
                                     text_color=C["text2"])
        self._status.pack(pady=4)

        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(side="bottom", fill="x", padx=24, pady=16)
        ghost_btn(btn_bar, "Cancel", command=self.destroy, height=36).pack(side="right")
        primary_btn(btn_bar, "Send to Open Dental",
                    command=self._send, height=36).pack(side="right", padx=(0, 8))

    def _search(self) -> None:
        query = self._search_var.get().strip()
        if not query:
            return
        for w in self._results_frame.winfo_children():
            w.destroy()
        conn = self._connector()
        if conn is None:
            return
        results = conn.search_patients(name=query)
        if not results:
            ctk.CTkLabel(self._results_frame, text="No patients found.",
                         font=make_font(11), text_color=C["text3"]).grid(padx=8, pady=8)
            return
        for p in results[:20]:
            pat_id = p.get("PatNum", 0)
            name = f"{p.get('LName', '')}, {p.get('FName', '')}".strip(", ")
            dob = p.get("Birthdate", "")
            label = f"{name}  (#{pat_id})" + (f"  DOB: {dob}" if dob else "")
            ctk.CTkButton(
                self._results_frame, text=label, anchor="w",
                fg_color="transparent", hover_color=C["border"],
                text_color=C["text2"], font=make_font(11), height=32,
                command=lambda pid=pat_id, n=name: self._pick(pid, n),
            ).grid(sticky="ew", padx=4, pady=2)

    def _pick(self, patient_num: int, name: str) -> None:
        self._patient_num = patient_num
        self._selected_label.configure(
            text=f"Selected: {name} (#{patient_num})", text_color=C["success"])

    def _connector(self) -> OpenDentalConnector | None:
        url = self.cfg.get("od_api_url", "").strip()
        key = self.cfg.get("od_developer_key", "").strip()
        if not url or not key:
            self._status.configure(
                text="Open Dental credentials not configured in Settings.",
                text_color=C["warn"])
            return None
        return OpenDentalConnector(url, key, self.cfg.get("od_customer_key", ""))

    def _send(self) -> None:
        if self._patient_num is None:
            self._status.configure(text="Please search and select a patient first.",
                                   text_color=C["warn"])
            return
        conn = self._connector()
        if conn is None:
            return
        self._status.configure(text="Sending…", text_color=C["text2"])
        self.update()
        ok, msg = conn.insert_progress_note(self._patient_num, self.note_text)
        self._status.configure(text=msg,
                               text_color=C["success"] if ok else C["danger"])
        if ok:
            self.after(1500, self.destroy)
