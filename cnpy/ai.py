import time
import os

from openai import OpenAI
from ollama import Client
from dotenv import load_dotenv

from cnpy.db import db
from cnpy.dir import exe_root

# Load environment variables from .env file
load_dotenv(dotenv_path=exe_root / ".env")

local_ai_model = os.getenv("OLLAMA_MODEL", "")
can_local_ai_translation = bool(local_ai_model)

can_online_ai_translation = bool(os.getenv("OPENAI_API_KEY"))

AI_QUESTION = os.getenv("CNPY_AI_QUESTION", '"{v}"是')


ollama_client: Client | None = None


def local_ai_translation(v: str) -> str | None:
    """
    Translate a string using local AI.

    Notes:
        - This function requires the Ollama library to be installed and configured.

    See Also:
        - https://ollama.com for installation instructions.

    Args:
        v (str): The string to translate.

    Returns:
        str | None: The translated string, or None if the translation fails.
    """
    start = time.time()
    result = None

    try:
        print("Using local AI translation for:", v)

        global ollama_client
        if not ollama_client:
            ollama_client = Client(
                # host=None,  # Use environment variable OLLAMA_HOST
            )

        response = ollama_client.chat(
            model=local_ai_model,
            messages=[{"role": "user", "content": AI_QUESTION.format(v=v)}],
        )

        # Print completion details after awaiting the response
        print(f"{v} completed local AI response")
        result = response.message.content
    except Exception as e:
        print(f"Error in ai_translation {v}: {e}")

    print(f"{v} local AI translation took {time.time() - start:.1f} seconds")
    return result


openai_client: OpenAI | None = None


def online_ai_translation(v: str) -> str | None:
    """
    Translate a string using online AI.

    Notes:
        - This function requires `OPENAI_API_KEY` to be set in the environment.
          Get one from https://platform.deepseek.com or https://platform.openai.com.

    See Also:
        - https://api-docs.deepseek.com to use DeepSeek with OpenAI API.
        - https://platform.openai.com/docs/models to use OpenAI models (e.g. GPT-4.1).
          Set `OPENAI_BASE_URL` to `https://api.openai.com/v1` in the `.env` file and set `OPENAI_MODEL` as appropriate.

    Args:
        v (str): The string to translate.

    Returns:
        str | None: The translated string, or None if the translation fails.
    """
    start = time.time()
    result = None

    try:
        print("Using online AI translation for:", v)

        global openai_client
        if not openai_client:
            openai_client = OpenAI(
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com"),
                # api_key=None,  # Use environment variable OPENAI_API_KEY
            )

        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
            messages=[{"role": "user", "content": AI_QUESTION.format(v=v)}],
            temperature=float(
                os.getenv("OPENAI_TEMPERATURE", "1.3")
            ),  # Adjust temperature according to documentation
            stream=False,
        )

        # Print completion details after awaiting the response
        print(f"{v} completed online AI response")
        result = response.choices[0].message.content
    except Exception as e:
        print(f"Error in ai_translation {v}: {e}")

    print(f"{v} online AI translation took {time.time() - start:.1f} seconds")
    return result


def ai_translation(v: str) -> str | None:
    """
    Translate a string using AI.

    This function first attempts to use online AI translation. If that fails,
    it falls back to local AI translation. If both methods fail, it returns None.
    The translated string is cached in the database for future use.

    Args:
        v (str): The string to translate.

    Returns:
        str | None: The translated string, or None if all translation methods fail.
    """
    # Try online AI translation first
    if can_online_ai_translation:
        t = online_ai_translation(v)
        if t:
            db.execute("INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)", (v, t))
            db.commit()
            return t

    # If online translation fails, fall back to local translation
    if can_local_ai_translation:
        t = local_ai_translation(v)
        if t:
            db.execute("INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)", (v, t))
            db.commit()
            return t

    # If both online and local translation fail, return None
    return None


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
        translation = ai_translation(v)
        print(translation)


if __name__ == "__main__":
    # Load the database
    load_db()

    # Test the speed of the AI translation
    _test_speed()
