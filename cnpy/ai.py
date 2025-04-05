from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

from cnpy.db import db


def local_ai_translation(v: str) -> str | None:
    from ollama import chat

    try:
        print("Using local AI translation for:", v)

        response = chat(
            model="starling-lm",
            messages=[{"role": "user", "content": f'"{v}"是'}],
        )

        print(f"local AI response for {v}:", response)
        return response.message.content
    except Exception as e:
        print(f"Error in ai_translation: {e}")

    return None


client: OpenAI | None = None


def online_ai_translation(v: str) -> str | None:
    try:
        print("Using online AI translation for:", v)

        global client
        if not client:
            client = OpenAI(
                base_url="https://api.deepseek.com",
                # api_key="",  # Replace with your actual API key or use environment variable OPENAI_API_KEY
            )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f'"{v}"是'}],
            temperature=1.3,
            stream=False,
        )

        print(f"online AI response for {v}:", response)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in ai_translation: {e}")

    return None


can_online_ai_translation = True
can_local_ai_translation = True


def ai_translation(v: str) -> str:
    """
    Translate a string using AI.
    :param v: The string to translate.
    :return: The translated string or None if an error occurs.
    """
    for r in db.execute("SELECT t FROM ai_dict WHERE v = ? LIMIT 1", (v,)):
        return r[0]

    # If not found in the database, insert a placeholder
    # to avoid repeated queries
    db.execute("INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)", (v, ""))
    db.commit()

    global can_online_ai_translation, can_local_ai_translation

    # Try online AI translation first
    if can_online_ai_translation:
        t = online_ai_translation(v)
        if t:
            db.execute("INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)", (v, t))
            db.commit()
            return t

        can_online_ai_translation = False

    # If online translation fails, fall back to local translation
    if can_local_ai_translation:
        t = local_ai_translation(v)
        if t:
            db.execute("INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)", (v, t))
            db.commit()
            return t

        can_local_ai_translation = False

    # If both online and local translation fail, return an empty string
    # and mark the entry as failed
    return ""


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

    db.execute("DELETE FROM ai_dict WHERE t = ''")
    db.commit()


if __name__ == "__main__":
    # Test the speed of the AI translation
    for r in db.execute("SELECT v FROM vlist ORDER BY RANDOM() LIMIT 5"):
        v = r[0]
        print(">", v)
        translation = ai_translation(v)
        print(translation)
