import json
import random

from pprint import pprint

from cjpy.db import db


class Api:
    def log(self, obj):
        pprint(obj, indent=1)

    def new_vocab_list(self, count=20):
        rs = []

        for r in random.choices(
            db.execute(
                """
            SELECT * FROM quiz
            ORDER BY json_extract([data], '$.wordfreq') DESC
            LIMIT 1000
            """,
            ).fetchall(),
            k=count,
        ):
            r = dict(r)

            for k in ("data", "srs"):
                if type(r[k]) is str:
                    r[k] = json.loads(r[k])

            for k in list(r.keys()):
                if r[k] is None:
                    del r[k]

            rs.append(r)

        return rs

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
