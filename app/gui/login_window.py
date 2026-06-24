"""PIN login window."""
import customtkinter as ctk
from app.gui.theme import C, make_font, primary_btn, make_entry
from app.core.crypto import verify_pin


class LoginWindow(ctk.CTkToplevel):
    def __init__(self, parent, cfg: dict, on_authenticated):
        super().__init__(parent)
        self.cfg = cfg
        self.on_authenticated = on_authenticated
        self.title("DentalScribe v3 — Login")
        self.geometry("360x280")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", parent.destroy)
        self._attempts = 0
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text="DentalScribe v3",
                     font=make_font(20, bold=True),
                     text_color=C["text"]).pack(pady=(40, 4))
        ctk.CTkLabel(self, text="Enter your PIN to continue",
                     font=make_font(12), text_color=C["text2"]).pack(pady=(0, 24))

        self._pin_var = ctk.StringVar()
        e = make_entry(self, textvariable=self._pin_var, placeholder="PIN",
                       show="●", width=200)
        e.pack()
        e.bind("<Return>", lambda _: self._submit())

        primary_btn(self, "Unlock", command=self._submit,
                    width=200, height=38).pack(pady=12)

        self._msg = ctk.CTkLabel(self, text="", font=make_font(11),
                                  text_color=C["danger"])
        self._msg.pack()

    def _submit(self) -> None:
        pin = self._pin_var.get()
        if verify_pin(pin, self.cfg["pin_hash"]):
            from app.core.crypto import derive_key, get_fernet
            self.cfg["_fernet"] = get_fernet(derive_key(pin))
            self.destroy()
            self.on_authenticated()
        else:
            self._attempts += 1
            self._pin_var.set("")
            self._msg.configure(
                text=f"Incorrect PIN. ({self._attempts} failed attempt{'s' if self._attempts > 1 else ''})"
            )
