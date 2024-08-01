import webview

from cjpy import load_db
from cjpy.api import Api


if __name__ == "__main__":
    load_db()

    win = webview.create_window(
        "Pinyin Quiz",
        "web/cjdict.html",
        js_api=Api(),
    )
    webview.start(lambda: win.evaluate_js("newVocab()"))
