"""CustomTkinter theme — v3."""
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":          "#0A0F1E",
    "surface":     "#111827",
    "surface2":    "#1A2235",
    "border":      "#1E3A5F",
    "accent":      "#2563EB",
    "accent_dark": "#1D4ED8",
    "accent2":     "#7C3AED",
    "text":        "#F1F5F9",
    "text2":       "#94A3B8",
    "text3":       "#475569",
    "success":     "#22C55E",
    "warn":        "#F59E0B",
    "warn_bg":     "#451A03",
    "danger":      "#EF4444",
    "record":      "#EF4444",
    "record_dark": "#C41E1E",
}

STATUS_COLORS = {
    "normal":  C["text2"],
    "success": C["success"],
    "warn":    C["warn"],
    "danger":  C["danger"],
    "record":  C["record"],
}


def make_font(size: int = 12, bold: bool = False) -> ctk.CTkFont:
    return ctk.CTkFont("Segoe UI", size, weight="bold" if bold else "normal")


def mono_font(size: int = 11) -> ctk.CTkFont:
    return ctk.CTkFont("Consolas", size)


def section_label(parent, text: str) -> ctk.CTkLabel:
    return ctk.CTkLabel(parent, text=text.upper(),
                        font=make_font(10, bold=True), text_color=C["text3"])


def divider(parent) -> ctk.CTkFrame:
    return ctk.CTkFrame(parent, height=1, fg_color=C["border"], corner_radius=0)


def primary_btn(parent, text: str, command=None, **kw) -> ctk.CTkButton:
    defaults = dict(
        fg_color=C["accent"], hover_color=C["accent_dark"],
        text_color="#ffffff", corner_radius=8,
        font=make_font(12, bold=True),
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, text=text, command=command, **defaults)


def ghost_btn(parent, text: str, command=None, **kw) -> ctk.CTkButton:
    defaults = dict(
        fg_color="transparent", hover_color=C["border"],
        text_color=C["text2"], border_width=1,
        border_color=C["border"], corner_radius=8,
        font=make_font(11),
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, text=text, command=command, **defaults)


def subtle_btn(parent, text: str, command=None, **kw) -> ctk.CTkButton:
    defaults = dict(
        fg_color="transparent", hover_color=C["surface2"],
        text_color=C["text2"], corner_radius=8,
        font=make_font(11),
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, text=text, command=command, **defaults)


def danger_btn(parent, text: str, command=None, **kw) -> ctk.CTkButton:
    defaults = dict(
        fg_color="transparent", hover_color=C["danger"],
        text_color=C["danger"], border_width=1,
        border_color=C["danger"], corner_radius=8,
        font=make_font(11),
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, text=text, command=command, **defaults)


def make_entry(parent, textvariable=None, placeholder: str = "",
               show: str = "", **kw) -> ctk.CTkEntry:
    defaults = dict(
        fg_color=C["surface2"], border_color=C["border"],
        text_color=C["text"], placeholder_text_color=C["text3"],
        corner_radius=8,
    )
    defaults.update(kw)
    return ctk.CTkEntry(parent, textvariable=textvariable,
                        placeholder_text=placeholder, show=show, **defaults)


def make_textbox(parent, **kw) -> ctk.CTkTextbox:
    defaults = dict(
        fg_color=C["surface2"], text_color=C["text"],
        font=mono_font(11), corner_radius=10,
        border_width=1, border_color=C["border"],
        scrollbar_button_color=C["border"],
        scrollbar_button_hover_color=C["text3"],
        wrap="word",
    )
    defaults.update(kw)
    return ctk.CTkTextbox(parent, **defaults)


def make_combo(parent, values=None, command=None, **kw) -> ctk.CTkComboBox:
    defaults = dict(
        fg_color=C["surface2"], border_color=C["border"],
        button_color=C["border"], button_hover_color=C["accent"],
        text_color=C["text"], dropdown_fg_color=C["surface"],
        dropdown_text_color=C["text"], dropdown_hover_color=C["accent"],
        corner_radius=8, font=make_font(11), state="normal",
    )
    defaults.update(kw)
    return ctk.CTkComboBox(parent, values=values or [], command=command, **defaults)
