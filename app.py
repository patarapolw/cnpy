import sys

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

    api.web_log = lambda s: win.evaluate_js(
        "log('{}')".format(s.replace("'", "\\'").replace("\\", "\\\\"))
    )
    api.web_location = lambda s: win.evaluate_js(
        "location.href = '{}'".format(s.replace("'", "\\'").replace("\\", "\\\\"))
    )
    api.web_ready = lambda: win.evaluate_js("ready()")

    webview.start(lambda: api.start(), debug=is_debug)

    db.commit()
