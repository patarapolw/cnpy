import sys
import os
from threading import Thread
import atexit

from cnpy.db import db
from cnpy.api import server, start, g
from cnpy.sync import upload_sync


if __name__ == "__main__":
    is_debug = False

    for arg in sys.argv[1:]:
        if arg == "--debug":
            is_debug = True

    def on_close():
        db.commit()
        upload_sync()

    atexit.register(on_close)

    t_server = Thread(
        target=lambda: server.run(port=5000, debug=True),
        daemon=False,  # Blocking thread
    )
    t_server.run()

    g.web_ready = lambda: None

    start()
