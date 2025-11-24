import sqlite3

from regex import Regex, IGNORECASE
import jieba

from cnpy.dir import user_root, assets_root

db_filename = user_root / "main.db"
db_version: int = 4


db = sqlite3.connect(
    db_filename,
    check_same_thread=False,
    cached_statements=0,
)
db.row_factory = sqlite3.Row


def re(y, x):
    if x:
        return bool(Regex(y, IGNORECASE).fullmatch(x))
    return False


db.create_function("REGEXP", 2, re)

assets_db = sqlite3.connect(
    (assets_root / "assets.db").as_uri() + "?mode=ro",
    check_same_thread=False,
    uri=True,
)
assets_db.row_factory = sqlite3.Row

radical_db = sqlite3.connect(
    (assets_root / "radical.db").as_uri() + "?mode=ro",
    check_same_thread=False,
    uri=True,
)
radical_db.row_factory = sqlite3.Row

jieba.set_dictionary(assets_root / "dict.txt.big")
