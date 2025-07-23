import sqlite3
import json

from regex import Regex

# Delete words that aren't in the IME
# Or when one of the sentences seem too odd
# New cloze can still be generated in any case
TO_DELETE = {
    "畏怯",
}

db = sqlite3.connect("user/main.db")
db.row_factory = sqlite3.Row

re_han = Regex(r"\p{Han}")

for row in db.execute(
    """
    SELECT v, arr FROM ai_cloze
    """
):
    v = row["v"]
    arr: list[dict] = json.loads(row["arr"])
    is_no_bar = False
    is_no_chinese = False

    if v in TO_DELETE:
        is_no_chinese = True

    for r in arr:
        q: str = r["question"]
        if not re_han.search(q):
            is_no_chinese = True
            break

        if "_" not in q:
            is_no_bar = True
            r["question"] = q.replace(v, "__")

    if is_no_chinese:
        print(v, "no chinese")
        db.execute("DELETE FROM ai_cloze WHERE v = ?", (v,))
    elif is_no_bar:
        print(v, "no __")
        db.execute(
            "UPDATE ai_cloze SET arr = ? WHERE v = ?",
            (json.dumps(arr, ensure_ascii=False), v),
        )

db.commit()
