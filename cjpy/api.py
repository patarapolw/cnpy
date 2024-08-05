import fsrs
from regex import Regex

import json
import random
import datetime
import webbrowser
from pprint import pprint

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
    def log(self, obj):
        pprint(obj, indent=1, sort_dicts=False)

    def open_in_browser(self, url):
        webbrowser.open(url)

    def stats(self):
        stats = make_stats()
        for k, v in stats.items():
            if type(v) is str and len(v) > 50:
                stats[k] = v[:50] + "..."

        return stats

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

        all_items.sort(
            key=lambda r: r.get("srs", {}).get("difficulty", 0), reverse=True
        )
        all_items = all_items[:count]
        # random.shuffle(all_items)

        return {"result": all_items, "count": len(all_items)}

    def new_vocab_list(self, count=20):
        skip_voc = self._get_custom_list(exe_root / "user/skip")

        all_items = [
            dejson_quiz(r)
            for r in db.execute(
                """
                SELECT * FROM quiz
                WHERE srs IS NULL
                AND {}
                ORDER BY json_extract([data], '$.wordfreq') DESC
                LIMIT 1000
                """.format(
                    "v NOT IN ('{}')".format("','".join(skip_voc))
                    if skip_voc
                    else "TRUE"
                ),
            )
        ]

        if len(all_items) > count:
            all_items = random.sample(all_items, k=count)
        else:
            random.shuffle(all_items)

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

            return -len(r["english"])

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
