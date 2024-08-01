from wordfreq import zipf_frequency
from regex import Regex

import json
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

from cjpy.db import db


def load_db():
    # db.executescript(
    #     """
    #     DROP TABLE IF EXISTS cedict;
    #     """
    # )

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS cedict (
            simp    TEXT NOT NULL,
            trad    TEXT,
            pinyin  TEXT NOT NULL,
            english JSON NOT NULL,
            [data]  JSON
        );

        CREATE INDEX IF NOT EXISTS idx_cedict_simp_trad ON cedict (simp, trad);
        CREATE INDEX IF NOT EXISTS idx_cedict_pinyin ON cedict (pinyin);
        CREATE INDEX IF NOT EXISTS idx_cedict_wordfreq ON cedict (json_extract([data], '$.wordfreq'));

        CREATE TABLE IF NOT EXISTS quiz (
            v       TEXT NOT NULL PRIMARY KEY,
            srs     JSON,
            [data]  JSON
        );

        CREATE INDEX IF NOT EXISTS idx_quiz_srs_due ON quiz (json_extract(srs, '$.due'));
        CREATE INDEX IF NOT EXISTS idx_quiz_wordfreq ON quiz (json_extract([data], '$.wordfreq'));
        """
    )

    # db.executescript(
    #     """
    #     UPDATE cedict SET [data] = NULL WHERE [data] = '{}';
    #     """
    # )

    populate_db()


def populate_db():
    if not db.execute("SELECT 1 FROM cedict LIMIT 1").fetchall():
        cedict = Path("assets/dic/cedict_ts.u8")

        if not cedict.exists():
            zipPath = Path("cedict.zip")

            urlretrieve(
                "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip",
                zipPath,
            )

            with ZipFile(zipPath) as z:
                z.extract(cedict.name, path=cedict)

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
