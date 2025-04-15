import time
import os

from openai import OpenAI
from ollama import Client
from dotenv import load_dotenv

from cnpy.db import db
from cnpy.dir import exe_root

# Load environment variables from .env file
load_dotenv(dotenv_path=exe_root / ".env")

can_local_ai_translation = True
can_online_ai_translation = True


ollama_client: Client | None = None


def local_ai_translation(v: str) -> str | None:
    """
    Translate a string using local AI.

    Notes:
        - This function requires the Ollama library to be installed and configured.
        - If the function fails (e.g., model not found or Ollama not installed),
          local AI translation will be disabled for subsequent calls.

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
                host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            )

        response = ollama_client.chat(
            model=os.getenv("OLLAMA_MODEL", "qwen:7b"),
            messages=[{"role": "user", "content": f'"{v}"是'}],
        )

        # Print completion details after awaiting the response
        print(f"{v} completed local AI response")
        result = response.message.content
    except Exception as e:
        print(f"Error in ai_translation {v}: {e}")

        # Disable local AI translation if it fails
        # such as model not found or ollama not installed
        global can_local_ai_translation
        can_local_ai_translation = False

        print("Disabled local AI translation")

    print(f"Local AI translation {v} took {time.time() - start:.2f} seconds")
    return result


openai_client: OpenAI | None = None


def online_ai_translation(v: str) -> str | None:
    """
    Translate a string using online AI.

    Notes:
        - This function requires DeepSeek's OpenAI API to be configured.
        - If the function fails due to network issues, authentication errors,
          or lack of subscription, online AI translation will be disabled for subsequent calls.
        - Other errors (e.g., rate limits or server errors) will not disable online translation.

    See Also:
        - https://api-docs.deepseek.com for API documentation.

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
                base_url=os.getenv("OPENAI_API_BASE", "https://api.deepseek.com"),
                # api_key="",  # Replace with your actual API key or use environment variable OPENAI_API_KEY
            )

        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
            messages=[{"role": "user", "content": f'"{v}"是'}],
            temperature=float(
                os.getenv("OPENAI_TEMPERATURE", "1.3")
            ),  # Adjust temperature according to documentation
            stream=False,
        )

        # Print completion details after awaiting the response
        print(f"{v} completed online AI response")
        result = response.choices[0].message.content
    except Exception as e:
        print(f"Error in ai_translation: {e}")

        # Check for authentication or connection errors
        # and disable online AI translation if necessary
        msg = str(e).lower()
        if "api_key" in msg or "authentication" in msg or "connection" in msg:
            global can_online_ai_translation
            can_online_ai_translation = False

            print("Disabled online AI translation")

    print(f"Online AI translation {v} took {time.time() - start:.2f} seconds")
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
