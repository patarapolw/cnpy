import fsrs
from regex import Regex

import json
import datetime
import webbrowser
from pprint import pprint
import random

from cjpy.db import db
from cjpy.quiz import load_db_entry as dejson_quiz
from cjpy.cedict import load_db_entry as dejson_cedict
from cjpy.tatoeba import load_db_entry as dejson_sentence
from cjpy.stats import make_stats
from cjpy.dir import exe_root


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

srs = fsrs.FSRS()


class Api:
    def __init__(self):
        self.get_stats()

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

    def due_vocab_list(self, count=20):
        now = datetime.datetime.now(datetime.UTC).isoformat()

        skip_voc = self._get_custom_list(exe_root / "user/skip")

        all_items = [
            dejson_quiz(r)
            for r in db.execute(
                """
                SELECT * FROM quiz
                WHERE json_extract(srs, '$.due') < ?
                AND {}
                """.format(
                    "v NOT IN ('{}')".format("','".join(skip_voc))
                    if skip_voc
                    else "TRUE"
                ),
                (now,),
            )
        ]

        more_voc = self._get_custom_list(exe_root / "user/vocab")

        for it in skip_voc:
            if it in more_voc:
                more_voc.remove(it)

        if more_voc:
            all_items.extend(
                dejson_quiz(r)
                for r in db.execute(
                    """
                    SELECT * FROM quiz
                    WHERE v IN (
                        SELECT DISTINCT simp FROM cedict WHERE simp IN ('{}')
                    ) AND srs IS NULL
                    """.format(
                        "','".join(more_voc)
                    )
                )
            )

        n = len(all_items)

        # random between near difficulty, like [5.0,5.5), [5.5,6.0)
        random.shuffle(all_items)
        all_items.sort(
            key=lambda r: int(r.get("srs", {}).get("difficulty", 0) * 2), reverse=True
        )
        all_items = all_items[:count]

        return {"result": all_items, "count": n}

    def new_vocab_list(self, count=20):
        skip_voc = self._get_custom_list(exe_root / "user/skip")

        # zipf freq min is p75 or at least 5
        # max = 7.79, >6 = 101, 5-6 = 1299, 4-5 = 8757
        freq_min = 5
        stats_min = (
            self.latest_stats["p75"] * 0.75 if "p75" in self.latest_stats else None
        )
        if stats_min and stats_min < freq_min:
            freq_min = stats_min

        all_items = [
            dejson_quiz(r)
            for r in db.execute(
                """
                SELECT * FROM quiz
                WHERE srs IS NULL
                AND {}
                AND json_extract([data], '$.wordfreq') > ?
                ORDER BY RANDOM()
                LIMIT {}
                """.format(
                    (
                        "v NOT IN ('{}')".format("','".join(skip_voc))
                        if skip_voc
                        else "TRUE"
                    ),
                    count,
                ),
                (freq_min,),
            )
        ]

        return {"result": all_items}

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
            prev_ids = set(r["id"] for r in sentences)

            for r in db.execute(
                """
            SELECT *
            FROM sentence
            WHERE id IN (
                SELECT json_each.value
                FROM quiz, json_each(json_extract([data], '$.sent'))
                WHERE v = ?
            )
            ORDER BY RANDOM()
            LIMIT 5
            """,
                (v,),
            ):
                r = dejson_sentence(r)
                if r["id"] not in prev_ids:
                    sentences.append(r)

        return {"cedict": rs, "sentences": sentences[:5]}

    def mark(self, v: str, t: str):
        card = fsrs.Card()

        for r in db.execute("SELECT srs FROM quiz WHERE v = ? LIMIT 1", (v,)):
            if type(r["srs"]) is str:
                card = fsrs.Card.from_dict(json.loads(r["srs"]))
                break

        card, review_log = srs.review_card(
            card,
            {
                "right": fsrs.Rating.Good,
                "repeat": fsrs.Rating.Hard,
                "wrong": fsrs.Rating.Again,
            }[t],
        )

        card_json = json.dumps(card.to_dict())

        if not db.execute(
            "UPDATE quiz SET srs = ? WHERE v = ?",
            (card_json, v),
        ).rowcount:
            db.execute(
                "INSERT INTO quiz (v, srs) VALUES (?, ?)",
                (v, card_json),
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

    def _get_custom_list(self, path: "Path") -> set[str]:
        items = []
        re_han = Regex(r"^\p{Han}+$")

        for f in path.glob("**/*.txt"):
            items.extend(
                v
                for v in f.read_text(encoding="utf8").splitlines()
                if re_han.fullmatch(v)
            )

        return set(items)
