import webview

import json

from cjpy import load_db

db = load_db()


if __name__ == "__main__":

    class Api:
        def log(self, obj):
            print(obj)

        def new_vocab_list(self, count=20):
            rs = []

            for r in db.execute(
                """
                    SELECT
                        simp,
                        REPLACE(GROUP_CONCAT(DISTINCT pinyin), ',', '; ') pinyin,
                        GROUP_CONCAT(DISTINCT trad) trad,
                        json_group_array(english) en
                    FROM cedict
                    WHERE json_extract([data], '$.wordfreq') > 5
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

    win = webview.create_window("Pinyin Quiz", "web/cjdict.html", js_api=Api())
    webview.start(lambda: win.evaluate_js("newVocab()"))
