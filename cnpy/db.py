import sqlite3

from regex import Regex, IGNORECASE
import jieba

from cnpy.dir import user_root, assets_root


db = sqlite3.connect(user_root / "main.db", check_same_thread=False)
db.row_factory = sqlite3.Row


def re(y, x):
    if x:
        return bool(Regex(y, IGNORECASE).fullmatch(x))
    return False


db.create_function("REGEXP", 2, re)

assets_db = sqlite3.connect(assets_root / "assets.db", check_same_thread=False)
assets_db.row_factory = sqlite3.Row

radical_db = sqlite3.connect(assets_root / "radical.db", check_same_thread=False)
radical_db.row_factory = sqlite3.Row

jieba.set_dictionary(assets_root / "dict.txt.big")
