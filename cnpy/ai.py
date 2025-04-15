from openai import AsyncOpenAI
from ollama import AsyncClient
from dotenv import load_dotenv

from cnpy.db import db
from cnpy.dir import exe_root

# Load environment variables from .env file
load_dotenv(dotenv_path=exe_root / ".env")

can_local_ai_translation = True
can_online_ai_translation = True


ollama_client: AsyncClient | None = None


async def local_ai_translation(v: str) -> str | None:
    """
    Translate a string using local AI.

    Notes:
        - This function requires the Ollama library to be installed and configured.
        - The model "starling-lm" should be available locally.
        - If the function fails (e.g., model not found or Ollama not installed),
          local AI translation will be disabled for subsequent calls.

    See Also:
        - https://ollama.com for installation instructions.
        - https://ollama.com/library/starling-lm for model details.

    Args:
        v (str): The string to translate.

    Returns:
        str | None: The translated string, or None if the translation fails.
    """
    try:
        print("Using local AI translation for:", v)

        global ollama_client
        if not ollama_client:
            ollama_client = AsyncClient()

        response = await ollama_client.chat(
            model="starling-lm",  # Replace with other models if needed
            messages=[{"role": "user", "content": f'"{v}"是'}],
        )

        # Print completion details after awaiting the response
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


openai_client: AsyncOpenAI | None = None


async def online_ai_translation(v: str) -> str | None:
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
    try:
        print("Using online AI translation for:", v)

        global openai_client
        if not openai_client:
            openai_client = AsyncOpenAI(
                base_url="https://api.deepseek.com",  # Replace with other providers if needed
                # api_key="",  # Replace with your actual API key or use environment variable OPENAI_API_KEY
            )

        response = await openai_client.chat.completions.create(
            model="deepseek-chat",  # Replace with other models if needed
            messages=[{"role": "user", "content": f'"{v}"是'}],
            temperature=1.3,  # Adjust temperature according to documentation
            stream=False,
        )

        # Print completion details after awaiting the response
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


async def ai_translation(v: str) -> str | None:
    """
    Translate a string using AI.

    The function first checks the local database for a translation. If not found, it attempts
    online AI translation, followed by local AI translation as a fallback.

    Args:
        v (str): The string to translate.

    Returns:
        str | None: The translated string, or None if all translation methods fail.
    """
    # Try online AI translation first
    if can_online_ai_translation:
        t = await online_ai_translation(v)
        if t:
            db.execute("INSERT OR REPLACE INTO ai_dict (v, t) VALUES (?, ?)", (v, t))
            db.commit()
            return t

    # If online translation fails, fall back to local translation
    if can_local_ai_translation:
        t = await local_ai_translation(v)
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


async def _test_speed(n=5):
    # Test the speed of the AI translation
    for r in db.execute(f"SELECT v FROM vlist ORDER BY RANDOM() LIMIT {n}"):
        v = r[0]
        print(">", v)
        translation = await ai_translation(v)
        print(translation)


if __name__ == "__main__":
    import asyncio

    # Load the database
    load_db()

    # Test the speed of the AI translation
    asyncio.run(_test_speed())
