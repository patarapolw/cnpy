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


if __name__ == "__main__":
    load_db()
