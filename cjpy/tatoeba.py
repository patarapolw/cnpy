from regex import Regex
import jieba

import json
from pathlib import Path
from tempfile import mkdtemp
from urllib.request import urlretrieve
import tarfile
import bz2

from cjpy.db import db


def load_db():
    db.executescript(
        """
        DROP TABLE sentence;
        """
    )

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

        db.executescript(
            """
            CREATE UNIQUE INDEX idx_u_cmn ON sentence (cmn);

            CREATE TEMP TABLE eng (
                id      INT NOT NULL PRIMARY KEY,
                eng     TEXT NOT NULL
            );

            CREATE TEMP TABLE links (
                id1     INT,
                id2     INT,
                PRIMARY KEY (id1, id2)
            );
            """
        )

        cmn_ids = set()
        eng_ids = set()

        for ln in (asset_dir / "cmn_sentences.tsv").open("r", encoding="utf8"):
            rs = ln.rstrip().split("\t", 1)
            cmn_ids.add(int(rs[0]))

        for ln in (asset_dir / "eng_sentences.tsv").open("r", encoding="utf8"):
            rs = ln.rstrip().split("\t", 1)
            eng_ids.add(int(rs[0]))

        for ln in (asset_dir / "links.csv").open("r", encoding="utf8"):
            rs = ln.split("\t", 2)

            id1 = int(rs[0])
            id2 = int(rs[1])

            if id1 in cmn_ids and id2 in eng_ids:
                db.execute("INSERT INTO links (id1,id2) VALUES (?,?)", (id1, id2))

        db.commit()

        for ln in (asset_dir / "eng_sentences.tsv").open("r", encoding="utf8"):
            rs = ln.rstrip().split("\t")
            db.execute("INSERT INTO eng (id, eng) VALUES (?,?)", (int(rs[0]), rs[2]))

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
                    SELECT eng FROM eng WHERE id = (
                        SELECT id2 FROM links WHERE id1 = ?
                    )
                ),?)
                ON CONFLICT DO NOTHING
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

        db.executescript(
            """
            DROP TABLE eng;
            DROP TABLE links;
            DROP INDEX idx_u_cmn;
            """
        )

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
    filename = f"{lang}_sentences.tsv"

    if not (unzipdir / filename).exists():
        zipFilename = f"{lang}_sentences.tsv.bz2"
        zipPath = dldir / zipFilename

        urlretrieve(
            f"https://downloads.tatoeba.org/exports/per_language/{lang}/{zipFilename}",
            zipPath,
        )

        with (unzipdir / filename).open("wb") as unzipFile:
            with bz2.open(zipPath) as zipFile:
                unzipFile.write(zipFile.read())


def download_tatoeba_links(dldir: Path, unzipdir: Path):
    filename = "links.csv"

    if not (unzipdir / filename).exists():
        zipFilename = "links.tar.bz2"
        zipPath = dldir / zipFilename

        urlretrieve(
            f"https://downloads.tatoeba.org/exports/{zipFilename}",
            zipPath,
        )

        with tarfile.open(zipPath) as z:
            z.extract(filename, unzipdir)
