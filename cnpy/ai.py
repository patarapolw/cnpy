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
            messages=[{"role": "user", "content": f'"${v}"是'}],
        )

        print("AI response:", response)
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
                # api_key="",  # Replace with your actual API key
            )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": f'"${v}"是'}],
            temperature=1.3,
            stream=False,
        )

        print("AI response:", response)
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
    for r in db.execute("SELECT t FROM vlist_ai WHERE v = ? LIMIT 1", (v,)):
        return r[0]

    global can_online_ai_translation, can_local_ai_translation

    if can_online_ai_translation:
        t = online_ai_translation(v)
        if t:
            db.execute("INSERT OR REPLACE INTO vlist_ai (v, t) VALUES (?, ?)", (v, t))
            db.commit()
            return t

        can_online_ai_translation = False
    # If online translation fails, fall back to local translation

    if can_local_ai_translation:
        t = local_ai_translation(v)
        if t:
            db.execute("INSERT OR REPLACE INTO vlist_ai (v, t) VALUES (?, ?)", (v, t))
            db.commit()
            return t

        can_local_ai_translation = False

    return ""


def load_db():
    """
    Load the database.
    :return: None
    """

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS vlist_ai (
            v TEXT NOT NULL,
            t TEXT NOT NULL,
            PRIMARY KEY (v)
        );
        """
    )
    db.commit()


if __name__ == "__main__":
    # Test the function"

    for r in db.execute("SELECT v FROM vlist ORDER BY RANDOM() LIMIT 5"):
        v = r[0]
        print(">", v)
        translation = online_ai_translation(v)
        print(translation)
