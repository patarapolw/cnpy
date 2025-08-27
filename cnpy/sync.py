import sqlite3
from pathlib import Path

from cnpy.env import env
from cnpy.db import db
from cnpy.dir import user_root, settings_path

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

        CREATE TABLE IF NOT EXISTS ai_cloze (
            v   TEXT NOT NULL,
            arr JSON NOT NULL,
            modified TEXT,
            PRIMARY KEY (v)
        );

        CREATE INDEX IF NOT EXISTS idx_ai_cloze_modified ON ai_cloze (modified);
        """
    )

    if settings_path.exists():
        db.execute(
            "INSERT OR REPLACE INTO settings (k, v) VALUES (?, ?)",
            ("settings", settings_path.read_text("utf-8")),
        )

    for r in db.execute("SELECT * FROM settings"):
        k: str = r["k"]
        if k.startswith(ENV_LOCAL_KEY_PREFIX):
            continue

        sync_db.execute(
            "INSERT OR REPLACE INTO settings (k, v) VALUES (:k, :v)", dict(r)
        )

    for r in db.execute("SELECT * FROM quiz"):
        sync_db.execute(
            """
            INSERT INTO quiz
                (v, srs, [data], modified) VALUES (:v, :srs, :data, :modified)
            ON CONFLICT (v) DO UPDATE SET
                srs = :srs, [data] = :data, modified = :modified
            WHERE v = :v
            AND (
                modified IS NULL OR
                :modified > modified OR
                -- maximize 'srs.last_review'
                json_extract(srs, '$.last_review') IS NULL OR
                json_extract(:srs, '$.last_review') > json_extract(srs, '$.last_review')
            )
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

    for r in db.execute("SELECT * FROM ai_cloze"):
        sync_db.execute(
            """
            INSERT INTO ai_cloze (v, arr, modified) VALUES (:v, :arr, :modified)
            ON CONFLICT (v) DO UPDATE SET
                arr = :arr, modified = :modified
            WHERE v = :v
            AND (
                modified IS NULL OR
                :modified > modified
            )
            """,
            dict(r),
        )

    sync_db.commit()
    print(f"uploaded sync to {sync_db_path}")


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

        if k == "settings":
            settings_path.write_text(r["v"], encoding="utf-8")

    db.execute("DELETE FROM settings WHERE v = ''")

    for r in sync_db.execute("SELECT * FROM quiz"):
        db.execute(
            """
            INSERT INTO quiz
                (v, srs, [data], modified) VALUES (:v,:srs,:data,:modified)
            ON CONFLICT (v) DO UPDATE SET
                srs = :srs, [data] = :data, modified = :modified
            WHERE v = :v
            AND (
                modified IS NULL OR
                :modified > modified OR
                -- maximize 'srs.last_review'
                json_extract(srs, '$.last_review') IS NULL OR
                json_extract(:srs, '$.last_review') > json_extract(srs, '$.last_review')
            )
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
                ORDER BY created
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
                ORDER BY created
                """
            )
        ),
        encoding="utf-8",
    )
    print(f"restored sync from {sync_db_path}")
