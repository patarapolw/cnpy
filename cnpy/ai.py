import json
import threading
from typing import Generator

from openai import OpenAI
from regex import Regex
from json_repair import repair_json

from cnpy.db import db
from cnpy.env import env
from cnpy.sync import ENV_LOCAL_KEY_PREFIX

db_lock = threading.Lock()


def get_local_model():
    return env.get(f"{ENV_LOCAL_KEY_PREFIX}OLLAMA_MODEL") or ""


def get_can_local():
    return bool(get_local_model())


def get_online_model():
    return env.get("OPENAI_MODEL") or "deepseek-chat"


def get_can_online():
    return bool(env.get("OPENAI_API_KEY") or "")


Q_TRANSLATION_SYSTEM = """
你是一个中文参考工具，提供词语的词典释义、百科知识、口语及方言用法，并附带拼音和注音（注音符号）。
若词语存在多音字，请按不同读音分别列出释义。
所有翻译和例句中，禁止使用拼音或英文解释。
""".strip()
Q_TRANSLATION = '"{v}"是什么？'

Q_MEANING_ROLE = """
You are an AI language expert specializing in modern Mandarin Chinese linguistics.
Your task is to evaluate whether a provided meaning accurately matches a given Chinese word.
Also consider possibility that the provided meaning is a typo.

* If the meaning is **clearly correct**, return `"correct": true`.
* If the meaning is **clearly wrong**, return `"correct": false`.
* If the meaning is **ambiguous, partially correct, or depends on context**, return `"correct": null`.

Then, explain why the meaning is correct, incorrect, or partially accurate.
Include the Pinyin(s) of the given Chinese word in the given meaning context.
If there multiple possible Pinyins, explain why.
Include nuances and common uses.
""".strip()

Q_MEANING = f"""
{Q_MEANING_ROLE}

* Always output fields in order: correct, explanation.

Respond in this JSON format:

```json
{{
  "correct": true | false | null,
  "explanation": "..."
}}
```
""".strip()

Q_MEANING_WITH_CLOZE = f"""
{Q_MEANING_ROLE}

Regardless of correctness, generate at least one cloze test sentence per distinct usage sense of the word.
Make **sufficient number of** cloze test sentences to cover **all** distinct usage senses of the word, as well as homographs bearing the same Hanzi.

* The blank should be best filled by the Chinese headword.
* The headword **must** be the same as the original Chinese word.
* Provide 2–3 plausible but incorrect alternatives for each. Alternatives are different from each other and from the headword.
* Explain why the headword is the most appropriate choice among the options.
* Reading and meaning **must not be included** inside the cloze questions and cloze alts.
* Always output fields in order: correct, explanation, cloze.

Respond in this JSON format:

```json
{{
  "correct": true | false | null,
  "explanation": "...",
  "cloze": [
    {{
      "question": "...",
      "headword": "...",
      "alt": ["...", "...", "..."],
      "explanation": "..."
    }}
  ]
}}
```
""".strip()


def stream_ai_ask(
    q_system: str, q_user: str, largest_model: bool
) -> Generator[str, None, None]:
    """
    Generator to respond to a question using LLM.

    Notes:
        - This function requires `OPENAI_API_KEY` to be set in the environment.
          Get one from https://platform.deepseek.com or https://platform.openai.com.

    See Also:
        - https://api-docs.deepseek.com to use DeepSeek with OpenAI API.
        - https://platform.openai.com/docs/models to use OpenAI models (e.g. GPT-4.1).
          Set `OPENAI_BASE_URL` to `https://api.openai.com/v1` in the `.env` file and set `OPENAI_MODEL` as appropriate.

    Args:
        q_system (str): The string defining system role.
        q_user (str): The string to ask.

    Returns:
        str | None: The answered string, or None if fails.
    """
    model = get_online_model() if largest_model else ""

    base_url = "https://api.openai.com/v1"
    if model.startswith("deepseek-"):
        base_url = "https://api.deepseek.com"
    elif model.startswith("gemini-") or model.startswith("gemma-"):
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

    base_url = (
        (env.get("OPENAI_BASE_URL") or base_url)
        if largest_model
        # Use environment variable CNPY_LOCAL_OLLAMA_HOST
        else env.get(f"{ENV_LOCAL_KEY_PREFIX}OLLAMA_HOST")
    )

    openai_client = OpenAI(
        base_url=base_url,
        api_key=env.get("OPENAI_API_KEY") if largest_model else None,
    )

    temperature = env.get("OPENAI_TEMPERATURE")
    if not temperature and model == "deepseek-chat":
        temperature = "1.3"
    if not largest_model:
        temperature = None

    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            (
                {"role": "user", "content": q_system}
                if model.startswith("gemma-")
                else {"role": "system", "content": q_system}
            ),
            {"role": "user", "content": q_user},
        ],
        temperature=float(
            temperature or "1"
        ),  # Adjust temperature according to documentation
        stream=True,
    )

    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def ai_ask(
    v: str, *, meaning: str | None = "", cloze: str | None = ""
) -> Generator[dict, None, None]:
    """
    Ask AI with a question type

    This function first attempts to use local AI. If that fails,
    it falls back to online AI. If both methods fail, it returns None.
    In case of translation, the result string is cached in the database for future use.

    Args:
        v (str): The string of vocab to ask.
        meaning (str | None): The string of user supplied meaning to the vocab

    Returns:
        Generator[dict, None, None]: The answered JSON, or None if all methods fail.
    """
    llm_stream: Generator[str, None, None] | None = None
    q_system = Q_TRANSLATION_SYSTEM
    q_user = Q_TRANSLATION.format(v=v)
    name = f"{v} translation"
    cloze_results = []

    if meaning:
        name = f"{v} meaning"
        q_system = Q_MEANING_WITH_CLOZE

        if not env.get(f"{ENV_LOCAL_KEY_PREFIX}ALWAYS_NEW_CLOZE"):
            for r in db.execute("SELECT arr FROM ai_cloze WHERE v = ? LIMIT 1", (v,)):
                q_system = Q_MEANING
                cloze_results = json.loads(r["arr"])
                print(f"{v}: reusing AI cloze")

        q_user = f'Is "{meaning}" a correct meaning for "{v}" in Chinese?'
        if cloze:
            q_user = f'Is "{meaning}" a correct meaning for "{v}" in sentence "{cloze}" in Chinese?'
        else:
            cloze_results = []

    is_ai_run = False

    def do_local():
        if get_can_local():
            nonlocal is_ai_run
            is_ai_run = True

            print(f"{name}: using local AI")
            return stream_ai_ask(q_system, q_user, False)

    def do_online():
        if get_can_online():
            nonlocal is_ai_run
            is_ai_run = True

            print(f"{name}: using online AI")
            return stream_ai_ask(q_system, q_user, True)

    if meaning:
        llm_stream = do_local() or do_online()
    else:
        llm_stream = do_online() or do_local()

    if not llm_stream:
        return

    current_output = ""

    obj: dict = {}

    def get_correct():
        correct: bool | None = obj.get("correct")
        if correct is not None and type(correct) is not bool:
            return None
        return correct

    def get_explanation():
        explanation: str | None = obj.get("explanation")
        if type(explanation) is not str:
            return None
        return explanation

    for chunk in llm_stream:
        current_output += chunk

        if not meaning:
            obj["translation"] = current_output
        else:
            obj = repair_json(current_output, return_objects=True, stream_stable=True)  # type: ignore
            if not isinstance(obj, dict):
                continue

            obj["v"] = v
            obj["q_user"] = q_user

            if not get_explanation():
                yield obj
                continue

            if cloze_results:
                obj["cloze"] = cloze_results

            # wait for complete explanation to yield
            # yield obj

    with db_lock:
        if not meaning:
            db.execute(
                "INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)",
                (v, current_output),
            )
        else:
            correct = get_correct()
            explanation = get_explanation()
            if explanation:
                db.execute(
                    """
                    INSERT OR REPLACE INTO revlog_meaning (v, correct, explanation, answer, cloze)
                    VALUES (?,?,?,?,?)
                    """,
                    (
                        v,
                        5 if correct is None else int(correct),
                        explanation,
                        meaning,
                        cloze or "",
                    ),
                )

        db.commit()

    obj["isComplete"] = True
    yield obj

    obj_cloze = obj.get("cloze")
    if not isinstance(obj_cloze, list):
        return

    is_valid_cloze = True
    errors: set[str] = set()
    re_han = Regex(r"\p{Han}")

    # a space followed by alphabets (having upper/lower cases) or "English" punctuations (!-~)
    # ending with an "English" period (not Chinese ones like 。)
    # e.g. ' "Émanuel".'
    # includes (brackets of sentence meaning.)
    re_en = Regex(r" [\p{L&}\p{M}!-~]+\.")

    for r in obj_cloze:
        if type(r) is not dict or not all(
            k in r for k in ["question", "headword", "alt"]
        ):
            is_valid_cloze = False
            continue

        q: str = r["question"]
        headword: str = r["headword"]
        alt: list[str] = r["alt"]

        if headword != v:
            e = f"q for {headword}"
            errors.add(e)
            print(f"Error: {v} ({e}): {q}")
            break

        filtered_alt = [s for s in alt if s != v]

        if not alt:
            e = f"{v} in {alt}"
            errors.add(e)
            print(f"Error: {v} ({e}): {q}")
            break

        alt = filtered_alt
        r["alt"] = alt

        if not re_han.search(q) or re_en.search(q):
            e = f"malformed q"
            errors.add(e)
            print(f"Error: {v} ({e}): {q}")
            break

        if "_" not in q:
            q = q.replace(v, "__")
            if "_" not in q:
                e = f"no cloze deletion"
                errors.add(e)
                print(f"Error: {v} ({e}): {q}")
                break
            r["question"] = q

    if not is_valid_cloze:
        return

    with db_lock:
        if not errors:
            print(f"{v}: saving AI cloze")
            db.execute(
                "INSERT OR REPLACE INTO ai_cloze (v, arr, modified) VALUES (?, ?, datetime())",
                (v, json.dumps(obj_cloze, ensure_ascii=False)),
            )
        else:
            db.execute(
                "INSERT INTO ai_error (v,error,output) VALUES (?,?,?)",
                (
                    v,
                    json.dumps(list(errors), ensure_ascii=False),
                    json.dumps(obj, ensure_ascii=False),
                ),
            )

        db.commit()


def load_db():
    """
    Initialize the database.

    This function creates the `ai_dict` table if it does not exist and removes
    placeholder entries from the table.

    This function creates the `ai_cloze` table if it does not exist.
    """
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS ai_dict (
            v TEXT NOT NULL,
            t TEXT NOT NULL,
            PRIMARY KEY (v)
        );

        CREATE TABLE IF NOT EXISTS ai_cloze (
            v   TEXT NOT NULL,
            arr JSON NOT NULL,
            modified TEXT,
            PRIMARY KEY (v)
        );

        CREATE TABLE IF NOT EXISTS revlog_meaning (
            v           TEXT NOT NULL,
            created     TEXT NOT NULL DEFAULT (datetime()),
            correct     INTEGER NOT NULL,
            explanation TEXT NOT NULL,
            answer      TEXT NOT NULL,
            cloze       TEXT NOT NULL
            -- PRIMARY KEY (ROWID)
        );

        CREATE INDEX IF NOT EXISTS idx_revlog_meaning_v       ON revlog_meaning (v);
        CREATE INDEX IF NOT EXISTS idx_revlog_meaning_created ON revlog_meaning (created);
        CREATE INDEX IF NOT EXISTS idx_revlog_meaning_correct ON revlog_meaning (correct);

        CREATE TABLE IF NOT EXISTS ai_error (
            v           TEXT NOT NULL,
            error       TEXT NOT NULL,
            output      TEXT NOT NULL,
            created     TEXT NOT NULL DEFAULT (datetime())
        );
        """
    )

    if db.execute("PRAGMA user_version").fetchone()[0] < 2:
        if not db.execute(
            "SELECT 1 FROM pragma_table_info('ai_cloze') WHERE name = 'modified'"
        ).fetchmany(1):
            db.executescript("ALTER TABLE ai_cloze ADD COLUMN modified TEXT")

    db.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_ai_cloze_modified ON ai_cloze (modified);
        """
    )

    # Delete placeholder entries
    db.execute("DELETE FROM ai_dict WHERE t = ''")
    db.commit()


def _test_speed(n=5):
    # Test the speed of the AI translation
    for r in db.execute(f"SELECT v FROM vlist ORDER BY RANDOM() LIMIT {n}"):
        v = r[0]
        print(">", v)
        translation = ai_ask(v)
        print(translation)


if __name__ == "__main__":
    # Load the database
    load_db()

    # Test the speed of the AI ask
    _test_speed()
