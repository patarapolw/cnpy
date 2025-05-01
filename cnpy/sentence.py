from typing import Callable

from cnpy.db import db, assets_db


def load_db(web_log: Callable[[str], None] = print):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS sentence (
            id      INT NOT NULL PRIMARY KEY,
            cmn     TEXT NOT NULL,
            eng     TEXT,
            [data]  JSON
        );

        CREATE INDEX IF NOT EXISTS idx_sentence_cmn_length ON sentence (LENGTH(cmn));
        CREATE INDEX IF NOT EXISTS idx_quiz_sent ON quiz (json_array_length([data], '$.sent'));
        """
    )
    populate_db(web_log)


def load_db_entry(r):
    return dict(r)


def populate_db(web_log: Callable[[str], None] = print):
    if not db.execute("SELECT 1 FROM sentence LIMIT 1").fetchall():
        web_log("Building sentence corpus...")

        for r in assets_db.execute(
            "SELECT id, cmn, eng, voc FROM tatoeba ORDER BY f DESC"
        ):
            db.execute(
                "INSERT INTO sentence (id, cmn, eng, [data]) VALUES (?,?,?,?)",
                (r["id"], r["cmn"], r["eng"], r["voc"]),
            )
        db.commit()

        db.execute(
            """
            WITH a AS (
                SELECT
                    json_each.value v0,
                    json_group_array(DISTINCT sentence.id) ids
                FROM sentence, json_each(sentence.data)
                GROUP BY json_each.value
            )
            UPDATE quiz SET
                [data] = json_set(IFNULL([data], '{}'), '$.sent', json(a.ids))
            FROM a
            WHERE v = a.v0 OR v IN (SELECT simp FROM cedict WHERE trad = a.v0)
            """
        )

        db.execute("UPDATE sentence SET [data] = NULL")
        db.commit()

        web_log("Done")


def reset_db():
    db.executescript(
        """
        DROP TABLE sentence;
        """
    )

    load_db()


if __name__ == "__main__":
    reset_db()
