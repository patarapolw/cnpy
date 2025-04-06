from wordfreq import zipf_frequency
from regex import Regex
import jieba

import sqlite3
from urllib.request import urlretrieve
from zipfile import ZipFile
import tarfile
import bz2
import json

from cnpy.dir import tmp_root, assets_root

jieba.set_dictionary(assets_root / "dict.txt.big")

db = sqlite3.connect("assets/assets.db")


def dump_cedict_and_wordfreq(forced=False):
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS wordfreq (
            v   TEXT NOT NULL PRIMARY KEY,
            f   FLOAT
        );
        """
    )

    filename = "cedict_ts.u8"
    cedict = assets_root / filename

    if forced or not cedict.exists():
        zipPath = tmp_root / "cedict.zip"

        url = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip"
        print("Downloading {} from {}".format(filename, url))
        urlretrieve(url, zipPath)

        with ZipFile(zipPath) as z:
            z.extract(cedict.name, path=cedict.parent)

    re_han = Regex(r"^\p{Han}+$")

    for ln in cedict.open("r", encoding="utf8"):
        if ln[0] == "#":
            continue

        trad, simp, _ = ln.split(" ", 2)

        for v in [trad, simp]:
            if not re_han.fullmatch(v):
                continue

            db.execute(
                "INSERT INTO wordfreq (v, f) VALUES (?,?) ON CONFLICT DO NOTHING",
                (v, zipf_frequency(v, "zh")),
            )

    db.commit()

    print("Done")


def dump_tatoeba():
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS tatoeba (
            id      INT NOT NULL PRIMARY KEY,
            cmn     TEXT NOT NULL,
            eng     TEXT,
            voc     JSON,
            f       FLOAT
        );

        CREATE INDEX IF NOT EXISTS idx_tatoeba_f ON tatoeba (f);
        """
    )

    if not db.execute("SELECT 1 FROM tatoeba LIMIT 1").fetchall():
        _download_tatoeba("cmn")
        _download_tatoeba("eng")

        _download_tatoeba_links()

        print("Building sentence dictionary...")

        db.executescript(
            """
            CREATE UNIQUE INDEX idx_u_cmn ON tatoeba (cmn);

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

        for ln in (tmp_root / "cmn_sentences.tsv").open("r", encoding="utf8"):
            rs = ln.rstrip().split("\t", 1)
            cmn_ids.add(int(rs[0]))

        for ln in (tmp_root / "eng_sentences.tsv").open("r", encoding="utf8"):
            rs = ln.rstrip().split("\t", 1)
            eng_ids.add(int(rs[0]))

        for ln in (tmp_root / "links.csv").open("r", encoding="utf8"):
            rs = ln.split("\t", 2)

            id1 = int(rs[0])
            id2 = int(rs[1])

            if id1 in cmn_ids and id2 in eng_ids:
                db.execute("INSERT INTO links (id1,id2) VALUES (?,?)", (id1, id2))

        db.commit()

        for ln in (tmp_root / "eng_sentences.tsv").open("r", encoding="utf8"):
            rs = ln.rstrip().split("\t")
            db.execute("INSERT INTO eng (id, eng) VALUES (?,?)", (int(rs[0]), rs[2]))

        db.commit()

        re_en = Regex(r"[A-Za-z]")
        re_han = Regex(r"^\p{Han}+$")

        for ln in (tmp_root / "cmn_sentences.tsv").open("r", encoding="utf8"):
            rs = ln.rstrip().split("\t")

            id1 = rs[0]
            sentence = rs[2]

            if re_en.search(sentence):
                continue

            f = 0
            voc = set()
            for v in jieba.cut_for_search(sentence):
                if re_han.fullmatch(v):
                    if v not in voc:
                        voc.add(v)
                        f += zipf_frequency(v, "zh")

            db.execute(
                """
                INSERT INTO tatoeba (id, cmn, eng, voc, f) VALUES (?,?,(
                    SELECT eng FROM eng WHERE id = (
                        SELECT id2 FROM links WHERE id1 = ?
                    )
                ),?,?)
                ON CONFLICT DO NOTHING
                """,
                (
                    id1,
                    sentence,
                    id1,
                    json.dumps(list(voc), ensure_ascii=False),
                    f,
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

        print("Done")


def _download_tatoeba(lang: str):
    filename = f"{lang}_sentences.tsv"

    if not (tmp_root / filename).exists():
        zipFilename = f"{lang}_sentences.tsv.bz2"
        zipPath = tmp_root / zipFilename

        url = f"https://downloads.tatoeba.org/exports/per_language/{lang}/{zipFilename}"
        print("Downloading {} from {}".format(filename, url))
        urlretrieve(url, zipPath)

        with (tmp_root / filename).open("wb") as unzipFile:
            with bz2.open(zipPath) as zipFile:
                unzipFile.write(zipFile.read())


def _download_tatoeba_links():
    filename = "links.csv"

    if not (tmp_root / filename).exists():
        zipFilename = "links.tar.bz2"
        zipPath = tmp_root / zipFilename

        url = f"https://downloads.tatoeba.org/exports/{zipFilename}"
        print("Downloading {} from {}".format(filename, url))
        urlretrieve(url, zipPath)

        with tarfile.open(zipPath) as z:
            z.extract(filename, tmp_root)


if __name__ == "__main__":
    dump_cedict_and_wordfreq()
    dump_tatoeba()

    db.commit()
