import os
import socket
from threading import Thread

from cnpy.api import server
from cnpy.app import prepare, run


def main_dev():
    is_bottle_child = bool(os.getenv("BOTTLE_CHILD"))

    if not is_bottle_child:
        prepare()

    bottle_port = int(os.getenv("BOTTLE_PORT", "0"))

    if is_bottle_child:
        server.run(reloader=True, port=bottle_port)
    else:
        if not bottle_port:
            sock = socket.socket()
            sock.bind(("", 0))
            bottle_port = sock.getsockname()[1]
            os.environ["BOTTLE_PORT"] = str(bottle_port)

        Thread(
            target=lambda s, p: s.run(reloader=True, port=p),
            args=(server, bottle_port),
            daemon=True,
        ).start()

        port = os.getenv("PORT", str(bottle_port))
        run(dev_url=f"http://localhost:{port}")


if __name__ == "__main__":
    main_dev()
