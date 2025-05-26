from urllib.parse import quote


# 產生 Google TTS 音訊連結
def generate_audio_url(text):
    if not text:
        return ""
    encoded_text = quote(text)
    return f"https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q={encoded_text}"
