from wordfreq import zipf_frequency
from regex import Regex

import json
from urllib.request import urlretrieve
from zipfile import ZipFile

from cjpy.db import db
from cjpy.dir import exe_root, tempdir


def load_db():
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
        """
    )

    populate_db()


def load_db_entry(r):
    r = dict(r)

    for k in ("data", "english"):
        if type(r[k]) is str:
            r[k] = json.loads(r[k])

    for k in list(r.keys()):
        if r[k] is None:
            del r[k]

    return r


def populate_db():
    if not db.execute("SELECT 1 FROM cedict LIMIT 1").fetchall():
        filename = "cedict_ts.u8"
        cedict = exe_root / "assets/dic" / filename

        if not cedict.exists():
            cedict.parent.mkdir(parents=True, exist_ok=True)

            zipPath = tempdir() / "cedict.zip"

            url = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip"
            print("Downloading {} from {}".format(filename, url))
            urlretrieve(url, zipPath)

            with ZipFile(zipPath) as z:
                z.extract(cedict.name, path=cedict.parent)

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

        db.execute(
            """
            UPDATE quiz SET
                [data] = json_remove([data], '$.wordfreq')
            WHERE [data] IS NOT NULL
            """
        )

        db.commit()

    if not db.execute(
        "SELECT 1 FROM quiz WHERE json_extract([data], '$.wordfreq') IS NOT NULL LIMIT 1"
    ).fetchall():
        f_dict = {}
        re_han = Regex(r"^\p{Han}+$")

        for r in db.execute("SELECT DISTINCT simp FROM cedict"):
            v = r["simp"]
            if v not in f_dict and re_han.fullmatch(v):
                f_dict[v] = zipf_frequency(v, "zh")

        for v, f in f_dict.items():
            is_updated = db.execute(
                """
                UPDATE quiz SET
                    [data] = json_set(IFNULL([data], '{}'), '$.wordfreq', ?)
                WHERE v = ?
                """,
                (f, v),
            ).rowcount

            if not is_updated:
                db.execute(
                    """
                    INSERT INTO quiz (v, [data]) VALUES (?, json_object('wordfreq', ?))
                    """,
                    (v, f),
                )

        db.commit()


def reset_db():
    db.executescript(
        """
        DROP TABLE cedict;
        """
    )

    load_db()

    db.executescript(
        """
        UPDATE cedict SET [data] = NULL WHERE [data] = '{}';
        """
    )


if __name__ == "__main__":
    reset_db()
