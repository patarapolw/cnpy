from openai import OpenAI
from dotenv import load_dotenv

from cnpy.db import db

# Load environment variables from .env file
load_dotenv()

can_local_ai_translation = True
can_online_ai_translation = True


def local_ai_translation(v: str) -> str | None:
    """
    Translate a string using local AI.

    :note: This function requires the Ollama library to be installed and configured.
    :see: https://ollama.com for installation instructions.
    :note: The model "starling-lm" should be available locally.
    :see: https://ollama.com/library/starling-lm for model details.
    :param v: The string to translate.
    :return: The translated string or None if fails.
    """
    from ollama import chat

    try:
        print("Using local AI translation for:", v)

        response = chat(
            model="starling-lm",  # Replace with other models if needed
            messages=[{"role": "user", "content": f'"{v}"是'}],
        )

        print(f"{v} completed local AI response")
        return response.message.content
    except Exception as e:
        print(f"Error in ai_translation: {e}")

        # Disable local AI translation if it fails
        # such as model not found or ollama not installed
        global can_local_ai_translation
        can_local_ai_translation = False

        print("Disabled local AI translation")

    return None


client: OpenAI | None = None


def online_ai_translation(v: str) -> str | None:
    """
    Translate a string using online AI.

    :note: This function requires DeepSeek's OpenAI API to be configured.
    :see: https://api-docs.deepseek.com for API documentation.
    :param v: The string to translate.
    :return: The translated string or None if fails.
    """
    try:
        print("Using online AI translation for:", v)

        global client
        if not client:
            client = OpenAI(
                base_url="https://api.deepseek.com",  # Replace with other providers if needed
                # api_key="",  # Replace with your actual API key or use environment variable OPENAI_API_KEY
            )

        response = client.chat.completions.create(
            model="deepseek-chat",  # Replace with other models if needed
            messages=[{"role": "user", "content": f'"{v}"是'}],
            temperature=1.3,  # Adjust temperature according to documentation
            stream=False,
        )

        print(f"{v} completed online AI response")
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in ai_translation: {e}")

        # Check for authentication or connection errors
        # and disable online AI translation if necessary
        msg = str(e).lower()
        if "api_key" in msg or "authentication" in msg or "connection" in msg:
            global can_online_ai_translation
            can_online_ai_translation = False

            print("Disabled online AI translation")

    return None


def ai_translation(v: str) -> str | None:
    """
    Translate a string using AI.
    :param v: The string to translate.
    :return: The translated string or None if fails.
    """
    for r in db.execute("SELECT t FROM ai_dict WHERE v = ? LIMIT 1", (v,)):
        return r[0]

    # If not found in the database, insert a placeholder
    # to avoid repeated queries
    db.execute("INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)", (v, ""))
    db.commit()

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
    # Create the database if it doesn't exist
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


if __name__ == "__main__":
    # Test the speed of the AI translation
    for r in db.execute("SELECT v FROM vlist ORDER BY RANDOM() LIMIT 5"):
        v = r[0]
        print(">", v)
        translation = ai_translation(v)
        print(translation)
