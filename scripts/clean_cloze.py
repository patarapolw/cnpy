import sqlite3
import json

db = sqlite3.connect("user/main.db")
db.row_factory = sqlite3.Row

for row in db.execute(
    """
    SELECT v, arr FROM ai_cloze
    """
):
    v = row["v"]
    arr: list[dict] = json.loads(row["arr"])
    is_no_bar = False

    for r in arr:
        q: str = r["question"]
        if "_" not in q:
            is_no_bar = True
            r["question"] = q.replace(v, "__")

    if is_no_bar:
        print(v)
        db.execute(
            "UPDATE ai_cloze SET arr = ? WHERE v = ?",
            (json.dumps(arr, ensure_ascii=False), v),
        )

db.commit()
