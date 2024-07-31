import webview

import json

from cjpy import load_db

db = load_db()


if __name__ == "__main__":

    class Api:
        def __init__(self, where="TRUE") -> None:
            self.where = where

        def log(self, obj):
            print(obj)

        def total_vocab(self):
            return len(
                db.execute(
                    f"SELECT 1 FROM cedict WHERE {self.where} GROUP BY simp"
                ).fetchall()
            )

        def new_vocab_list(self, count=20):
            rs = []

            for r in db.execute(
                f"""
                    SELECT
                        simp,
                        REPLACE(GROUP_CONCAT(DISTINCT pinyin), ',', '; ') pinyin,
                        GROUP_CONCAT(DISTINCT trad) trad,
                        json_group_array(english) en
                    FROM cedict
                    WHERE {self.where}
                    GROUP BY simp
                    ORDER BY RANDOM() LIMIT ?
                    """,
                (count,),
            ):
                r = dict(r)
                r["en"] = json.loads(r["en"])
                rs.append(r)

            return rs

        def new_vocab(self):
            return self.new_vocab_list(1)[0]

    win = webview.create_window(
        "Pinyin Quiz",
        "web/cjdict.html",
        js_api=Api("json_extract([data], '$.wordfreq') > 6"),
    )
    webview.start(lambda: win.evaluate_js("newVocab()"))
