import time

from openai import OpenAI
from ollama import Client

from cnpy.db import db
from cnpy.env import env
from cnpy.sync import ENV_LOCAL_KEY_PREFIX

local_ai_model = env.get(f"{ENV_LOCAL_KEY_PREFIX}OLLAMA_MODEL") or ""
can_local_ai = bool(local_ai_model)

can_online_ai = bool(env.get("OPENAI_API_KEY") or "")

Q_TRANSLATION = '"{v}"是什么？有什么读法（注音在内），用法，关联词/句子？'
Q_MEANING = """
You are a Chinese translation checker.
You will be given a vocabulary and a meaning in English. Determine if the meaning matches.
Misspellings are considered acceptable. If wrong, give the translation of the English instead.

Answer in JSON:
{{
  "correct": true, // false if wrong, null if it depends / not sure
  "explanation": "" // give some explanation why right or wrong, and also other possible meanings of the vocabulary
}}

Is "{m}" a correct meaning for "{v}" in Chinese?
""".strip()


ollama_client: Client | None = None


def ollama_ai_ask(s: str) -> str | None:
    """
    Ask a question using Ollama.

    Notes:
        - This function requires the Ollama library to be installed and configured.

    See Also:
        - https://ollama.com for installation instructions.

    Args:
        s (str): The string to ask.

    Returns:
        str | None: The answered string, or None if fails.
    """
    result = None

    try:
        global ollama_client
        if not ollama_client:
            ollama_client = Client(
                # Use environment variable CNPY_LOCAL_OLLAMA_HOST
                host=env.get(f"{ENV_LOCAL_KEY_PREFIX}OLLAMA_HOST")
            )

        response = ollama_client.chat(
            model=local_ai_model,
            messages=[{"role": "user", "content": s}],
        )

        result = response.message.content
    except Exception as e:
        print(f"Error in ollama_ai `{s}`: {e}")

    return result


openai_client: OpenAI | None = None


def online_ai_ask(s: str) -> str | None:
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
        v (str): The string to ask.

    Returns:
        str | None: The answered string, or None if fails.
    """
    result = None

    try:
        global openai_client
        if not openai_client:
            openai_client = OpenAI(
                base_url=env.get("OPENAI_BASE_URL") or "https://api.deepseek.com",
                # api_key=None,  # Use environment variable OPENAI_API_KEY
            )

        model = env.get("OPENAI_MODEL") or "deepseek-chat"
        temperature = env.get("OPENAI_TEMPERATURE")
        if not temperature and model == "deepseek-chat":
            temperature = "1.3"

        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": s}],
            temperature=float(
                temperature or "1"
            ),  # Adjust temperature according to documentation
            stream=False,
        )

        result = response.choices[0].message.content
    except Exception as e:
        print(f"Error in online_ai `{s}`: {e}")

    return result


def ai_ask(v: str, meaning: str | None = "") -> str | None:
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
    prompt = Q_MEANING.format(v=v, m=meaning) if meaning else Q_TRANSLATION.format(v=v)

    start = time.time()

    if can_local_ai:
        print(f"{v}: using local AI")
        t = ollama_ai_ask(prompt)

    if not t and can_online_ai:
        print(f"{v}: using online AI")
        t = online_ai_ask(prompt)

    print(f"{v}: AI response took {time.time() - start:.1f} seconds")

    if t and not meaning:
        print(f"{v}: saving AI translation")
        db.execute("INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)", (v, t))
        db.commit()

    # If both online and local fail, return None
    return t or None


def load_db():
    """
    Initialize the database.

    This function creates the `ai_dict` table if it does not exist and removes
    placeholder entries from the table.
    """
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_dict (
            v TEXT NOT NULL,
            t TEXT NOT NULL,
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
