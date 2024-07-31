import webview

import json

from cjpy import load_db

db = load_db()


if __name__ == "__main__":

    class Api:
        def new_vocab(self):
            r = dict(
                db.execute(
                    """
                    SELECT
                        simp,
                        REPLACE(GROUP_CONCAT(DISTINCT pinyin), ',', '; ') pinyin,
                        json_group_array(english) en
                    FROM cedict
                    WHERE json_extract([data], '$.wordfreq') > 5
                    GROUP BY simp
                    ORDER BY RANDOM() LIMIT 1
                    """
                ).fetchone()
            )
            r["en"] = json.loads(r["en"])
            print(r)
            return r

    win = webview.create_window("Pinyin Quiz", "web/cjdict.html", js_api=Api())
    webview.start(lambda: win.evaluate_js("newVocab()"))
