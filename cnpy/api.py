import fsrs
from regex import Regex
import jieba

import json
import datetime
from pprint import pprint
import random
from typing import Callable, Any, TypedDict, Optional

from cnpy import quiz, cedict, tatoeba
from cnpy.db import db
from cnpy.stats import make_stats
from cnpy.dir import exe_root


srs = fsrs.FSRS()


class UserSettings(TypedDict):
    levels: list[int]


class Api:
    web_log: Callable[[str], None]
    web_ready: Callable
    web_window: Callable[[str, str, Optional[dict]], Any]

    settings_path = exe_root / "user" / "settings.json"
    settings = UserSettings(levels=[])

    levels: dict[str, list[str]] = {}

    def __init__(self, v=""):
        self.v = v

        if self.settings_path.exists():
            self.settings = json.loads(self.settings_path.read_text("utf-8"))

        folder = exe_root / "assets" / "zhquiz-level"
        for f in folder.glob("**/*.txt"):
            self.levels[f.with_suffix("").name] = (
                f.read_text(encoding="utf-8").rstrip().splitlines()
            )

    def get_settings(self):
        return self.settings

    def save_settings(self):
        self.settings_path.write_text(
            json.dumps(
                self.settings,
                ensure_ascii=False,
                indent=2,
            )
        )

    def log(self, obj):
        pprint(obj, indent=1, sort_dicts=False)

    def start(self):
        quiz.load_db()
        cedict.load_db(self.web_log)
        tatoeba.load_db(self.web_log)

        self.web_ready()

        db.execute(
            """
            DELETE FROM revlog
            WHERE unixepoch('now') - unixepoch(created) > 60*60*24
            """
        )

        db.execute(
            """
            UPDATE vlist SET skip = NULL
            """
        )

    def analyze(self, txt: str):
        re_han = Regex(r"^\p{Han}+$")
        raw_vs = set(v for v in jieba.cut_for_search(txt) if re_han.fullmatch(v))
        if not raw_vs:
            return {"result": []}

        r = db.execute(
            """
            UPDATE quiz SET
                [data] = json_set(
                    IFNULL([data], '{}'),
                    '$.count',
                    IFNULL(json_extract([data], '$.count'), 0) + 1
                )
            WHERE
                v IN ('{}') AND
                json_extract([data], '$.wordfreq') < 6
            """.format(
                "{}",
                "','".join(raw_vs),
            )
        )
        db.commit()
        self.log(f"{r.rowcount} vocab counts updated")

        rs = [
            dict(r)
            for r in db.execute(
                """
                SELECT
                    v,
                    (
                        SELECT replace(replace(group_concat(DISTINCT pinyin), ',', '; '), 'u:', 'ü')
                        FROM (
                            SELECT pinyin
                            FROM cedict
                            WHERE simp = v
                            ORDER BY pinyin DESC, lower(pinyin)
                        )
                    ) pinyin
                FROM quiz
                WHERE
                    v IN ('{}') AND
                    v NOT IN (
                        SELECT v FROM vlist
                    ) AND
                    srs IS NULL AND
                    json_extract([data], '$.wordfreq') < 6
                ORDER BY
                    json_extract([data], '$.count') DESC,
                    json_extract([data], '$.wordfreq') > {} DESC,
                    json_array_length([data], '$.sent') > 3 DESC,
                    json_extract([data], '$.wordfreq') DESC,
                    json_array_length([data], '$.sent') > 0 DESC
                """.format(
                    "','".join(raw_vs),
                    self.get_freq_min(),
                )
            )
        ]
        return {"result": rs}

    def update_custom_lists(self):
        now = datetime.datetime.now()
        now_str = now.replace(tzinfo=now.astimezone().tzinfo).isoformat()
        re_han = Regex(r"^\p{Han}+$")

        vs = set()

        path = exe_root / "user/vocab"
        path.mkdir(exist_ok=True)

        for f in path.glob("**/*.txt"):
            nodup_f_vs = []
            is_dup = False

            for i, v in enumerate(f.open(encoding="utf-8")):
                v = v.strip()
                if v and re_han.fullmatch(v):
                    rs = list(db.execute("SELECT v FROM vlist WHERE v = ?", (v,)))

                    if not rs:
                        db.execute(
                            "INSERT INTO vlist (v, created) VALUES (?,?)",
                            (v, now_str),
                        )

                    if v in vs:
                        self.web_log(f"{f.relative_to(path)} [L{i+1}]: {v} duplicated")
                        is_dup = True
                    else:
                        nodup_f_vs.append(v)

                    vs.add(v)

            if is_dup:
                f.write_text("\n".join(nodup_f_vs), encoding="utf-8")

        for lv in self.settings.get("levels", []):
            for v in self.levels[f"{lv:02d}"]:
                db.execute(
                    "INSERT INTO vlist (v, created) VALUES (?,?) ON CONFLICT DO NOTHING",
                    (v, now_str),
                )
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
                            (v, now_str),
                        )
                    vs.add(v)

        db.execute("DELETE FROM vlist WHERE v NOT IN ('{}')".format("','".join(vs)))

    def get_stats(self):
        self.latest_stats = make_stats()
        return self.latest_stats

    def get_vocab(self, v: str):
        for r in db.execute("SELECT * FROM quiz WHERE v = ?", (v,)):
            return quiz.load_db_entry(r)

        return None

    def set_pinyin(self, v: str, pinyin: Optional[list[str]]):
        db.execute(
            """
            UPDATE quiz SET
                [data] = json_set(IFNULL([data], '{}'), '$.pinyin', json(?))
            WHERE v = ?
            """,
            (json.dumps(pinyin), v),
        )

    def due_vocab_list(self, limit=20, review_counter=0):
        all_items = [
            quiz.load_db_entry(r)
            for r in db.execute(
                """
                WITH vs AS (
                    SELECT v FROM vlist WHERE skip IS NULL
                )
                SELECT * FROM quiz
                WHERE
                (
                    json_extract(srs, '$.due') < date()||'T'||time()||'.99' OR
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
        n_new = len([r for r in all_items if not r.get("srs")])

        # random between near difficulty, like [5.0,5.5), [5.5,6.0)
        random.shuffle(all_items)
        all_items.sort(
            key=lambda r: int(r.get("srs", {}).get("difficulty", 0) * 2), reverse=True
        )

        result = []
        r_last = []
        max_review = limit * 2 - review_counter
        max_new = 10
        for r in all_items:
            if len(result) + len(r_last) >= limit:
                break

            if max_review > 0:
                max_review -= 1
                result.append(r)
            elif max_review + limit > 0 and max_new > 0 and not r.get("srs"):
                max_new -= 1
                result.append(r)
            else:
                r_last.append(r)

        result.extend(r_last)
        random.shuffle(result)

        if self.v:
            v0 = None

            for r in result:
                if r["v"] == self.v:
                    v0 = r

            if v0:
                result.remove(v0)
                result.insert(0, v0)
            else:
                v0 = self.get_vocab(self.v)

            if v0:
                result.insert(0, v0)

            self.v = ""

        return {
            "result": result[:limit],
            "count": n,
            "new": n_new,
        }

    def get_freq_min(self):
        # zipf freq min is p75 or at least 5
        # max = 7.79, >6 = 101, 5-6 = 1299, 4-5 = 8757
        freq_min = 5
        stats_min = (
            self.latest_stats["p75"] * 0.75 if "p75" in self.latest_stats else None
        )
        if stats_min and stats_min < freq_min:
            freq_min = stats_min

        return freq_min

    def new_vocab_list(self, limit=20):
        all_items = [
            quiz.load_db_entry(r)
            for r in db.execute(
                """
                SELECT * FROM quiz
                WHERE srs IS NULL
                AND v NOT IN (
                    SELECT v FROM vlist WHERE skip IS NOT NULL
                )
                ORDER BY
                    json_extract([data], '$.count') DESC,
                    json_extract([data], '$.wordfreq') > {} DESC,
                    json_array_length([data], '$.sent') > 3 DESC,
                    json_array_length([data], '$.sent') > 0 DESC,
                    RANDOM()
                LIMIT {}
                """.format(
                    self.get_freq_min(),
                    limit,
                ),
            )
        ]

        return {"result": all_items}

    def vocab_details(self, v: str):
        rs = [
            cedict.load_db_entry(r)
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
            tatoeba.load_db_entry(r)
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
                r = tatoeba.load_db_entry(r)
                if r["cmn"] not in prev_cmn:
                    sentences.append(r)

        return {"cedict": rs, "sentences": sentences[:5]}

    def mark(self, v: str, t: str):
        card = fsrs.Card()
        self.log({v, t})

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

    def new_window(self, url: str, title: str, args: Optional[dict] = None):
        self.web_window(url, title, args)

    def load_file(self, f: str):
        path = exe_root / "user" / f
        if path.exists():
            return (exe_root / "user" / f).read_text(encoding="utf-8")
        return ""

    def save_file(self, f: str, txt: str):
        (exe_root / "user" / f).write_text(txt, encoding="utf-8")

    def get_levels(self):
        return self.levels

    def set_level(self, lv: int, state: bool):
        lv_set = set(self.settings.get("levels"))
        if state:
            lv_set.add(lv)
        else:
            lv_set.remove(lv)

        lv_list = list(lv_set)
        lv_list.sort()

        self.settings["levels"] = lv_list
        self.save_settings()
