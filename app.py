import sys
import re
from typing import Optional

import webview

from cnpy.db import db
from cnpy.api import server, g, start


if __name__ == "__main__":
    is_debug = False

    for arg in sys.argv[1:]:
        if arg == "--debug":
            is_debug = True

    win = webview.create_window(
        "cnpy",
        server,  # type: ignore
        text_select=True,
        confirm_close=True,
        maximized=True,
    )
    log_win = None

    def web_window(url: str, title: str, args: Optional[dict] = None):
        args = args or {"width": 600}

        return webview.create_window(
            title,
            url,
            text_select=True,
            **args,
        )

    def web_log(s: str, *, height=500):
        global log_win
        if log_win:
            try:
                log_win.width
            except TypeError:
                log_win = None

        current_url = win.get_current_url() or ""
        if not current_url.endswith("/loading.html") and not log_win:
            log_win = web_window(
                re.sub(r"\w+\.html$", "loading.html", current_url),
                "Log",
                {"width": 600, "height": height},
            )

        w = log_win or win
        w.evaluate_js("log('{}')".format(s.replace("'", "\\'").replace("\\", "\\\\")))

    def web_close_log():
        global log_win
        if log_win:
            log_win.destroy()
            log_win = None

    g.web_log = web_log
    g.web_close_log = web_close_log
    g.web_ready = lambda: win.load_url("/dashboard.html")
    g.win = win

    webview.start(lambda: start(), debug=is_debug)

    db.commit()
