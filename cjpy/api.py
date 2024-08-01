from fsrs import *
from regex import Regex

import json
import random
import datetime
from pprint import pprint
from pathlib import Path

from cjpy.db import db

f_srs = FSRS()


class Api:
    def log(self, obj):
        pprint(obj, indent=1)

    def stats(self):
        studied = db.execute(
            """
            SELECT * FROM quiz
            WHERE json_extract(srs, '$.due') IS NOT NULL
            ORDER BY json_extract([data], '$.wordfreq') DESC
            """,
        ).fetchall()

        stats = {"studied": len(studied)}

        for r in studied:
            r = dict(r)

            for k in ("data", "srs"):
                if type(r[k]) is str:
                    r[k] = json.loads(r[k])

            f = r["data"]["wordfreq"]

            # stats.setdefault("upper", f)
            stats["rarest"] = f

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

        return stats

    def due_vocab_list(self, count=20):
        rs = []

        now = datetime.datetime.now(datetime.UTC).isoformat().split(".", 1)[0]
        # self.log(now)

        all_items = list(
            db.execute(
                """
                SELECT * FROM quiz
                WHERE json_extract(srs, '$.due') < ?
                """,
                (now,),
            ).fetchall()
        )

        more_items = []
        re_han = Regex(r"^\p{Han}+$")

        for f in Path("user/vocab").glob("**/*.txt"):
            more_items.extend(
                v
                for v in f.read_text(encoding="utf8").splitlines()
                if re_han.fullmatch(v)
            )

        if more_items:
            stmt = (
                "SELECT DISTINCT simp FROM cedict WHERE simp IN ('"
                + "','".join(set(more_items))
                + "')"
            )

            all_items.extend(
                db.execute(
                    f"""
                    SELECT * FROM quiz
                    WHERE v IN ({stmt}) AND srs IS NULL
                    """
                )
            )

        for r in (
            random.sample(
                all_items,
                k=count,
            )
            if len(all_items) > count
            else random.shuffle(all_items) or all_items
        ):
            r = dict(r)

            for k in ("data", "srs"):
                if type(r[k]) is str:
                    r[k] = json.loads(r[k])

            for k in list(r.keys()):
                if r[k] is None:
                    del r[k]

            rs.append(r)

        return {"result": rs, "count": len(all_items)}

    def new_vocab_list(self, count=20):
        rs = []

        all_items = list(
            db.execute(
                """
                SELECT * FROM quiz
                WHERE srs IS NULL
                ORDER BY json_extract([data], '$.wordfreq') DESC
                LIMIT 1000
                """,
            ).fetchall()
        )

        for r in (
            random.sample(
                all_items,
                k=count,
            )
            if len(all_items) > count
            else random.shuffle(all_items) or all_items
        ):
            r = dict(r)

            for k in ("data", "srs"):
                if type(r[k]) is str:
                    r[k] = json.loads(r[k])

            for k in list(r.keys()):
                if r[k] is None:
                    del r[k]

            rs.append(r)

        return {"result": rs}

    def vocab_details(self, v: str):
        rs = []

        for r in db.execute("SELECT * FROM cedict WHERE simp = ?", (v,)):
            r = dict(r)

            for k in ("data", "english"):
                if type(r[k]) is str:
                    r[k] = json.loads(r[k])

            for k in list(r.keys()):
                if r[k] is None:
                    del r[k]

            rs.append(r)

        return rs

    def mark(self, v: str, t: str):
        card = Card()

        for r in db.execute("SELECT srs FROM quiz WHERE v = ? LIMIT 1", (v,)):
            if type(r["srs"]) is str:
                card = Card.from_dict(json.loads(r["srs"]))
                break

        card, review_log = f_srs.review_card(
            card,
            {"right": Rating.Good, "repeat": Rating.Hard, "wrong": Rating.Again}[t],
        )

        card_json = json.dumps(card.to_dict())
        # self.log(card.to_dict())

        if not db.execute(
            "UPDATE quiz SET srs = ? WHERE v = ?",
            (card_json, v),
        ).rowcount:
            db.execute(
                "INSERT INTO quiz (v, srs) VALUES (?, ?)",
                (v, card_json),
            )

        db.commit()
