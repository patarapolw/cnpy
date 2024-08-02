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


def populate_db():
    pass
