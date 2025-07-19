import sys
from threading import Thread
import atexit

from cnpy.db import db
from cnpy.api import server, start, g


if __name__ == "__main__":
    is_debug = False

    for arg in sys.argv[1:]:
        if arg == "--debug":
            is_debug = True

    atexit.register(lambda: db.commit())

    t_server = Thread(
        target=lambda: server.run(port=5000, debug=True),
        daemon=False,  # Blocking thread
    )
    t_server.run()

    g.web_ready = lambda: None

    start()
