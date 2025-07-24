import sqlite3
from pathlib import Path
import json
from pprint import pp
from random import shuffle
import sys

COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 5


db = sqlite3.connect(
    Path("user/main.db").absolute().as_uri() + "?mode=ro",
    uri=True,
)
db.row_factory = sqlite3.Row

batch = [
    {"v": r["v"], "q": json.loads(r["q"])}
    for r in db.execute(
        f"""
        SELECT
            json_each.value q,
            v
        FROM ai_cloze, json_each(arr)
        ORDER BY ai_cloze.ROWID DESC
        LIMIT 1000;
        """
    )
]

shuffle(batch)
batch = batch[:COUNT]

shuffle(batch)
batch = batch[:COUNT]

while batch:
    shuffle(batch)
    to_del = set()

    for i, r in enumerate(batch):
        v1 = input(r["q"]["question"] + " ")
        if v1 == r["v"]:
            print("Correct")
            del batch[i]
        elif v1 in r["q"]["alt"]:
            print(f"Not really: {r['v']}")
        else:
            print(f"Incorrect: {r['v']}")

        print(r["q"]["explanation"])

        if v1 != r["v"]:
            for d in db.execute(
                """
                SELECT * FROM cedict WHERE simp = ?
                """,
                (r["v"],),
            ):
                pp(dict(d))
