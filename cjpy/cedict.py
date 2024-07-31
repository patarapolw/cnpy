from wordfreq import zipf_frequency

import json

from cjpy.db import db


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

        CREATE INDEX IF NOT EXISTS idx_cedict_simp_trad ON cedict (simp, trad);
        CREATE INDEX IF NOT EXISTS idx_cedict_pinyin ON cedict (pinyin);
        CREATE INDEX IF NOT EXISTS idx_cedict_wordfreq ON cedict (json_extract([data], '$.wordfreq'));
        """
    )
    populate_db()


def populate_db():
    if not db.execute("SELECT 1 FROM cedict LIMIT 1").fetchall():
        for ln in open("assets/dic/cedict_ts.u8", encoding="utf8"):
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

    f_dict = {}

    for r in db.execute(
        "SELECT simp FROM cedict WHERE json_extract([data], '$.wordfreq') IS NULL"
    ):
        v = r["simp"]
        if v not in f_dict:
            f_dict[v] = zipf_frequency(v, "zh")

    for v, f in f_dict.items():
        db.execute(
            """
            UPDATE cedict SET
                [data] = json_set(IFNULL([data], '{}'), '$.wordfreq', ?)
            WHERE simp = ?
            """,
            (f, v),
        )

    db.commit()


if __name__ == "__main__":
    import webview

    load_db()

    class Api:
        def new_vocab(self):
            r = dict(
                db.execute(
                    """
                    SELECT
                        simp,
                        REPLACE(GROUP_CONCAT(DISTINCT pinyin), ',', '; ') pinyin,
                        json_group_array(english) en
                    FROM cedict
                    WHERE json_extract([data], '$.wordfreq') > 5
                    GROUP BY simp
                    ORDER BY RANDOM() LIMIT 1
                    """
                ).fetchone()
            )
            r["en"] = json.loads(r["en"])
            print(r)
            return r

    win = webview.create_window("Pinyin Quiz", "../web/cjdict.html", js_api=Api())
    webview.start(lambda: win.evaluate_js("newVocab()"))
