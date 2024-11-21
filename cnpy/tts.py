from gtts import gTTS

import requests
import json

from .dir import tmp_root

is_emoti_available = True
is_gtts_available = True


ttsDir = tmp_root / "tts"
ttsDir.mkdir(exist_ok=True)


def tts_audio(text: str, voice=""):
    return emoti_audio(text, voice) or gtts_audio(text)


def emoti_audio(text: str, voice=""):
    """
    ```
    docker run -dp 127.0.0.1:8501:8501 -p 127.0.0.1:8000:8000 syq163/emoti-voice:latest
    ```
    See https://github.com/netease-youdao/EmotiVoice/pull/60#issuecomment-2476641137

    Args:
        text (str): text to speak
        voice (str, optional): https://github.com/netease-youdao/EmotiVoice/wiki/%F0%9F%98%8A-voice-wiki-page

    Returns:
        Path | None: None if unsuccessful
    """
    if not voice:
        voice = "9017"

    outPath = ttsDir / f"[{voice}]{text}.mp3"
    if outPath.exists():
        return outPath

    global is_emoti_available

    if not is_emoti_available:
        return

    try:
        headers = {"Content-Type": "application/json"}
        url = "http://localhost:8000/v1/audio/speech"
        query = {
            "model": "emoti-voice",
            "input": text,  # 使用传入的文本参数
            "voice": voice,
            "response_format": "mp3",
            "speed": 1,
        }
        response = requests.post(url=url, data=json.dumps(query), headers=headers)

        # 检查请求是否成功
        if response.status_code == 200:
            # 保存文件
            with open(outPath, "wb") as f:
                f.write(response.content)
            print(f"emoti-voice saved to {outPath}")

            return outPath

        print(f"Failed to get audio. Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(e)

    is_emoti_available = False


def gtts_audio(text: str):
    """
    This project is not affiliated with Google or Google Cloud. Breaking upstream changes can occur without notice. This project is leveraging the undocumented Google Translate speech functionality and is different from Google Cloud Text-to-Speech.

    See https://gtts.readthedocs.io/

    Args:
        text (str): text to speak

    Returns:
        Path | None: None if unsuccessful
    """

    voice = "gtts"
    outPath = ttsDir / f"[{voice}]{text}.mp3"
    if outPath.exists():
        return outPath

    global is_gtts_available
    if not is_gtts_available:
        return

    try:
        tts = gTTS(text, lang="zh-CN")
        tts.save(str(outPath))
        print(f"gtts saved to {outPath}")

        return outPath
    except Exception as e:
        print(e)

    is_gtts_available = False
