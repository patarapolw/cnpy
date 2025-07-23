import sqlite3
from pathlib import Path
import json
from pprint import pp
from random import shuffle

COUNT = 3


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
        ORDER BY RANDOM()
        LIMIT {COUNT};
        """
    )
]

while batch:
    shuffle(batch)
    to_del = set()

    for r in batch:
        v1 = input(r["q"]["question"])
        if v1 == r["v"]:
            print("Correct")
            to_del.add(r["v"])
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

    batch = [r for r in batch if r["v"] not in to_del]
