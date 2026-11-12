import json
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEVELS_ROOT = ROOT / "assets" / "zhquiz-level"
DATABASE = ROOT / "user" / "main.db"
OUTPUT = ROOT / "docs" / "levels"


def hsk_for_level(level: int) -> int:
    if level <= 5:
        return 1
    if level <= 10:
        return 2
    if level > 40:
        return 6
    return (level - 1) // 10 + 2


def dictionary_key(word: str) -> str:
    return re.split(r"[（(]", word, maxsplit=1)[0].strip()


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def markdown_cell(value: str) -> str:
    return value.replace("|", r"\|").replace("\r", " ").replace("\n", " ")


def load_level_lists() -> dict[int, list[str]]:
    levels: dict[int, list[str]] = {}
    for path in LEVELS_ROOT.glob("**/*.txt"):
        level = int(path.stem)
        if level in levels:
            raise ValueError(f"Duplicate vocabulary file for level {level}")
        levels[level] = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    expected = set(range(1, 61))
    if set(levels) != expected:
        missing = sorted(expected - set(levels))
        extra = sorted(set(levels) - expected)
        raise ValueError(f"Expected levels 1-60; missing={missing}, extra={extra}")
    return levels


def load_dictionary(
    words: set[str],
) -> dict[str, list[tuple[str, str | None, str, list[str]]]]:
    if not DATABASE.is_file():
        raise FileNotFoundError(f"Dictionary database not found: {DATABASE}")

    database_uri = f"{DATABASE.as_uri()}?mode=ro"
    dictionary: dict[str, list[tuple[str, str | None, str, list[str]]]] = {}
    with sqlite3.connect(database_uri, uri=True) as connection:
        ordered_words = sorted(words)
        for offset in range(0, len(ordered_words), 500):
            batch = ordered_words[offset : offset + 500]
            placeholders = ",".join("?" for _ in batch)
            rows = connection.execute(
                f"SELECT simp, trad, pinyin, english FROM cedict WHERE simp IN ({placeholders})",
                batch,
            )
            for word, traditional, pinyin, english_json in rows:
                meanings = [
                    meaning
                    for group in json.loads(english_json)
                    for meaning in group
                    if meaning
                ]
                dictionary.setdefault(word, []).append(
                    (word, traditional, pinyin, meanings)
                )
    return dictionary


def load_sentences(
    words: set[str],
) -> dict[str, list[tuple[str, str]]]:
    if not DATABASE.is_file():
        raise FileNotFoundError(f"Sentence database not found: {DATABASE}")

    database_uri = f"{DATABASE.as_uri()}?mode=ro"
    sentence_ids: dict[str, list[int]] = {}
    with sqlite3.connect(database_uri, uri=True) as connection:
        ordered_words = sorted(words)
        for offset in range(0, len(ordered_words), 500):
            batch = ordered_words[offset : offset + 500]
            placeholders = ",".join("?" for _ in batch)
            rows = connection.execute(
                f"""
                SELECT v, json_extract(data, '$.sent')
                FROM quiz
                WHERE v IN ({placeholders})
                """,
                batch,
            )
            for word, sent_json in rows:
                if sent_json:
                    sentence_ids[word] = json.loads(sent_json)

        sentence_rows: dict[int, tuple[str, str | None]] = {}
        all_ids = sorted({sent_id for ids in sentence_ids.values() for sent_id in ids})
        for offset in range(0, len(all_ids), 500):
            batch = all_ids[offset : offset + 500]
            placeholders = ",".join("?" for _ in batch)
            rows = connection.execute(
                f"SELECT id, cmn, eng FROM sentence WHERE id IN ({placeholders})",
                batch,
            )
            sentence_rows.update(
                (sent_id, (cmn, eng)) for sent_id, cmn, eng in rows
            )

    return {
        word: [
            sentence_rows[sent_id]
            for sent_id in ids
            if sent_id in sentence_rows
        ]
        for word, ids in sentence_ids.items()
    }


def marked_example(
    word: str,
    traditional: str | None,
    sentences: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    forms = [word]
    if traditional and traditional != word:
        forms.append(traditional)

    candidates = []
    for chinese, english in sentences:
        if not english or len(chinese) > 240 or len(english) > 400:
            continue
        form = next((form for form in forms if form in chinese), None)
        if form:
            marked = chinese.replace(form, f"**{form}**", 1)
            candidates.append((forms.index(form), len(chinese), marked, english))

    candidates.sort()
    return [(chinese, english) for _, _, chinese, english in candidates[:2]]


def render_level(
    level: int,
    words: list[str],
    dictionary: dict[str, list[tuple[str, str | None, str, list[str]]]],
    sentences: dict[str, list[tuple[str, str]]],
) -> str:
    rows = ["---", "target: zh-CN", "vocabulary:", "  words:"]
    vocabulary_table = [
        "## Vocabulary",
        "",
        "| Vocabulary | Pinyin | Definitions |",
        "| --- | --- | --- |",
    ]

    for word in words:
        key = dictionary_key(word)
        matches = dictionary.get(key, [])
        pinyin = list(dict.fromkeys(entry[2] for entry in matches))
        traditional = next(
            (entry[1] for entry in matches if entry[1] and entry[1] != key),
            None,
        )
        meanings = list(
            dict.fromkeys(meaning for entry in matches for meaning in entry[3])
        )
        label = re.search(r"[（(](.*?)[）)]", word)

        rows.extend(
            [
                f"    - zh: {yaml_string(key)}",
                f"      en: {yaml_string('; '.join(meanings[:8]) or 'No CC-CEDICT definition found.')}",
            ]
        )
        examples = marked_example(key, traditional, sentences.get(key, []))
        if examples:
            rows.append("      examples:")
            for chinese, english in examples:
                rows.extend(
                    [
                        f"        - zh: {yaml_string(chinese)}",
                        f"          en: {yaml_string(english)}",
                    ]
                )
        shown_meanings = "; ".join(meanings[:8]) or "No CC-CEDICT definition found."
        vocabulary_table.append(
            "| "
            + " | ".join(
                markdown_cell(value)
                for value in (key, "; ".join(pinyin[:5]) or "—", shown_meanings)
            )
            + " |"
        )
        if pinyin:
            rows.append(f"      pinyin: {yaml_string('; '.join(pinyin[:5]))}")
        if traditional:
            rows.append(f"      traditional: {yaml_string(traditional)}")
        if label:
            rows.append(f"      notes: {yaml_string('ZhQuiz label: ' + label.group(1))}")

    rows.extend(["---", "", f"# Level {level}", ""])
    rows.extend(vocabulary_table)

    next_prev = []
    if level > 1:
        previous_hsk = hsk_for_level(level - 1)
        next_prev.append(
            f"[Previous level](/levels/hsk-{previous_hsk}/level-{level - 1})"
        )
    next_prev.append("[All vocabulary levels](/levels/)")
    if level < 60:
        next_hsk = hsk_for_level(level + 1)
        next_prev.append(f"[Next level](/levels/hsk-{next_hsk}/level-{level + 1})")

    rows.extend(
        [
            f"HSK {hsk_for_level(level)} · {len(words)} vocabulary entries",
            "",
            " · ".join(next_prev),
            "",
        ]
    )
    return "\n".join(rows)


def render_hsk_index(hsk: int, levels: list[int]) -> str:
    rows = [f"# HSK {hsk}", ""]
    rows.extend(f"- [Level {level}](./level-{level})" for level in levels)
    rows.append("")
    return "\n".join(rows)


def main() -> None:
    levels = load_level_lists()
    dictionary_words = {
        dictionary_key(word) for words in levels.values() for word in words
    }
    dictionary = load_dictionary(dictionary_words)
    sentences = load_sentences(dictionary_words)
    groups: dict[int, list[int]] = {}

    for level, words in levels.items():
        hsk = hsk_for_level(level)
        groups.setdefault(hsk, []).append(level)
        hsk_directory = OUTPUT / f"hsk-{hsk}"
        hsk_directory.mkdir(parents=True, exist_ok=True)
        output_path = hsk_directory / f"level-{level}.md"
        output_path.write_text(
            render_level(level, words, dictionary, sentences),
            encoding="utf-8",
            newline="\n",
        )

    for hsk, hsk_levels in groups.items():
        (OUTPUT / f"hsk-{hsk}" / "index.md").write_text(
            render_hsk_index(hsk, hsk_levels),
            encoding="utf-8",
            newline="\n",
        )

    for old_page in OUTPUT.glob("[0-9][0-9].md"):
        old_page.unlink()

    print(f"Generated {len(levels)} vocabulary lessons in {OUTPUT}")


if __name__ == "__main__":
    main()
