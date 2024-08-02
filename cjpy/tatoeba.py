from regex import Regex
import jieba

import json
from pathlib import Path
from tempfile import mkdtemp

from cjpy.db import db


def load_db():
    # db.executescript(
    #     """
    #     DROP TABLE sentence;
    #     """
    # )

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS sentence (
            id      INT NOT NULL PRIMARY KEY,
            cmn     TEXT NOT NULL,
            eng     TEXT,
            [data]  JSON
        );
        """
    )
    populate_db()


def populate_db():
    if not db.execute("SELECT 1 FROM sentence LIMIT 1").fetchall():
        tmp_dir = Path(mkdtemp())
        asset_dir = Path("assets/dic")

        download_tatoeba("cmn", tmp_dir, asset_dir)
        download_tatoeba("eng", tmp_dir, asset_dir)

        download_tatoeba_links(tmp_dir, asset_dir)

        db.execute(
            """
            CREATE TEMP TABLE links (
                id1     INT,
                id2     INT,
                PRIMARY KEY (id1, id2)
            );
            """
        )

        for ln in (asset_dir / "links.csv").open("r", encoding="utf8"):
            rs = ln.split("\t", 2)
            db.execute(
                "INSERT INTO links (id1,id2) VALUES (?,?)", (int(rs[0]), int(rs[1]))
            )

        db.commit()

        for ln in (asset_dir / "eng_sentences.tsv").open("r", encoding="utf8"):
            rs = ln.rstrip().split("\t")
            db.execute(
                "INSERT INTO sentence (id, cmn) VALUES (?,?)", (-int(rs[0]), rs[2])
            )

        db.commit()

        re_en = Regex(r"[A-Za-z]")
        re_han = Regex(r"^\p{Han}+$")

        for ln in (asset_dir / "cmn_sentences.tsv").open("r", encoding="utf8"):
            rs = ln.rstrip().split("\t")

            id1 = rs[0]
            sentence = rs[2]

            if re_en.search(sentence):
                continue

            db.execute(
                """
                INSERT INTO sentence (id, cmn, eng, [data]) VALUES (?,?,(
                    SELECT cmn FROM sentence WHERE id = -(
                        SELECT id2 FROM links WHERE id1 = ?
                    )
                ),?)
                """,
                (
                    id1,
                    sentence,
                    id1,
                    json.dumps(
                        list(
                            set(
                                v
                                for v in jieba.cut_for_search(sentence)
                                if re_han.fullmatch(v)
                            )
                        ),
                        ensure_ascii=False,
                    ),
                ),
            )

        db.commit()

        db.execute("DELETE FROM sentence WHERE id < 0")
        db.execute("DROP TABLE links")

        db.execute(
            """
            WITH a AS (
                SELECT
                    json_each.value v0,
                    json_group_array(DISTINCT sentence.id) ids
                FROM sentence, json_each(sentence.data)
                GROUP BY json_each.value
            )
            UPDATE quiz SET
                [data] = json_set(IFNULL([data], '{}'), '$.sent', json(a.ids))
            FROM a
            WHERE v = a.v0
            """
        )
        db.commit()

        db.execute("UPDATE sentence SET [data] = NULL")
        db.commit()


def download_tatoeba(lang: str, dldir: Path, unzipdir: Path):
    pass


def download_tatoeba_links(dldir: Path, unzipdir: Path):
    pass
