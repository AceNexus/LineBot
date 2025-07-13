import json
import logging
from typing import Union

from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent,
    ButtonComponent, URIAction, CarouselContainer, PostbackAction, SeparatorComponent, BubbleStyle, BlockStyle
)

from app.services.groq_service import chat_with_groq
from app.utils.google_tts import generate_audio_url
from app.utils.theme import COLOR_THEME

logger = logging.getLogger(__name__)

# 英文單字難度等級
DIFFICULTY_LEVELS = {
    '1': 'beginner',
    '2': 'intermediate',
    '3': 'advanced'
}

# 難度名稱
DIFFICULTY_NAMES = {
    '1': '初級',
    '2': '中級',
    '3': '高級'
}


def get_english_words(chat_id: str, difficulty_id: int, count: int):
    """獲取指定難度和數量的英文單字"""
    difficulty_level = DIFFICULTY_LEVELS.get(str(difficulty_id))
    difficulty_name = DIFFICULTY_NAMES.get(str(difficulty_id), '英文單字')

    if not difficulty_level:
        return f"找不到難度代碼：{difficulty_id}"

    return fetch_english_words_flex(chat_id, difficulty_name, difficulty_level, count)


def fetch_english_words_flex(chat_id: str, difficulty_name: str, difficulty_level: str, count: int):
    """獲取英文單字並轉換為 Flex Message"""
    try:
        # 準備 bubbles 用於 carousel
        bubbles = []

        for i in range(count):
            word_data = get_single_english_word(chat_id, difficulty_level)

            if isinstance(word_data, dict):
                # 創建單字的 bubble
                bubble = create_word_bubble(word_data, difficulty_name)
                bubbles.append(bubble)
            else:
                logger.warning(f"Failed to generate word {i + 1}: {word_data}")

        if not bubbles:
            return "抱歉，無法生成英文單字，請稍後再試。"

        # 如果只有一個單字，直接返回 FlexSendMessage
        if len(bubbles) == 1:
            return FlexSendMessage(
                alt_text=f"英文單字學習 - {difficulty_name}",
                contents=bubbles[0]
            )

        # 多個單字使用 carousel
        carousel = CarouselContainer(contents=bubbles)

        flex_message = FlexSendMessage(
            alt_text=f"英文單字學習 - {difficulty_name} ({count}個)",
            contents=carousel
        )

        return flex_message

    except Exception as e:
        logger.error(f"Failed to fetch English words: {e}")
        return "無法取得英文單字內容"


def get_single_english_word(chat_id: str, difficulty_level: str) -> Union[dict, str]:
    """
    獲取單個英文單字
    """
    # 根據難度等級調整 prompt
    difficulty_prompts = {
        'beginner': "請選擇適合初學者的基礎英文單字，常見於日常對話中的簡單詞彙（如CEFR A1-A2級別）",
        'intermediate': "請選擇難度符合台灣常見的「三千單」詞彙等級（如全民英檢中級、CEFR B1-B2級）的單字，應為日常生活中常見且實用的詞彙",
        'advanced': "請選擇較具挑戰性的高級英文單字，適合進階學習者（如CEFR C1-C2級別），包含學術或專業領域常用詞彙"
    }

    prompt = f"""請提供一個英文單字的學習內容，包含以下欄位：

    1. 單字 (word)
    2. 發音（使用台灣常見的 KK 音標）(pronunciation)
    3. 詞性 (part_of_speech)
    4. 英文解釋 (definition_en)
    5. 中文解釋 (definition_zh)
    6. 例句 (example_sentence)
    7. 例句翻譯 (example_translation)

    {difficulty_prompts.get(difficulty_level, difficulty_prompts['intermediate'])}

    請以 **純 JSON 格式** 回覆，**不要添加多餘說明或文字**，並請確認所有資訊準確無誤。

    以下為格式範例：
    {{
      "word": "negotiate",
      "pronunciation": "/nɪˈɡoʊʃiˌeɪt/",
      "part_of_speech": "verb",
      "definition_en": "to discuss something formally in order to reach an agreement",
      "definition_zh": "協商、談判",
      "example_sentence": "We need to negotiate a better deal with the supplier.",
      "example_translation": "我們需要與供應商協商更好的條件。"
    }}
    """

    # 使用 'english' 會話類型，與一般聊天和日文學習分離
    response = chat_with_groq(chat_id, prompt, session_type="english")

    try:
        if isinstance(response, str):
            logger.info(f"Response is a string: {response}")
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
            logger.info(f"Response has text attribute: {response_text}")
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
        return "抱歉，獲取英文單字時發生錯誤，請通知維護人員，謝謝。"

    required_fields = ["word", "pronunciation", "part_of_speech", "definition_en",
                       "definition_zh", "example_sentence", "example_translation"]

    for field in required_fields:
        if field not in word_data:
            word_data[field] = ""
            logger.warning(f"Missing '{field}' field in word data. Set to empty string.")

    return word_data


def create_word_bubble(word_data: dict, difficulty_name: str):
    """
    創建單字的 bubble
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

    # Header
    header_box = BoxComponent(
        layout="vertical",
        contents=[
            TextComponent(text=f"{difficulty_name}", weight="bold", size="lg", color=COLOR_THEME['text_primary'])
        ],
        background_color=COLOR_THEME['card']
    )

    # Body
    body_contents = [
        TextComponent(
            text=f"{word_data['word']} ({word_data['part_of_speech']})",
            weight="bold",
            size="xl",
            color=COLOR_THEME['text_primary'],
            wrap=True
        ),
        TextComponent(
            text=f"🔊 {word_data.get('pronunciation', '')}",
            size="md",
            color=COLOR_THEME['info'],
            wrap=True
        ),
        TextComponent(
            text=f"💡 英文解釋: {word_data['definition_en']}",
            size="sm",
            color=COLOR_THEME['text_secondary'],
            wrap=True
        ),
        TextComponent(
            text=f"📘 中文解釋: {word_data['definition_zh']}",
            size="sm",
            color=COLOR_THEME['text_secondary'],
            wrap=True
        ),
        TextComponent(
            text="✏️ 例句:",
            weight="bold",
            size="sm",
            color=COLOR_THEME['text_primary'],
            wrap=True
        ),
        TextComponent(
            text=f"● {word_data['example_sentence']}",
            wrap=True,
            size="sm",
            color=COLOR_THEME['text_primary']
        ),
        TextComponent(
            text=f"○ {word_data['example_translation']}",
            wrap=True,
            size="sm",
            color=COLOR_THEME['text_secondary']
        )
    ]

    body_box = BoxComponent(
        layout="vertical",
        spacing="md",
        contents=body_contents,
        background_color=COLOR_THEME['card']
    )

    # Footer
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
                color=COLOR_THEME['primary'],
                height="sm",
                margin="sm"
            ),
            ButtonComponent(
                action=URIAction(
                    label="🔊 例句發音",
                    uri=example_audio_url
                ),
                style="secondary",
                color=COLOR_THEME['info'],
                height="sm",
                margin="sm"
            )
        ],
        background_color=COLOR_THEME['card'],
        padding_all="lg"
    )

    # 建立 BubbleContainer
    bubble = BubbleContainer(
        header=header_box,
        body=body_box,
        footer=footer_box,
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card']),
            footer=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )

    return bubble


def get_english_difficulty_menu() -> FlexSendMessage:
    """生成英文單字難度選單 - 宮格樣式"""

    title = TextComponent(
        text="英文單字學習",
        weight="bold",
        size="xl",
        align="center",
        color=COLOR_THEME['text_primary'],
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇單字難度等級",
        size="sm",
        color=COLOR_THEME['text_secondary'],
        align="center",
        wrap=True,
        margin="sm"
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[
            title,
            subtitle,
            SeparatorComponent(margin="lg", color=COLOR_THEME['separator'])
        ],
        spacing="md",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    # 建立宮格按鈕（每列 3 顆）
    difficulty_items = list(DIFFICULTY_NAMES.items())
    grid_rows = []

    for i in range(0, len(difficulty_items), 3):
        row_buttons = []
        for j in range(3):
            index = i + j
            if index < len(difficulty_items):
                key, name = difficulty_items[index]
                button = ButtonComponent(
                    action=PostbackAction(
                        label=name,
                        data=f"english_difficulty={key}",
                        display_text=f"英文單字難度：{name}"
                    ),
                    style="primary",
                    color=COLOR_THEME['primary'] if index % 2 == 0 else COLOR_THEME['info'],
                    flex=1,
                    height="sm"
                )
                row_buttons.append(button)
        grid_rows.append(BoxComponent(
            layout="horizontal",
            contents=row_buttons,
            spacing="xs"
        ))

    footer_box = BoxComponent(
        layout="vertical",
        contents=grid_rows,
        spacing="sm",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    bubble = BubbleContainer(
        body=body_box,
        footer=footer_box,
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card']),
            footer=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )

    return FlexSendMessage(
        alt_text="英文單字難度選單",
        contents=bubble
    )


def get_english_count_menu(difficulty_id: str) -> FlexSendMessage:
    """生成英文單字數量選單 - 6 宮格佈局"""
    difficulty_name = DIFFICULTY_NAMES.get(difficulty_id, "英文單字")

    title = TextComponent(
        text=f"{difficulty_name}",
        weight="bold",
        size="xl",
        align="center",
        color=COLOR_THEME['text_primary'],
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇要學習的單字數量",
        size="sm",
        color=COLOR_THEME['text_secondary'],
        align="center",
        wrap=True,
        margin="sm"
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[
            title,
            subtitle,
            SeparatorComponent(margin="lg", color=COLOR_THEME['separator'])
        ],
        spacing="md",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    # 6 宮格按鈕（2 行 × 3 列）
    grid_rows = []
    for row in range(2):  # 2 行
        row_buttons = []
        for col in range(3):  # 每行 3 顆
            count = row * 3 + col + 1
            button = ButtonComponent(
                action=PostbackAction(
                    label=f"{count}",
                    data=f"english_count={difficulty_id}/{count}",
                    display_text = f"英文單字：學習{difficulty_name}，共 {count} 個單字"
                ),
                style="primary",
                color=COLOR_THEME['primary'] if count % 2 == 1 else COLOR_THEME['info'],
                flex=1,
                height="sm"
            )
            row_buttons.append(button)

        grid_rows.append(BoxComponent(
            layout="horizontal",
            contents=row_buttons,
            spacing="xs"
        ))

    footer_box = BoxComponent(
        layout="vertical",
        contents=grid_rows,
        spacing="sm",
        padding_all="lg",
        background_color=COLOR_THEME['card']
    )

    bubble = BubbleContainer(
        body=body_box,
        footer=footer_box,
        styles=BubbleStyle(
            body=BlockStyle(background_color=COLOR_THEME['card']),
            footer=BlockStyle(background_color=COLOR_THEME['card'])
        )
    )

    return FlexSendMessage(
        alt_text=f"{difficulty_name} 單字數量選單",
        contents=bubble
    )
