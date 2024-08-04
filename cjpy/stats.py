import json
from collections import Counter
from typing import Any


from cjpy.db import db


def make_stats():
    # New and 1x correct Card difficulty is 5.1
    max_difficulty = 6

    def de_json(r):
        r = dict(r)

        for k in ("data", "srs"):
            if type(r[k]) is str:
                r[k] = json.loads(r[k])

        return r

    studied = [
        de_json(r)
        for r in db.execute(
            """
        SELECT * FROM quiz
        WHERE json_extract(srs, '$.due') IS NOT NULL
        ORDER BY json_extract([data], '$.wordfreq') DESC
        """
        )
    ]

    good = [r for r in studied if r["srs"]["difficulty"] < max_difficulty]

    stats: dict[str, Any] = {"studied": len(studied), "good": len(good)}

    for r in good:
        f = r["data"]["wordfreq"]

        if f >= 6:
            pass
        elif f >= 5:
            k = "5.x"
            stats[k] = stats.setdefault(k, 0) + 1
        elif f >= 4:
            k = "4.x"
            stats[k] = stats.setdefault(k, 0) + 1
        elif f >= 3:
            k = "3.x"
            stats[k] = stats.setdefault(k, 0) + 1
        elif f >= 2:
            k = "2.x"
            stats[k] = stats.setdefault(k, 0) + 1
        elif f >= 1:
            k = "1.x"
            stats[k] = stats.setdefault(k, 0) + 1
        else:
            k = "0.x"
            stats[k] = stats.setdefault(k, 0) + 1

    def p(arr: list, f: float):
        return arr[int(len(arr) * f)]["data"]["wordfreq"]

    stats["p75"] = p(good, 0.75)
    stats["p99"] = p(good, 0.99)

    good.reverse()

    stats["lone"] = "".join(r["v"] for r in good if len(r["v"]) == 1)
    stats["lone.count"] = len(stats["lone"])

    for i, (c, count) in enumerate(
        Counter("".join("".join(set(r["v"])) for r in good)).most_common()
    ):
        if count < 3:
            break

        i += 1

        stats["h3"] = stats.get("h3", "") + c
        stats["h3.count"] = i

        if count >= 5:
            stats["h5"] = stats.get("h5", "") + c
            stats["h5.count"] = i

    return stats
