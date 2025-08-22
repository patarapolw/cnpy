import time
import json
import traceback
import pprint

from openai import OpenAI
from ollama import Client
from regex import Regex

from cnpy.db import db
from cnpy.env import env
from cnpy.sync import ENV_LOCAL_KEY_PREFIX


def get_local_model():
    return env.get(f"{ENV_LOCAL_KEY_PREFIX}OLLAMA_MODEL") or ""


def get_can_local():
    return bool(get_local_model())


def get_online_model():
    return env.get("OPENAI_MODEL") or "deepseek-chat"


def get_can_online():
    return bool(env.get("OPENAI_API_KEY") or "")


Q_TRANSLATION_SYSTEM = """
You are a monolingual Chinese dictionary with Pinyin and Bopomofo reading / encyclopedia / colloquial language reference.
Give meanings and explanations in Chinese.
Avoid giving reading or meaning in examples, only giving for the headword.
In case of multiple readings, list results separately by readings.
""".strip()
Q_TRANSLATION = '"{v}"是什么？'

Q_MEANING_ROLE = """
You are an AI language expert specializing in modern Mandarin Chinese linguistics.
Your task is to evaluate whether a provided meaning accurately matches a given Chinese word.
Also consider possibility that the provided meaning is a typo.

* If the meaning is **clearly correct**, return `"correct": true`.
* If the meaning is **clearly wrong**, return `"correct": false`.
* If the meaning is **ambiguous, partially correct, or depends on context**, return `"correct": null`.

Then, explain why the meaning is correct, incorrect, or partially accurate. Include the Pinyin of the given Chinese word in the given meaning context. Include nuances and common uses.
""".strip()

Q_MEANING = f"""
{Q_MEANING_ROLE}

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
* Reading and meaning **must not be included** inside the cloze test sentences and Chinese words.

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


def ollama_ai_ask(q_system: str, q_user: str) -> str | None:
    """
    Ask a question using Ollama.

    Notes:
        - This function requires the Ollama library to be installed and configured.

    See Also:
        - https://ollama.com for installation instructions.

    Args:
        q_system (str): The string defining system role.
        q_user (str): The string to ask.

    Returns:
        str | None: The answered string, or None if fails.
    """
    result = None

    try:
        # todo: OpenAI compatibility (https://github.com/ollama/ollama/blob/main/docs/openai.md)
        ollama_client = Client(
            # Use environment variable CNPY_LOCAL_OLLAMA_HOST
            host=env.get(f"{ENV_LOCAL_KEY_PREFIX}OLLAMA_HOST")
        )

        response = ollama_client.chat(
            model=get_local_model(),
            messages=[
                {"role": "system", "content": q_system},
                {"role": "user", "content": q_user},
            ],
        )

        result = response.message.content
    except Exception as e:
        print(f"Error in ollama_ai `{q_user}`: {e}")

    return result


def online_ai_ask(q_system: str, q_user: str) -> str | None:
    """
    Ask a question using online AI.

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
    result = None

    try:
        model = get_online_model()

        model_type = "openai"
        base_url = "https://api.openai.com/v1"
        if model.startswith("deepseek-"):
            model_type = "deepseek"
            base_url = "https://api.deepseek.com"
        elif model.startswith("gemini-") or model.startswith("gemma-"):
            model_type = "google"
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

        base_url = env.get("OPENAI_BASE_URL") or base_url

        openai_client = OpenAI(
            base_url=base_url,
            api_key=env.get("OPENAI_API_KEY"),
        )

        temperature = env.get("OPENAI_TEMPERATURE")
        if not temperature and model == "deepseek-chat":
            temperature = "1.3"

        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                (
                    {"role": "user", "content": q_system}
                    if model_type == "google"
                    else {"role": "system", "content": q_system}
                ),
                {"role": "user", "content": q_user},
            ],
            temperature=float(
                temperature or "1"
            ),  # Adjust temperature according to documentation
            stream=False,
        )

        result = response.choices[0].message.content
    except Exception as e:
        print(f"Error in online_ai `{q_user}`: {e}")

    return result


def ai_ask(v: str, *, meaning: str | None = "", cloze: str | None = "") -> str | None:
    """
    Ask AI with a question type

    This function first attempts to use local AI. If that fails,
    it falls back to online AI. If both methods fail, it returns None.
    In case of translation, the result string is cached in the database for future use.

    Args:
        v (str): The string of vocab to ask.
        meaning (str | None): The string of user supplied meaning to the vocab

    Returns:
        str | None: The answered string, or None if all methods fail.
    """
    t: str | None = None
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

    start = time.time()

    is_ai_run = False

    def do_local():
        if get_can_local():
            nonlocal is_ai_run
            is_ai_run = True

            print(f"{name}: using local AI")
            return ollama_ai_ask(q_system, q_user)

    def do_online():
        if get_can_online():
            nonlocal is_ai_run
            is_ai_run = True

            print(f"{name}: using online AI")
            return online_ai_ask(q_system, q_user)

    if meaning:
        t = do_local() or do_online()
    else:
        t = do_online() or do_local()

    if is_ai_run:
        print(f"{name}: AI response took {time.time() - start:.1f} seconds")

    if not t:
        return None

    if meaning:
        try:
            # Like find(), but raise ValueError when the substring is not found.
            # @see https://docs.python.org/3/library/stdtypes.html#str.index
            i_opening = t.index("{")

            i_closing = t.rfind("}")
            if i_closing == -1:
                raise ValueError("Closing '}' not found in AI response")

            r = t[i_opening : i_closing + 1]
            obj = json.loads(r)

            if cloze_results:
                obj["cloze"] = cloze_results
            else:
                errors: set[str] = set()
                re_han = Regex(r"\p{Han}")

                # a space followed by alphabets (having upper/lower cases) or "English" punctuations (!-~)
                # ending with an "English" period (not Chinese ones like 。)
                # e.g. ' "Émanuel".'
                # includes (brackets of sentence meaning.)
                re_en = Regex(r" [\p{L&}\p{M}!-~]+\.")

                cloze_results = obj["cloze"]
                for r in cloze_results:
                    q: str = r["question"]
                    headword: str = r["headword"]
                    alt: list[str] = r["alt"]

                    if headword != v:
                        e = f"q for {headword}"
                        errors.add(e)
                        print(f"{v} ({e}): {q}")
                        break

                    if v in alt:
                        e = f"{v} in {alt}"
                        errors.add(e)
                        print(f"{v} ({e}): {q}")
                        break

                    if not re_han.match(q) or re_en.match(q):
                        e = f"malformed q"
                        errors.add(e)
                        print(f"{v} ({e}): {q}")
                        break

                    if "_" not in q:
                        q = q.replace(v, "__")
                        if "_" not in q:
                            e = f"no cloze deletion"
                            errors.add(e)
                            print(f"{v} ({e}): {q}")
                            break
                        r["question"] = q

                if not errors:
                    print(f"{v}: saving AI cloze")
                    db.execute(
                        "INSERT OR REPLACE INTO ai_cloze (v, arr) VALUES (?, ?)",
                        (v, json.dumps(cloze_results, ensure_ascii=False)),
                    )

            obj["q_user"] = q_user
            t = json.dumps(obj, ensure_ascii=False)

            obj["v"] = v
            pprint.pp(obj, sort_dicts=False)
        except ValueError:
            traceback.print_exc()
            print(v, t)
    else:
        print(f"{v}: saving AI translation")
        db.execute("INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)", (v, t))
        db.commit()

    return t


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
            PRIMARY KEY (v)
        );
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
