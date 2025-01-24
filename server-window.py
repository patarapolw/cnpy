import sys
from threading import Thread

import webview

from cnpy.db import db
from cnpy.api import server, start


if __name__ == "__main__":
    is_debug = False

    for arg in sys.argv[1:]:
        if arg == "--debug":
            is_debug = True

    t_server = Thread(target=lambda: server.run(port=5000, debug=True), daemon=True)
    t_server.run()

    win = webview.create_window(
        "Pinyin Quiz",
        "http://localhost:3000",
        text_select=True,
        confirm_close=True,
    )
    log_win = None

    webview.start(lambda: start(), debug=is_debug)

    db.commit()
