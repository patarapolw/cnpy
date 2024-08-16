import sys

import webview

from cnpy import load_db
from cnpy.api import Api


if __name__ == "__main__":
    is_debug = "--debug" in sys.argv

    db = load_db()

    api = Api()
    api.log(api.latest_stats)

    win = webview.create_window("Pinyin Quiz", "web/quiz.html", js_api=api)
    webview.start(lambda: win.evaluate_js("newVocab()"), debug=is_debug)

    db.commit()
    api.log(api.get_stats())
