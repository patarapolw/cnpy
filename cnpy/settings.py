from cnpy.db import db
from cnpy.dir import settings_path
from cnpy.env import env


def load_db():
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS settings (
            k   TEXT NOT NULL PRIMARY KEY,
            v   TEXT -- or serialized json
        );
        """
    )
    populate_db()


def populate_db():
    for k, v in env.items():
        db.execute("INSERT OR REPLACE INTO settings (k, v) VALUES (?, ?)", (k, v))

    db.execute(
        "INSERT OR REPLACE INTO settings (k, v) VALUES (?, ?)",
        ("settings", settings_path.read_text("utf-8")),
    )
    db.commit()

    for r in db.execute("SELECT k, v FROM settings WHERE k != 'settings'"):
        env[r["k"]] = r["v"]


def reset_db():
    load_db()


if __name__ == "__main__":
    reset_db()
