import webview
from regex import Regex

import datetime
import sys

from cnpy import load_db
from cnpy.db import db
from cnpy.dir import exe_root
from cnpy.api import server


def prepare():
    load_db()

    db.execute(
        """
        DELETE FROM revlog
        WHERE unixepoch('now') - unixepoch(created) > 60*60*24
        """
    )

    db.execute(
        """
        UPDATE vlist SET skip = NULL
        """
    )

    now = datetime.datetime.now()
    re_han = Regex(r"^\p{Han}+$")

    vs = set()

    path = exe_root / "user/vocab"
    path.mkdir(exist_ok=True)

    for f in path.glob("**/*.txt"):
        for i, v in enumerate(f.open(encoding="utf-8")):
            v = v.strip()
            if v and re_han.fullmatch(v):
                rs = list(db.execute("SELECT v FROM vlist WHERE v = ?", (v,)))

                if not rs:
                    db.execute(
                        "INSERT INTO vlist (v, created) VALUES (?,?)",
                        (
                            v,
                            now.replace(tzinfo=now.astimezone().tzinfo).isoformat(),
                        ),
                    )
                elif v in vs:
                    print(f"{f.relative_to(path)} [L{i+1}]: {v} duplicated")

                vs.add(v)

    path = exe_root / "user/skip"
    path.mkdir(exist_ok=True)

    for f in path.glob("**/*.txt"):
        for i, v in enumerate(f.open(encoding="utf-8")):
            v = v.strip()
            if v and re_han.fullmatch(v):
                if not db.execute(
                    """
                    UPDATE vlist SET
                        skip = 1
                    WHERE v = ?
                    """,
                    (v,),
                ).rowcount:
                    db.execute(
                        "INSERT INTO vlist (v, created, skip) VALUES (?, ?, 1)",
                        (
                            v,
                            now.replace(tzinfo=now.astimezone().tzinfo).isoformat(),
                        ),
                    )


if __name__ == "__main__":
    prepare()

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

    win = webview.create_window("Pinyin Quiz", server)  # type: ignore
    webview.start(lambda: win.evaluate_js(f"newVocab('{v}')"), debug=is_debug)

    db.commit()
