import sys
from tkinter import Tk

import webview

from cnpy.db import db
from cnpy.api import server, g, start
from cnpy.sync import upload_sync


def enable_dark_titlebar(window):
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
        value = ctypes.c_int(1)
        dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(window.native.Handle.ToInt32()),
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        pass  # silently ignore on unsupported Windows versions


if __name__ == "__main__":
    is_debug = False

    for arg in sys.argv[1:]:
        if arg == "--debug":
            is_debug = True

    tk = Tk()
    tk.withdraw()
    width, height = 1920, 1080
    win_size: dict = {"width": width, "height": height}
    if tk.winfo_screenwidth() < width + 100 or tk.winfo_screenheight() < height + 100:
        win_size = {"maximized": True}
    tk.destroy()

    win = webview.create_window(
        "cnpy",
        server,  # type: ignore
        text_select=True,
        confirm_close=True,
        **win_size,
    )
    log_win = None

    g.web_ready = lambda: win.load_url("/dashboard.html")
    g.win = win

    win.events.before_show += enable_dark_titlebar
    webview.start(
        lambda: start(),
        debug=is_debug,
        private_mode=False,
    )

    db.commit()
    upload_sync()
