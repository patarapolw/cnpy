import fsrs
from regex import Regex

import json
import datetime
import webbrowser
from pprint import pprint
import random

from cnpy.db import db
from cnpy.quiz import load_db_entry as dejson_quiz
from cnpy.cedict import load_db_entry as dejson_cedict
from cnpy.tatoeba import load_db_entry as dejson_sentence
from cnpy.stats import make_stats
from cnpy.dir import exe_root


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

srs = fsrs.FSRS()


class Api:
    def __init__(self, v=""):
        self.v = v

        self.get_stats()

        db.execute(
            """
            DELETE FROM revlog
            WHERE unixepoch('now') - unixepoch(created) > 60*60*24
            """
        )

        now = datetime.datetime.now()
        re_han = Regex(r"^\p{Han}+$")

        vs = set()

        path = exe_root / "user/vocab"
        path.mkdir(exist_ok=True)

        for f in path.glob("**/*.txt"):
            for i, v in enumerate(f.open(encoding="utf-8")):
                v = v.strip()
                if v and re_han.fullmatch(v):
                    rs = list(db.execute("SELECT v FROM vlist WHERE v = ?", (v,)))

                    if not rs:
                        db.execute(
                            "INSERT INTO vlist (v, created) VALUES (?,?)",
                            (
                                v,
                                now.replace(tzinfo=now.astimezone().tzinfo).isoformat(),
                            ),
                        )
                    elif v in vs:
                        print(f"{f.relative_to(path)} [L{i+1}]: {v} duplicated")

                    vs.add(v)

        path = exe_root / "user/skip"
        path.mkdir(exist_ok=True)

        for f in path.glob("**/*.txt"):
            for i, v in enumerate(f.open(encoding="utf-8")):
                v = v.strip()
                if v and re_han.fullmatch(v):
                    if not db.execute(
                        """
                        UPDATE vlist SET
                            skip = 1
                        WHERE v = ?
                        """,
                        (v,),
                    ).rowcount:
                        db.execute(
                            "INSERT INTO vlist (v, created, skip) VALUES (?, ?, 1)",
                            (
                                v,
                                now.replace(tzinfo=now.astimezone().tzinfo).isoformat(),
                            ),
                        )

    def log(self, obj):
        pprint(obj, indent=1, sort_dicts=False)

    def open_in_browser(self, url):
        webbrowser.open(url)

    def get_stats(self):
        self.latest_stats = make_stats()
        for k, v in self.latest_stats.items():
            if type(v) is str and len(v) > 50:
                self.latest_stats[k] = v[:50] + "..."

        return self.latest_stats

    def due_vocab_list(self, limit=20):
        all_items = [
            dejson_quiz(r)
            for r in db.execute(
                """
                WITH vs AS (
                    SELECT v FROM vlist WHERE skip IS NULL
                )
                SELECT * FROM quiz
                WHERE
                (
                    json_extract(srs, '$.due') < date()||'T'||time() OR
                    (
                        json_extract(srs, '$.due') IS NULL
                        AND v IN (
                            SELECT DISTINCT simp FROM cedict WHERE simp IN vs OR trad IN vs
                        )
                    )
                ) AND v NOT IN (
                    SELECT v FROM vlist WHERE skip IS NOT NULL
                )
                """
            )
        ]

        n = len(all_items)

        # random between near difficulty, like [5.0,5.5), [5.5,6.0)
        random.shuffle(all_items)
        all_items.sort(
            key=lambda r: int(r.get("srs", {}).get("difficulty", 0) * 2), reverse=True
        )

        if self.v:
            r0 = None
            rs = []
            for r in all_items:
                if r["v"] == self.v:
                    r0 = r
                else:
                    rs.append(r)

            all_items = rs

            if not r0:
                r0 = dejson_quiz(
                    db.execute("SELECT * FROM quiz WHERE v = ?", (self.v,)).fetchone()
                )
                n += 1

            all_items.insert(0, r0)

            self.v = ""

        return {"result": all_items[:limit], "count": n}

    def new_vocab_list(self, limit=20):
        skip_voc = [
            r["v"] for r in db.execute("SELECT v FROM vlist WHERE skip IS NOT NULL")
        ]

        all_items = [
            dejson_quiz(r)
            for r in db.execute(
                """
                SELECT * FROM quiz
                WHERE srs IS NULL
                AND {}
                AND json_array_length([data], '$.sent') >= 3
                ORDER BY RANDOM()
                LIMIT 1000
                """.format(
                    (
                        "v NOT IN ('{}')".format("','".join(skip_voc))
                        if skip_voc
                        else "TRUE"
                    ),
                ),
            )
        ]

        # zipf freq min is p75 or at least 5
        # max = 7.79, >6 = 101, 5-6 = 1299, 4-5 = 8757
        freq_min = 5
        stats_min = (
            self.latest_stats["p75"] * 0.75 if "p75" in self.latest_stats else None
        )
        if stats_min and stats_min < freq_min:
            freq_min = stats_min

        freq_items = []

        def format_output(f):
            f = f[:limit]
            random.shuffle(f)
            return {"result": f}

        for r in all_items:
            if r["data"]["wordfreq"] > freq_min:
                freq_items.append(r)

                if len(freq_items) >= limit:
                    return format_output(freq_items)

        freq_vs = set(r["v"] for r in freq_items)

        for r in all_items:
            if r["v"] not in freq_vs:
                freq_items.append(r)

                if len(freq_items) >= limit:
                    return format_output(freq_items)

        freq_items.extend(
            dejson_quiz(r)
            for r in db.execute(
                """
                SELECT * FROM quiz
                WHERE srs IS NULL
                AND {}
                AND json_array_length([data], '$.sent') < 3
                AND json_array_length([data], '$.sent') > 0
                LIMIT {}
                """.format(
                    (
                        (
                            "v NOT IN ('{}')".format("','".join(skip_voc))
                            if skip_voc
                            else "TRUE"
                        ),
                        limit,
                    ),
                ),
            )
        )

        if len(freq_items) < limit:
            freq_items.extend(
                dejson_quiz(r)
                for r in db.execute(
                    """
                SELECT * FROM quiz
                WHERE srs IS NULL
                AND {}
                AND json_array_length([data], '$.sent') = 0
                LIMIT {}
                """.format(
                        (
                            "v NOT IN ('{}')".format("','".join(skip_voc))
                            if skip_voc
                            else "TRUE"
                        ),
                        limit,
                    ),
                )
            )

        return format_output(freq_items)

    def vocab_details(self, v: str):
        rs = [
            dejson_cedict(r)
            for r in db.execute("SELECT * FROM cedict WHERE simp = ?", (v,))
        ]

        def sorter(r):
            p0 = r["pinyin"][0]
            if type(p0) is str and p0.isupper():
                return 10

            en = str(r["english"])
            if "used in" in en:
                return 1
            if "variant of" in en:
                return 2

            return -len([en for en in r["english"] if en[0] != "("])

        rs.sort(key=sorter)

        sentences = [
            dejson_sentence(r)
            for r in db.execute(
                """
            SELECT *
            FROM sentence
            WHERE id IN (
                SELECT json_each.value
                FROM quiz, json_each(json_extract([data], '$.sent'))
                WHERE v = ?
            )
            AND eng IS NOT NULL
            AND LENGTH(cmn) < 30
            ORDER BY RANDOM()
            LIMIT 5
            """,
                (v,),
            )
        ]

        if len(sentences) < 3:
            prev_cmn = set(r["cmn"] for r in sentences)

            for r in db.execute(
                """
                SELECT *
                FROM sentence
                WHERE id IN (
                    SELECT json_each.value
                    FROM quiz, json_each(json_extract([data], '$.sent'))
                    WHERE v = ?
                )
                AND {}
                ORDER BY RANDOM()
                LIMIT 5
                """.format(
                    "id NOT IN ({})".format(",".join(str(r["id"]) for r in sentences))
                    if sentences
                    else "TRUE"
                ),
                (v,),
            ):
                r = dejson_sentence(r)
                if r["cmn"] not in prev_cmn:
                    sentences.append(r)

        return {"cedict": rs, "sentences": sentences[:5]}

    def mark(self, v: str, t: str):
        card = fsrs.Card()
        print(v, t)

        prev_srs = None

        for r in db.execute("SELECT srs FROM quiz WHERE v = ? LIMIT 1", (v,)):
            if type(r["srs"]) is str:
                prev_srs = r["srs"]
                card = fsrs.Card.from_dict(json.loads(prev_srs))
                break

        mark = {
            "right": fsrs.Rating.Good,
            "repeat": fsrs.Rating.Hard,
            "wrong": fsrs.Rating.Again,
        }[t]

        card, review_log = srs.review_card(card, mark)

        card_json = json.dumps(card.to_dict())
        if not db.execute(
            "UPDATE quiz SET srs = ? WHERE v = ?",
            (card_json, v),
        ).rowcount:
            db.execute(
                "INSERT INTO quiz (v, srs) VALUES (?, ?)",
                (v, card_json),
            )

        now = datetime.datetime.now()

        db.execute(
            "INSERT INTO revlog (v, prev_srs, mark, created) VALUES (?,?,?,?)",
            (
                v,
                prev_srs,
                int(mark),
                now.replace(tzinfo=now.astimezone().tzinfo).isoformat(),
            ),
        )

        db.commit()

    def save_notes(self, v: str, notes: str):
        if not db.execute(
            """
            UPDATE quiz SET
                [data] = json_set(IFNULL([data], '{}'), '$.notes', ?)
            WHERE v = ?
            """,
            (notes, v),
        ).rowcount:
            db.execute(
                "INSERT INTO quiz (v, [data]) VALUES (?, json_object('notes', ?))",
                (v, notes),
            )

        db.commit()
