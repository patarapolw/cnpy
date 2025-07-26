import sqlite3
import json

from regex import Regex

# Delete words that aren't in the IME
# Or when one of the sentences seem too odd
# New cloze can still be generated in any case
NOT_IN_IME = [
    "畏怯",
    "藉由",
]

re_han = Regex(r"\p{Han}+")

# Deleter container for broken entries
BROKEN_ENTRIES = [
    m.group(0)
    for m in re_han.finditer(
        """
        """
    )
]

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

    is_no = {}

    if v in NOT_IN_IME:
        is_no["IME"] = True

    if v in BROKEN_ENTRIES:
        is_no["proper entry"] = True

    for r in arr:
        q: str = r["question"]
        if not re_han.search(q):
            is_no["Hanzi"] = True
            break

        if "_" not in q:
            if v not in q:
                is_no["v in question"] = True
                break

            is_no_bar = True
            r["question"] = q.replace(v, "__")

    if is_no:
        # dict() or {} with no key, is interpreted by Python as False.
        # at least 1 key is interpreted as True.
        print(v, f"no {",".join(is_no.keys())}")
        db.execute("DELETE FROM ai_cloze WHERE v = ?", (v,))
    elif is_no_bar:
        print(v, "no __")
        db.execute(
            "UPDATE ai_cloze SET arr = ? WHERE v = ?",
            (json.dumps(arr, ensure_ascii=False), v),
        )

db.commit()
