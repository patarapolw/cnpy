import sqlite3

from regex import Regex, IGNORECASE

from cnpy.dir import exe_root


db_path = exe_root / "user/main.db"
db_path.parent.mkdir(exist_ok=True)

db = sqlite3.connect(db_path, check_same_thread=False)
db.row_factory = sqlite3.Row


def re(y, x):
    if x:
        return bool(Regex(y, IGNORECASE).fullmatch(x))
    return False


db.create_function("REGEXP", 2, re)

assets_db = sqlite3.connect(exe_root / "assets/assets.db", check_same_thread=False)
assets_db.row_factory = sqlite3.Row
