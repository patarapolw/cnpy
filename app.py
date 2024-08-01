import webview

from cjpy import load_db
from cjpy.api import Api


if __name__ == "__main__":
    load_db()

    api = Api()
    api.log(api.stats())

    win = webview.create_window(
        "Pinyin Quiz",
        "web/cedict.html",
        js_api=api,
    )
    webview.start(lambda: win.evaluate_js("newVocab()"))
