import sqlite3
from pathlib import Path
import json
from pprint import pp


db = sqlite3.connect(
    Path("user/main.db").absolute().as_uri() + "?mode=ro",
    uri=True,
)
db.row_factory = sqlite3.Row

batch = [{}]

while batch:
    batch = [
        {"v": r["v"], "q": json.loads(r["q"])}
        for r in db.execute(
            """
            SELECT
                json_each.value q,
                v
            FROM ai_cloze, json_each(arr)
            ORDER BY RANDOM()
            LIMIT 5;
            """
        )
    ]

    to_del = []

    for i, r in enumerate(batch):
        v1 = input(r["q"]["question"])
        if v1 == r["v"]:
            pp("Correct")
            to_del.append(i)
        elif v1 in r["q"]["alt"]:
            pp(f"Not really: {r['v']}")
        else:
            pp(f"Incorrect: {r['v']}")

        pp(r["q"]["explanation"])

        for d in db.execute(
            """
            SELECT * FROM cedict WHERE simp = ?
            """,
            (r["v"],),
        ):
            pp(dict(d))

    for i in to_del:
        del batch[i]
