import sqlite3
from pathlib import Path
import atexit

from cnpy.env import env
from cnpy.db import db
from cnpy.dir import user_root

ENV_LOCAL_KEY_PREFIX = "CNPY_LOCAL_"
ENV_KEY_SYNC = f"{ENV_LOCAL_KEY_PREFIX}SYNC_DATABASE"


def upload_sync():
    sync_db_path = env.get(ENV_KEY_SYNC)
    if not sync_db_path:
        return

    sync_db = sqlite3.connect(sync_db_path)
    sync_db.executescript(
        """
        CREATE TABLE IF NOT EXISTS settings (
            k   TEXT NOT NULL PRIMARY KEY,
            v   TEXT -- or serialized json
        );

        CREATE TABLE IF NOT EXISTS quiz (
            v       TEXT NOT NULL PRIMARY KEY,
            srs     JSON,
            [data]  JSON,
            modified    TEXT -- datetime() output in UTC, e.g. 2025-06-26 04:56:48
        );

        CREATE INDEX IF NOT EXISTS idx_quiz_modified ON quiz (modified);

        DROP TABLE IF EXISTS vlist;
        CREATE TABLE vlist (
            v           TEXT NOT NULL PRIMARY KEY,
            created     TEXT NOT NULL,  -- TIMESTAMP
            skip        INT,            -- boolean
            [data]      JSON
        );
        """
    )

    for r in db.execute("SELECT * FROM settings"):
        k: str = r["k"]
        if k.startswith(ENV_LOCAL_KEY_PREFIX):
            continue

        sync_db.execute(
            "INSERT OR REPLACE INTO settings (k, v) VALUES (:k, :v)", dict(r)
        )

    sync_db.execute("DELETE FROM settings WHERE v = ''")

    for r in db.execute("SELECT * FROM quiz"):
        sync_db.execute(
            """
            INSERT INTO quiz
                (v, srs, [data], modified) VALUES (:v, :srs, :data, :modified)
            ON CONFLICT (v) DO UPDATE SET
                srs = :srs, [data] = :data, modified = :modified
            WHERE v = :v
            AND CASE
                -- "OR" to push all SRS updates
                WHEN modified IS NULL OR :modified IS NULL THEN TRUE
                ELSE :modified > modified
            END
            """,
            dict(r),
        )

    for r in db.execute(
        "SELECT * FROM vlist WHERE json_extract([data],'$.level') IS NULL"
    ):
        sync_db.execute(
            """
            INSERT INTO vlist
                (v, created, skip, [data]) VALUES (:v,:created,:skip,:data)
            """,
            dict(r),
        )

    sync_db.commit()
    print(f"uploaded sync to {sync_db_path}")


atexit.register(upload_sync)


def restore_sync():
    if env.get(f"{ENV_LOCAL_KEY_PREFIX}UPLOAD_ONLY"):
        return

    sync_db_path = env.get(ENV_KEY_SYNC)
    if not sync_db_path or not Path(sync_db_path).exists():
        return

    sync_db = sqlite3.connect(sync_db_path)
    sync_db.row_factory = sqlite3.Row

    for r in sync_db.execute("SELECT * FROM settings"):
        k: str = r["k"]
        if k.startswith(ENV_LOCAL_KEY_PREFIX):
            continue

        db.execute("INSERT OR REPLACE INTO settings (k, v) VALUES (:k, :v)", dict(r))
        env[r["k"]] = r["v"]

    db.execute("DELETE FROM settings WHERE v = ''")

    for r in sync_db.execute("SELECT * FROM quiz"):
        db.execute(
            """
            INSERT INTO quiz
                (v, srs, [data], modified) VALUES (:v,:srs,:data,:modified)
            ON CONFLICT (v) DO UPDATE SET
                srs = :srs, [data] = :data, modified = :modified
            WHERE v = :v
            AND CASE
                -- "OR", restore sync is more proactive, trying to restore more updates like recently quizzed
                WHEN modified IS NULL OR :modified IS NULL THEN TRUE
                ELSE :modified > modified
            END
            """,
            dict(r),
        )

    for r in sync_db.execute("SELECT * FROM vlist"):
        db.execute(
            """
            INSERT OR REPLACE INTO vlist
                (v, created, skip, [data]) VALUES (:v,:created,:skip,:data)
            """,
            dict(r),
        )

    (user_root / "vocab" / "vocab.txt").write_text(
        "\n".join(
            r["v"]
            for r in db.execute(
                """
                SELECT v FROM vlist
                WHERE skip IS NULL
                AND json_extract([data],'$.level') IS NULL
                """
            )
        ),
        encoding="utf-8",
    )

    (user_root / "skip" / "skip.txt").write_text(
        "\n".join(
            r["v"]
            for r in db.execute(
                """
                SELECT v FROM vlist
                WHERE skip IS NOT NULL
                """
            )
        ),
        encoding="utf-8",
    )
    print(f"restored sync from {sync_db_path}")
