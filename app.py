import sys
from typing import Optional

import webview
from regex import Regex

from cnpy.db import db
from cnpy.api import Api


if __name__ == "__main__":
    is_debug = False
    v = ""

    re_han = Regex(r"\p{Han}+")
    for arg in sys.argv[1:]:
        if arg == "--debug":
            is_debug = True
        elif arg == "--vocab":
            v = input("Please input vocabulary to load: ")
        elif re_han.fullmatch(arg):
            v = arg

    api = Api(v=v)

    win = webview.create_window(
        "Pinyin Quiz",
        "web/loading.html",
        js_api=api,
        text_select=True,
    )
    log_win = None

    def web_window(url: str, title: str, args: Optional[dict] = None):
        args = args or {"width": 600}

        return webview.create_window(
            title,
            url,
            js_api=api,
            text_select=True,
            **args,
        )

    def web_log(s: str):
        global log_win
        if not log_win:
            log_win = web_window("web/loading.html", "Log")

        w = log_win or win
        w.evaluate_js("log('{}')".format(s.replace("'", "\\'").replace("\\", "\\\\")))

    api.web_log = web_log
    api.web_ready = lambda: win.load_url("web/dashboard.html")
    api.web_window = web_window

    webview.start(lambda: api.start(), debug=is_debug)

    db.commit()
