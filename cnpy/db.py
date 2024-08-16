import sqlite3

from cnpy.dir import exe_root


db_path = exe_root / "user/main.db"
db_path.parent.mkdir(exist_ok=True)

db = sqlite3.connect(db_path, check_same_thread=False)
db.row_factory = sqlite3.Row
