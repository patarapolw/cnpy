import requests
import json

from .dir import web_root

is_api_available = True


def tts_audio(text: str, voice=""):
    """
    ```
    docker run -dp 127.0.0.1:8501:8501 -p 127.0.0.1:8000:8000 syq163/emoti-voice:latest
    ```
    See https://github.com/netease-youdao/EmotiVoice/pull/60#issuecomment-2476641137

    Args:
        text (str): Text to speak
        voice (str, optional): https://github.com/netease-youdao/EmotiVoice/wiki/%F0%9F%98%8A-voice-wiki-page

    Returns:
        Path | None: None is unsuccessful
    """
    global is_api_available

    if not is_api_available:
        return

    if not voice:
        voice = "6097"

    ttsDir = web_root / "tts"
    ttsDir.mkdir(exist_ok=True)

    outPath = ttsDir / f"[{voice}]{text}.mp3"
    if outPath.exists():
        return outPath

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
        print(f"Audio saved to {outPath}")

        return outPath

    print(f"Failed to get audio. Status code: {response.status_code}")
    print(f"Response: {response.text}")

    is_api_available = False


# 主程序调用部分
if __name__ == "__main__":
    text = "调试成功，调用TTS成功"
    tts_audio(text)
