import sys
from tkinter import Tk

import webview

from cnpy.db import db
from cnpy.api import server, g, start


if __name__ == "__main__":
    is_debug = False

    for arg in sys.argv[1:]:
        if arg == "--debug":
            is_debug = True

    tk = Tk()
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

    webview.start(lambda: start(), debug=is_debug)

    db.commit()
