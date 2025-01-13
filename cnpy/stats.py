import json
from collections import Counter
from typing import TypedDict


from cnpy.db import db


Stats = TypedDict(
    "Stats",
    {
        "studied": int,
        "good": int,
        "5.x": int,
        "4.x": int,
        "3.x": int,
        "2.x": int,
        "1.x": int,
        "0.x": int,
        "p75": float,
        "p99": float,
        "lone": str,
        "lone.count": int,
        "h5": str,
        "h5.count": int,
        "h3": str,
        "h3.count": int,
        "accuracy": float,
        "hanzi.count": int,
        "all": str,
    },
    total=False,
)


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

    stats = Stats()

    stats["studied"] = len(studied)
    stats["good"] = len(good)
    stats["all"] = "".join(set("".join(r["v"] for r in studied)))

    if good:
        for r in good:
            f = r["data"]["wordfreq"] or 0

            if f >= 6:
                pass
            elif f >= 5:
                k = "5.x"
                if k in stats:
                    stats[k] += 1
                else:
                    stats[k] = 1
            elif f >= 4:
                k = "4.x"
                if k in stats:
                    stats[k] += 1
                else:
                    stats[k] = 1
            elif f >= 3:
                k = "3.x"
                if k in stats:
                    stats[k] += 1
                else:
                    stats[k] = 1
            elif f >= 2:
                k = "2.x"
                if k in stats:
                    stats[k] += 1
                else:
                    stats[k] = 1
            elif f >= 1:
                k = "1.x"
                if k in stats:
                    stats[k] += 1
                else:
                    stats[k] = 1
            else:
                k = "0.x"
                if k in stats:
                    stats[k] += 1
                else:
                    stats[k] = 1

        def p(arr: list, f: float):
            return arr[int(len(arr) * f)]["data"]["wordfreq"]

        stats["p75"] = p(good, 0.75)
        stats["p99"] = p(good, 0.99)

        if stats["p99"] == stats["p75"]:
            del stats["p99"]

        good.reverse()

        stats["lone"] = "".join(r["v"][0] for r in good if len(set(r["v"])) == 1)

        if stats["lone"]:
            stats["lone.count"] = len(stats["lone"])
        else:
            del stats["lone"]

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

        stats["accuracy"] = stats["good"] / stats["studied"]

        # lone+h3.count remove duplicate
        stats["hanzi.count"] = 0

        if "h3" in stats:
            if "lone" in stats:
                stats["hanzi.count"] = len(set(stats["lone"] + stats["h3"]))
            else:
                stats["hanzi.count"] = len(stats["h3"])
        else:
            if "lone" in stats:
                stats["hanzi.count"] = len(stats["lone"])

    return stats
