import json
import logging
from urllib.parse import quote

from linebot.models import FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, ButtonComponent, URIAction

from app.services.groq_service import chat_with_groq

logger = logging.getLogger(__name__)


def get_english_word():
    """
    使用 Groq AI 提供英文單字學習內容
    功能：獲取一個日常生活中常用的英文單字或表達方式，並提供完整的學習資訊
    返回：包含單字、發音、詞性、英文解釋、中文意思、例句及翻譯的完整學習內容
    """
    system_id = "english_word_system"

    prompt = """請提供一個英文單字學習內容，包含以下部分：
    1. 單字 (word)
    2. 發音，使用台灣常用的 KK 音標 (pronunciation)
    3. 詞性 (part of speech)
    4. 英文解釋 (definition in English)
    5. 中文意思 (definition in Chinese)
    6. 例句 (example sentence)
    7. 例句翻譯 (translation of example)

    請提供一個日常生活中常用、但詞彙難度略高（如 CEFR B1~B2 級），能提升英文口說或寫作層次的實用單字或表達方式，適合一般對話或正式場合使用。

    請依照上述項目，以 **純 JSON 格式回覆**，**不要包含多餘文字或說明**，並且確認資訊準確。

    以下為格式範例：
    {
      "word": "negotiate",
      "pronunciation": "/nɪˈɡoʊʃiˌeɪt/",
      "part_of_speech": "verb",
      "definition_en": "to discuss something formally in order to reach an agreement",
      "definition_zh": "協商、談判",
      "example_sentence": "We need to negotiate a better deal with the supplier.",
      "example_translation": "我們需要與供應商協商更好的條件。"
    }
    """

    response = chat_with_groq(system_id, prompt)

    try:
        if isinstance(response, str):
            logger.debug(f"Response is a string: {response[:200]}")
            try:
                word_data = json.loads(response)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'(\{.*\})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    word_data = json.loads(json_str)
                else:
                    raise ValueError("Unable to extract JSON format from the string response")
        elif hasattr(response, 'text'):
            response_text = response.text
            logger.debug(f"Response has text attribute: {response_text[:200]}")
            try:
                word_data = json.loads(response_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    word_data = json.loads(json_str)
                else:
                    raise ValueError("Unable to extract JSON format from the response text")
        elif hasattr(response, 'json'):
            word_data = response.json()
        else:
            raise TypeError(f"Unsupported response type: {type(response)}")

    except Exception as e:
        logger.error(f"Failed to parse response as JSON: {str(e)}")
        logger.debug(f"Original response: {str(response)[:500]}")

        # 提供默認單字資訊作為備用
        word_data = {
            "word": "fallback",
            "pronunciation": "/ˈfɔːlbæk/",
            "part_of_speech": "noun",
            "definition_en": "something or someone to turn to in case of failure or emergency",
            "definition_zh": "備用方案、後備選擇",
            "example_sentence": "We need a fallback plan in case this doesn't work.",
            "example_translation": "我們需要一個備用計劃，以防這個不起作用。"
        }

    required_fields = ["word", "pronunciation", "part_of_speech", "definition_en",
                       "definition_zh", "example_sentence", "example_translation"]

    for field in required_fields:
        if field not in word_data:
            word_data[field] = ""
            logger.warning(f"Missing '{field}' field in word data. Set to empty string.")

    flex_bubble = create_flex_bubble(word_data)
    return FlexSendMessage(
        alt_text=f"英文單字：{word_data['word']}",
        contents=flex_bubble
    )


def create_flex_bubble(word_data):
    """
    使用 LINE SDK 的原生物件建立 Flex 訊息
    """
    # 生成單字發音連結
    try:
        word_audio_url = generate_audio_url(word_data["word"])
    except Exception as e:
        logger.error(f"Error occurred while generating word pronunciation URL: {str(e)}")
        word_audio_url = ""

    # 生成例句發音連結
    try:
        example_audio_url = generate_audio_url(word_data["example_sentence"])
    except Exception as e:
        logger.error(f"Error occurred while generating example sentence pronunciation URL: {str(e)}")
        example_audio_url = ""

    # 使用 LINE SDK 內建的物件
    header_box = BoxComponent(
        layout="vertical",
        contents=[
            TextComponent(text="📖英文單字", weight="bold", size="lg")
        ]
    )

    body_contents = [
        TextComponent(
            text=f"📚 {word_data['word']} ({word_data['part_of_speech']})",
            weight="bold",
            size="xl",
            wrap=True
        ),
        TextComponent(
            text=f"🔊 {word_data.get('pronunciation', '')}",
            size="md",
            color="#888888",
            wrap=True
        ),
        TextComponent(
            text=f"💡 英文解釋: {word_data['definition_en']}",
            size="sm",
            color="#555555",
            wrap=True
        ),
        TextComponent(
            text=f"📘 中文解釋: {word_data['definition_zh']}",
            size="sm",
            color="#555555",
            wrap=True
        ),
        TextComponent(
            text="✏️ 例句:",
            weight="bold",
            size="sm",
            wrap=True
        ),
        TextComponent(
            text=f"● {word_data['example_sentence']}",
            wrap=True,
            size="sm",
            color="#333333"
        ),
        TextComponent(
            text=f"○ {word_data['example_translation']}",
            wrap=True,
            size="sm",
            color="#666666"
        )
    ]

    body_box = BoxComponent(
        layout="vertical",
        spacing="md",
        contents=body_contents
    )

    footer_box = BoxComponent(
        layout="vertical",
        spacing="sm",
        contents=[
            ButtonComponent(
                action=URIAction(
                    label="🔊 單字發音",
                    uri=word_audio_url
                ),
                style="primary",
                color="#00C300"
            ),
            ButtonComponent(
                action=URIAction(
                    label="🔊 例句發音",
                    uri=example_audio_url
                ),
                style="secondary",
                color="#1E90FF"
            )
        ]
    )

    # 建立 BubbleContainer
    bubble = BubbleContainer(
        header=header_box,
        body=body_box,
        footer=footer_box
    )

    return bubble


# 產生 Google TTS 音訊連結
def generate_audio_url(text):
    if not text:
        return ""
    encoded_text = quote(text)
    return f"https://translate.google.com/translate_tts?ie=UTF-8&tl=en&client=tw-ob&q={encoded_text}"


def get_japanese_word():
    from linebot.models import TextSendMessage
    return TextSendMessage(text="我們正在努力開發此功能,敬請期待")