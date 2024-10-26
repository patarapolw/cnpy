from regex import Regex
import jieba

import json
from urllib.request import urlretrieve
from zipfile import ZipFile
from typing import Callable

from cnpy.db import db, assets_db
from cnpy.dir import tmp_root


def load_db(web_log: Callable[[str], None] = print):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS cedict (
            simp    TEXT NOT NULL,
            trad    TEXT,
            pinyin  TEXT NOT NULL,
            english JSON NOT NULL,
            [data]  JSON
        );

        CREATE INDEX IF NOT EXISTS idx_cedict_simp ON cedict (simp);
        CREATE INDEX IF NOT EXISTS idx_cedict_trad ON cedict (trad);
        """
    )

    populate_db(web_log)


def load_db_entry(r):
    r = dict(r)

    for k in ("data", "english"):
        if type(r[k]) is str:
            r[k] = json.loads(r[k])

    for k in list(r.keys()):
        if r[k] is None:
            del r[k]

    return r


def populate_db(web_log: Callable[[str], None] = print):
    if not db.execute("SELECT 1 FROM cedict LIMIT 1").fetchall():
        filename = "cedict_ts.u8"
        cedict = tmp_root / filename

        if not cedict.exists():
            zipPath = tmp_root / "cedict.zip"

            url = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip"
            web_log("Downloading {} from {}".format(filename, url))
            urlretrieve(url, zipPath)

            with ZipFile(zipPath) as z:
                z.extract(cedict.name, path=cedict.parent)

        web_log("Building vocab dictionary...")

        for ln in cedict.open("r", encoding="utf8"):
            if ln[0] == "#":
                continue

            trad, simp, _ = ln.split(" ", 2)
            ln = ln[len(trad) + len(simp) + 2 :]

            if trad == simp:
                trad = None

            if not simp:
                continue

            start_idx = ln.find("[")
            end_idx = ln.find("]")

            pinyin = ln[start_idx + 1 : end_idx]

            if not pinyin:
                continue

            ln = ln[end_idx + 1 :]

            english = []

            while ln:
                start_idx = ln.find("/")
                if start_idx == -1:
                    break

                ln = ln[start_idx + 1 :]

                end_idx = ln.find("/")
                if end_idx == -1:
                    break

                english.append(ln[0:end_idx].split("; "))

            db.execute(
                "INSERT INTO cedict (simp, trad, pinyin, english) VALUES (?,?,?,?)",
                (simp, trad, pinyin, json.dumps(english, ensure_ascii=False)),
            )

        db.commit()

        web_log("Done")

    if not db.execute(
        "SELECT 1 FROM quiz WHERE json_extract([data], '$.wordfreq') IS NOT NULL LIMIT 1"
    ).fetchall():
        web_log("Building wordfreq...")

        re_han = Regex(r"^\p{Han}+$")

        for r in db.execute("SELECT DISTINCT simp FROM cedict"):
            v = r["simp"]
            if not re_han.fullmatch(v):
                continue

            db.execute("INSERT INTO quiz (v) VALUES (?) ON CONFLICT DO NOTHING", (v,))

        db.commit()

        for r in db.execute("SELECT v, [data] FROM quiz"):
            d = json.loads(r["data"]) if r["data"] else {}

            if "wordfreq" not in d:
                for k in assets_db.execute(
                    "SELECT f FROM wordfreq WHERE v = ? LIMIT 1", (r["v"],)
                ):
                    d["wordfreq"] = k["f"]

            if "vs" not in d:
                d["vs"] = list(
                    set(
                        s
                        for s in jieba.cut_for_search(r["v"])
                        if re_han.fullmatch(r["v"])
                    )
                )

            db.execute(
                "UPDATE quiz SET [data] = ? WHERE v = ?",
                (json.dumps(d, ensure_ascii=False), r["v"]),
            )

        db.commit()

        web_log("Done")


def reset_db():
    db.executescript(
        """
        DROP TABLE cedict;
        """
    )

    load_db()


if __name__ == "__main__":
    reset_db()
