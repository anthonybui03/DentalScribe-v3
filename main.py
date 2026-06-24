"""DentalScribe v3 — entry point."""
import subprocess
import sys
import time
import urllib.request
import customtkinter as ctk

from app.core import config as cfg_module
from app.gui import theme  # noqa: F401


def _ensure_ollama() -> None:
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return
    except Exception:
        pass
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        for _ in range(20):
            time.sleep(0.5)
            try:
                urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
                return
            except Exception:
                pass
    except FileNotFoundError:
        pass


def main() -> None:
    _ensure_ollama()
    cfg = cfg_module.load()

    root = ctk.CTk()
    root.title("DentalScribe v3")
    root.geometry("1240x760")
    root.minsize(960, 620)
    from app.gui.theme import C
    root.configure(fg_color=C["bg"])

    def launch_main() -> None:
        from app.gui.main_window import MainWindow
        from app.gui.onboarding import OnboardingWindow, should_show
        MainWindow(root, cfg)
        if should_show(cfg):
            root.after(400, lambda: OnboardingWindow(root, cfg))

    if cfg.get("pin_hash"):
        from app.gui.login_window import LoginWindow
        LoginWindow(root, cfg, on_authenticated=launch_main)
    else:
        launch_main()

    root.mainloop()


if __name__ == "__main__":
    main()
