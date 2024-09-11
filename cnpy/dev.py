import os
import socket
from threading import Thread

from cnpy.api import server
from cnpy.app import prepare, run


def main_dev():
    is_bottle_child = bool(os.getenv("BOTTLE_CHILD"))

    if not is_bottle_child:
        prepare()

    PORT_ENV = "PORT"
    port = int(os.getenv(PORT_ENV, "0"))

    if is_bottle_child:
        server.run(reloader=True, port=port)
    else:
        if not port:
            sock = socket.socket()
            sock.bind(("", 0))
            port = sock.getsockname()[1]
            os.environ[PORT_ENV] = str(port)

        Thread(
            target=lambda s, p: s.run(reloader=True, port=p),
            args=(server, port),
            daemon=True,
        ).start()

    run(dev_url=f"http://localhost:{port}")


if __name__ == "__main__":
    main_dev()
