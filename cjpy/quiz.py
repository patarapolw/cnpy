import json

from cjpy.db import db


def load_db():
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS quiz (
            v       TEXT NOT NULL PRIMARY KEY,
            srs     JSON,
            [data]  JSON
        );

        CREATE INDEX IF NOT EXISTS idx_quiz_srs_due ON quiz (json_extract(srs, '$.due'));
        CREATE INDEX IF NOT EXISTS idx_quiz_wordfreq ON quiz (json_extract([data], '$.wordfreq'));
        """
    )

    populate_db()


def load_db_entry(r):
    r = dict(r)

    for k in ("data", "srs"):
        if type(r[k]) is str:
            r[k] = json.loads(r[k])

    for k in list(r.keys()):
        if r[k] is None:
            del r[k]

    return r


def populate_db():
    pass
