import json
import logging

from linebot.models import FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, ButtonComponent, URIAction

from app.services.groq_service import chat_with_groq
from app.utils.google_tts import generate_audio_url

logger = logging.getLogger(__name__)


def get_japanese_word(user_id: str):
    """
    使用 Groq AI 提供日文單字學習內容
    功能：獲取一個日常生活中常用的日文單字或表達方式，並提供完整的學習資訊
    返回：包含單字、假名、羅馬音、詞性、日文解釋、中文意思、例句及翻譯的完整學習內容
    """
    prompt = """請提供一個日文單字的學習內容，包含以下欄位：

    1. 單字 (word) - 漢字形式（如果有的話）
    2. 假名 (hiragana) - 平假名讀音
    3. 羅馬音 (romaji) - 羅馬字拼音
    4. 詞性 (part_of_speech)
    5. 日文解釋 (definition_ja)
    6. 中文解釋 (definition_zh)
    7. 例句 (example_sentence)
    8. 例句翻譯 (example_translation)

    請選擇難度符合日文檢定 N4-N3 級的單字，應為日常生活中常見且實用的詞彙，能夠提升口說與書寫能力，適用於一般對話或正式場合。

    請以 **純 JSON 格式** 回覆，**不要添加多餘說明或文字**，並請確認所有資訊準確無誤。

    以下為格式範例：
    {
      "word": "約束",
      "hiragana": "やくそく",
      "romaji": "yakusoku",
      "part_of_speech": "名詞",
      "definition_ja": "前もって決めた事柄を守ること",
      "definition_zh": "約定、承諾",
      "example_sentence": "友達と映画を見る約束をしました。",
      "example_translation": "我和朋友約定要一起看電影。"
    }
    """

    # 使用 'japanese' 會話類型，與一般聊天和英文學習分離
    response = chat_with_groq(user_id, prompt, session_type="japanese")

    try:
        if isinstance(response, str):
            logger.info(f"Response is a string: {response[:200]}")
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
            logger.info(f"Response has text attribute: {response_text[:200]}")
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
        return "抱歉，獲取日文單字時發生錯誤，請通知維護人員，謝謝。"

    required_fields = ["word", "hiragana", "romaji", "part_of_speech", "definition_ja",
                       "definition_zh", "example_sentence", "example_translation"]

    for field in required_fields:
        if field not in word_data:
            word_data[field] = ""
            logger.warning(f"Missing '{field}' field in word data. Set to empty string.")

    flex_bubble = create_japanese_flex_bubble(word_data)
    return FlexSendMessage(
        alt_text=f"日文單字：{word_data['word']}",
        contents=flex_bubble
    )


def create_japanese_flex_bubble(word_data):
    """
    使用 LINE SDK 的原生物件建立日文 Flex 訊息
    """
    # 生成單字發音連結（日文）
    try:
        word_audio_url = generate_audio_url(word_data["word"])
    except Exception as e:
        logger.error(f"Error occurred while generating Japanese word pronunciation URL: {str(e)}")
        word_audio_url = ""

    # 生成例句發音連結（日文）
    try:
        example_audio_url = generate_audio_url(word_data["example_sentence"])
    except Exception as e:
        logger.error(f"Error occurred while generating Japanese example sentence pronunciation URL: {str(e)}")
        example_audio_url = ""

    # 使用 LINE SDK 內建的物件
    header_box = BoxComponent(
        layout="vertical",
        contents=[
            TextComponent(text="📖日文單字", weight="bold", size="lg")
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
            text=f"あ {word_data.get('hiragana', '')}",
            size="md",
            color="#FF6B6B",
            wrap=True
        ),
        TextComponent(
            text=f"🔊 {word_data.get('romaji', '')}",
            size="md",
            color="#888888",
            wrap=True
        ),
        TextComponent(
            text=f"💡 日文解釋: {word_data['definition_ja']}",
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
                color="#FF6B6B"
            ),
            ButtonComponent(
                action=URIAction(
                    label="🔊 例句發音",
                    uri=example_audio_url
                ),
                style="secondary",
                color="#4ECDC4"
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
