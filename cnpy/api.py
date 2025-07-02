import fsrs
from regex import Regex
import jieba
import bottle
import webview

import json
import datetime
import random
from typing import Callable, TypedDict, Any
import threading
import traceback

from cnpy import quiz, cedict, sentence, ai, settings, sync
from cnpy.db import db, radical_db, db_version
from cnpy.stats import make_stats, Stats
from cnpy.tts import tts_audio
from cnpy.dir import assets_root, user_root, web_root, exe_root, settings_path
from cnpy.env import env
from cnpy.sync import ENV_LOCAL_KEY_PREFIX


class UserSettings(TypedDict):
    levels: list[int]


class ServerGlobal:
    web_ready: Callable
    win: webview.Window

    settings = UserSettings(
        levels=[],
    )

    levels: dict[str, list[str]] = {}
    v_quiz: Any = None

    latest_stats: Stats

    is_ai_translation_available = any(
        (env.get("OPENAI_API_KEY"), env.get(f"{ENV_LOCAL_KEY_PREFIX}OLLAMA_MODEL"))
    )


def start():
    quiz.load_db()
    cedict.load_db(print)
    sentence.load_db(print)
    ai.load_db()
    settings.load_db()

    sync.restore_sync()

    db.execute(f"PRAGMA user_version={db_version}")
    g.web_ready()

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


def fn_get_freq_min():
    # zipf freq min is p75 or at least 5
    # max = 7.79, >6 = 101, 5-6 = 1299, 4-5 = 8757
    freq_min = 5
    stats_min = g.latest_stats["p75"] * 0.75 if "p75" in g.latest_stats else None
    if stats_min and stats_min < freq_min:
        freq_min = stats_min

    return freq_min


def fn_save_settings():
    settings_path.write_text(
        json.dumps(
            g.settings,
            ensure_ascii=False,
            indent=2,
        )
    )


srs = fsrs.FSRS()
g = ServerGlobal()
server = bottle.Bottle()

if settings_path.exists():
    g.settings = json.loads(settings_path.read_text("utf-8"))

folder = assets_root / "zhquiz-level"
for f in folder.glob("**/*.txt"):
    g.levels[f.with_suffix("").name] = (
        f.read_text(encoding="utf-8").rstrip().splitlines()
    )


with server:

    @bottle.get("/")
    def index():
        return bottle.static_file("loading.html", root=web_root)

    @bottle.get("/favicon.ico")
    def favicon():
        return None

    @bottle.get("/api/tts/<s>.mp3")
    def tts(s: str):
        g.settings = json.loads(settings_path.read_text("utf-8"))
        p = tts_audio(s)
        if p:
            return bottle.static_file(p.name, root=p.parent)

    @bottle.get("/<filepath:path>")
    def serve_static(filepath):
        return bottle.static_file(filepath, root=web_root)

    @bottle.post("/api/get_settings")
    def get_settings():
        return g.settings

    @bottle.post("/api/sync/setup")
    def set_sync_db():
        file_path = g.win.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=str(exe_root),
            save_filename="cnpy.db",
            file_types=("cnpy SQLite database (*.db)",),
        )
        if file_path:
            file_path = str(file_path)

            db.execute(
                "INSERT OR REPLACE INTO settings (k,v) VALUES (?,?)",
                (sync.ENV_KEY_SYNC, file_path),
            )
            env[sync.ENV_KEY_SYNC] = file_path

            sync.restore_sync()

            return {"db": file_path}

        return {"db": None}

    @bottle.post("/api/sync/restore")
    def sync_restore():
        sync.restore_sync()

    @bottle.post("/api/env/get/<k>")
    def get_env(k: str):
        try:
            for r in db.execute("SELECT v FROM settings WHERE k = ? LIMIT 1", (k,)):
                return {"v": r["v"]}
        except Exception as e:
            traceback.print_exc()
            return {"v": env.get(k)}

        return {"v": None}

    @bottle.post("/api/env/set/<k>")
    def set_env(k: str):
        obj: Any = bottle.request.json
        db.execute("INSERT OR REPLACE INTO settings (k,v) VALUES (?,?)", (k, obj["v"]))
        env[k] = obj["v"]

    ai_translation_response_dict: dict[str, str] = {}
    meaning_quiz_response_dict: dict[str, str] = {}

    @bottle.post("/api/ai_translation/<v>")
    def ai_translation(v: str):
        obj: Any = bottle.request.json
        reset: bool = obj.get("reset", False)
        result_only: bool = obj.get("result_only", False)
        meaning: str | None = obj.get("meaning", None)

        result = ""
        global meaning_quiz_response_dict

        try:
            if meaning:
                reset = True
                result = meaning_quiz_response_dict.get(v, "")
                if result:
                    del meaning_quiz_response_dict[v]
            elif reset:
                db.execute(
                    "INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)", (v, "")
                )
                db.commit()
            elif r := db.execute(
                "SELECT t FROM ai_dict WHERE v = ? LIMIT 1", (v,)
            ).fetchone():
                result: str = r[0]
            elif tr := ai_translation_response_dict.get(v):
                result = tr
                del ai_translation_response_dict[v]
            else:
                # Insert placeholder entry if not exists
                db.execute("INSERT INTO ai_dict (v, t) VALUES (?, ?)", (v, ""))
                db.commit()
                reset = True

            if reset and result_only == False:
                if meaning:
                    result = ""

                def run_async_in_thread(d: dict):
                    try:
                        r = ai.ai_ask(v, meaning=meaning)
                        d[v] = r
                        if r and meaning:
                            try:
                                print(v, json.loads(r[r.index("{") : r.index("}") + 1]))
                            except ValueError:
                                traceback.print_exc()
                                print(v, r)
                    except Exception as e:
                        traceback.print_exc()
                        print(f"AI translation error {v}")

                thread = threading.Thread(
                    target=run_async_in_thread,
                    daemon=(
                        env.get(f"{ENV_LOCAL_KEY_PREFIX}WAIT_FOR_AI_RESULTS") or "1"
                    )
                    == "0",
                    args=(
                        (
                            meaning_quiz_response_dict
                            if meaning
                            else ai_translation_response_dict
                        ),
                    ),
                )
                thread.start()
        except Exception as e:
            print(f"AI translation error {v}: {e}")

        # print(f"{v} -> {result[:5]}...")
        return {"result": result}

    @bottle.post("/api/search")
    def search():
        obj: Any = bottle.request.json

        component: str = obj.get("c")
        voc: str = obj.get("v")
        pinyin: str = obj.get("p")

        if not (voc or component) and not pinyin:
            return {"result": []}

        rs = []
        vs = set()

        if (voc or component) and not pinyin:
            for r in db.execute(
                """
                SELECT
                    v,
                    CASE WHEN unixepoch(json_extract(srs,'$.due')) < unixepoch() + 60*60 THEN '' ELSE
                    (
                        SELECT replace(replace(group_concat(DISTINCT pinyin), ',', '; '), 'u:', 'ü')
                        FROM (
                            SELECT pinyin
                            FROM cedict
                            WHERE simp = v
                            ORDER BY pinyin DESC, lower(pinyin)
                        )
                    ) END pinyin
                FROM quiz
                WHERE v IN (SELECT simp FROM cedict WHERE simp IN (:v,:c) OR trad IN (:v,:c))
                """,
                {"c": component, "v": voc},
            ):
                if r["v"] in vs:
                    continue

                vs.add(r["v"])
                rs.append(dict(r))

        if component:
            sup = component

            for r in radical_db.execute(
                "SELECT sup FROM radical WHERE entry = :rad", {"rad": component}
            ):
                if r["sup"]:
                    sup += r["sup"]

            voc = f'[{"".join(set(sup))}]'
        elif voc:
            voc = f".*{voc}.*"

        obj["v"] = voc

        for r in db.execute(
            f"""
            SELECT
                v,
                CASE WHEN unixepoch(json_extract(srs,'$.due')) < unixepoch() + 60*60 THEN '' ELSE
                (
                    SELECT replace(replace(group_concat(DISTINCT pinyin), ',', '; '), 'u:', 'ü')
                    FROM (
                        SELECT pinyin
                        FROM cedict
                        WHERE simp = v
                        ORDER BY pinyin DESC, lower(pinyin)
                    )
                ) END pinyin
            FROM quiz
            WHERE v IN (
                SELECT simp
                FROM cedict
                WHERE {'pinyin REGEXP :p' if pinyin else 'TRUE'}
                AND {"(simp REGEXP :v OR trad REGEXP :v)" if voc else 'TRUE'}
            )
            ORDER BY
                json_extract(srs, '$.difficulty') DESC,
                json_extract([data], '$.wordfreq') DESC
            LIMIT 55
            """,
            obj,
        ):
            if r["v"] in vs:
                continue

            rs.append(dict(r))

        if len(rs) > 50:
            rs = rs[:50]
            rs.append({"v": "..."})

        return {"result": rs}

    @bottle.post("/api/analyze")
    def analyze():
        json: Any = bottle.request.json
        txt = json["txt"]

        re_han = Regex(r"^\p{Han}+$")
        raw_vs = set(v for v in jieba.cut_for_search(txt) if re_han.fullmatch(v))
        if not raw_vs:
            return {"result": []}

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
                    fn_get_freq_min(),
                )
            )
        ]
        return {"result": rs}

    @bottle.post("/api/update_custom_lists")
    def update_custom_lists():
        now = datetime.datetime.now()
        now_str = now.replace(tzinfo=now.astimezone().tzinfo).isoformat()
        re_han = Regex(r"^\p{Han}+$")

        vs = set()

        path = user_root / "vocab"
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
                        print(f"{f.relative_to(path)} [L{i+1}]: {v} duplicated")
                        is_dup = True
                    else:
                        nodup_f_vs.append(v)

                    vs.add(v)

            if is_dup:
                f.write_text("\n".join(nodup_f_vs), encoding="utf-8")

        levels = g.settings.get("levels", [])
        levels.sort(reverse=True)

        for lv in levels:
            for v in g.levels[f"{lv:02d}"]:
                db.execute(
                    "REPLACE INTO vlist (v, created, [data]) VALUES (?,?, json_object('level',?))",
                    (v, now_str, lv),
                )
                vs.add(v)

        path = user_root / "skip"
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

    @bottle.post("/api/get_stats")
    def get_stats():
        g.latest_stats = make_stats()
        return g.latest_stats

    @bottle.post("/api/set_pinyin/<v>/<t>")
    def set_pinyin(v: str, t):
        obj: Any = bottle.request.json
        pinyin = obj["pinyin"]

        db.execute(
            """
            UPDATE quiz SET
                [data] = json_set(IFNULL([data], '{}'), '$.'||?, json(?))
            WHERE v = ?
            """,
            (t, json.dumps(pinyin), v),
        )

    @bottle.post("/api/due_vocab_list/<review_counter:int>")
    def due_vocab_list(review_counter: int):
        limit = 20

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

        output = {
            "count": n,
            "new": n_new,
            "isAIenabled": g.is_ai_translation_available,
        }

        if g.v_quiz:
            v = g.v_quiz
            g.v_quiz = None

            output["result"] = [v]
            output["customItemSRS"] = v.get("srs")

            return output

        # random between near difficulty, like [5.0,5.5), [5.5,6.0)
        random.shuffle(all_items)
        all_items.sort(
            key=lambda r: int(r.get("srs", {}).get("difficulty", 0) * 2), reverse=True
        )

        result = []
        r_last = []
        max_review = limit * 2 - review_counter
        max_new = int(env.get("CNPY_MAX_NEW") or "10")
        for r in all_items:
            if len(result) >= limit:
                break

            if max_review > 0:
                max_review -= 1
                result.append(r)
            elif max_review + 10 > 0 and max_new > 0 and not r.get("srs"):
                max_new -= 1
                result.append(r)
            else:
                r_last.append(r)

        result.extend(r_last)
        result = result[:limit]
        random.shuffle(result)

        output["result"] = result

        return output

    @bottle.post("/api/get_vocab/<v>")
    def get_vocab(v: str):
        return quiz.load_db_entry(
            db.execute("SELECT * FROM quiz WHERE v = ?", (v,)).fetchone()
        )

    @bottle.post("/api/set_vocab_for_quiz/<v>")
    def set_vocab_for_quiz(v: str):
        g.v_quiz = None

        for r in db.execute("SELECT * FROM quiz WHERE v = ? LIMIT 1", (v,)):
            g.v_quiz = quiz.load_db_entry(r)

        if g.v_quiz is None:
            rs = db.execute(
                "SELECT * FROM quiz WHERE v IN (SELECT simp FROM cedict WHERE trad = ?)",
                (v,),
            ).fetchall()

            if len(rs) == 1:
                g.v_quiz = quiz.load_db_entry(rs[0])

        if g.v_quiz:
            return g.v_quiz

        return {"v": None}

    @bottle.post("/api/new_vocab_list")
    def new_vocab_list():
        limit = 20

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
                    fn_get_freq_min(),
                    limit,
                ),
            )
        ]

        return {"result": all_items}

    @bottle.post("/api/vocab_details/<v>")
    def vocab_details(v: str):
        dict_entries = [
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

        dict_entries.sort(key=sorter)

        sentences = [
            sentence.load_db_entry(r)
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
                r = sentence.load_db_entry(r)
                if r["cmn"] not in prev_cmn:
                    sentences.append(r)

        segments = []
        if len(v) > 2:
            for r in jieba.cut_for_search(v):
                if len(r) > 1 and r != v:
                    segments.append(r)

        return {
            "cedict": dict_entries,
            "sentences": sentences[:5],
            "segments": segments,
        }

    @bottle.post("/api/update_dict")
    def update_dict():
        cedict.reset_db(print)

    @bottle.post("/api/mark/<v>/<t>")
    def mark(v: str, t: str):
        g.v_quiz = None

        card = fsrs.Card()
        print([v, t])

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
            "UPDATE quiz SET srs = ?, modified = datetime() WHERE v = ?",
            (card_json, v),
        ).rowcount:
            db.execute(
                "INSERT INTO quiz (v, srs, modified) VALUES (?, ?, datetime())",
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

    @bottle.post("/api/save_notes/<v>")
    def save_notes(v: str):
        obj: Any = bottle.request.json
        notes = obj["notes"]

        if not db.execute(
            """
            UPDATE quiz SET
                [data] = json_set(IFNULL([data], '{}'), '$.notes', ?),
                modified = datetime()
            WHERE v = ?
            """,
            (notes, v),
        ).rowcount:
            db.execute(
                "INSERT INTO quiz (v, [data], modified) VALUES (?, json_object('notes', ?), datetime())",
                (v, notes),
            )

        db.commit()

    @bottle.post("/api/load_file/<f:path>")
    def load_file(f: str):
        path = user_root / f
        if path.exists():
            return (user_root / f).read_text(encoding="utf-8")
        return ""

    @bottle.post("/api/save_file/<f:path>")
    def save_file(f: str):
        json: Any = bottle.request.json
        txt = json["txt"]

        (user_root / f).write_text(txt, encoding="utf-8")

    @bottle.post("/api/get_levels")
    def get_levels():
        return g.levels

    @bottle.post("/api/set_level/<lv:int>/<t>")
    def set_level(lv: int, t: str):
        lv_set = set(g.settings.get("levels"))
        if t == "remove":
            lv_set.remove(lv)
        else:
            lv_set.add(lv)

        lv_list = list(lv_set)
        lv_list.sort()

        g.settings["levels"] = lv_list

        fn_save_settings()

    @bottle.post("/api/decompose")
    def decompose():
        obj: Any = bottle.request.json
        ks: list[str] = obj["ks"]

        result = {}

        for r in radical_db.execute(
            "SELECT entry, sub FROM radical WHERE entry GLOB '['||?||']'",
            ("".join(ks),),
        ):
            sub = Regex(r"[^\p{L}]").sub("", r["sub"])
            if sub:
                result[r["entry"]] = list(sub)

        return result
