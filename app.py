import sys

import webview
from regex import Regex

from cnpy import load_db
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

    db = load_db()

    api = Api(v=v)

    win = webview.create_window("Pinyin Quiz", "web/dashboard.html", js_api=api)
    webview.start(debug=is_debug)

    db.commit()
