import sys
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
        "Pinyin Quiz",
        server,  # type: ignore
        text_select=True,
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

    def web_log(s: str):
        global log_win
        if not (win.get_current_url() or "").endswith("/loading.html") and not log_win:
            log_win = web_window("/loading.html", "Log")

        w = log_win or win
        w.evaluate_js("log('{}')".format(s.replace("'", "\\'").replace("\\", "\\\\")))

    g.web_log = web_log
    g.web_ready = lambda: win.load_url("/dashboard.html")
    g.web_window = web_window

    webview.start(lambda: start(), debug=is_debug)

    db.commit()
