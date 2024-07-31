import sqlite3

db = sqlite3.connect("user/main.db")
db.row_factory = sqlite3.Row
