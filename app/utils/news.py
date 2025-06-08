import logging
import random
from typing import Optional, Union
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup
from linebot.models import (
    FlexSendMessage, TextSendMessage,
    CarouselContainer, BubbleContainer,
    BoxComponent, TextComponent, ButtonComponent,
    URIAction, PostbackAction,
    SeparatorComponent, BubbleStyle, BlockStyle
)

logger = logging.getLogger(__name__)

# 主題列表
TOPICS = {
    '1': 'https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRFptTXpJU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant',
    '2': 'https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx1YlY4U0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant',
    '3': 'https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRGx6TVdZU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant',
    '4': 'https://news.google.com/topics/CAAqLAgKIiZDQkFTRmdvSkwyMHZNR1ptZHpWbUVnVjZhQzFVVnhvQ1ZGY29BQVAB?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant',
    '5': 'https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNREpxYW5RU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant',
    '6': 'https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFp1ZEdvU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant',
    '7': 'https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNR3QwTlRFU0JYcG9MVlJYS0FBUAE?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant'
}

# 主題名稱
TOPIC_NAMES = {
    '1': '台灣',
    '2': '國際',
    '3': '商業',
    '4': '科技',
    '5': '娛樂',
    '6': '體育',
    '7': '健康'
}


def generate_news_topic_options() -> str:
    """生成新聞主題選項文字"""
    result = ["📰 新聞查詢", "格式：主題/數量", "範例：1/5 表示台灣新聞5則", ""]
    for key, name in TOPIC_NAMES.items():
        result.append(f"{key}. {name}")
    result.append("")
    result.append("💡 數量可選1-10則")
    return "\n".join(result)


def parse_news_format(msg: str) -> Optional[tuple]:
    """
    解析新聞格式：主題數字/數量數字
    例如：1/5 表示主題 1，數量 5
    """
    if '/' in msg:
        parts = msg.split('/')
        if len(parts) == 2:
            try:
                topic_id = int(parts[0].strip())
                count = int(parts[1].strip())
                return topic_id, count
            except ValueError:
                return None
    return None


def handle_news_input(msg: str) -> tuple[Union[str, FlexSendMessage], bool]:
    """
    處理新聞輸入，返回新聞內容或提示訊息
    返回: (結果, 是否成功處理)
    """
    parsed_result = parse_news_format(msg)
    if parsed_result:
        topic_id, count = parsed_result
        if 1 <= topic_id <= len(TOPIC_NAMES) and 1 <= count <= 10:
            return get_news(topic_id, count), True  # 成功獲取新聞
        else:
            return generate_news_topic_options(), False  # 參數錯誤，需要重新輸入
    else:
        return generate_news_topic_options(), False  # 格式錯誤，需要重新輸入


def get_news(topic_id, count):
    """獲取指定主題和數量的新聞"""
    topic_id = str(topic_id).strip()
    topic_url = TOPICS.get(topic_id)
    topic_name = TOPIC_NAMES.get(topic_id, '新聞')

    if not topic_url:
        return TextSendMessage(text=f"找不到主題代碼：{topic_id}")

    return fetch_google_news_flex(topic_name, topic_url, count)


def fetch_google_news_flex(topic_name, topic_url, count):
    """從 Google News 獲取新聞並轉換為 Flex Message"""
    try:
        response = requests.get(topic_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        news_links = soup.find_all('a', class_='gPFEn')

        random.shuffle(news_links)

        # 準備 bubbles 用於 carousel
        bubbles = []
        for i, link in enumerate(news_links):
            if i >= count:
                break

            title = link.text.strip()
            href = link.get('href', '')
            if href:
                full_url = unquote(urljoin('https://news.google.com/', href))
                short_url = shorten_url(full_url)

                # 為每條新聞創建一個 bubble
                header_text = TextComponent(text=topic_name, weight="bold", color="#1f76e3", size="sm")
                header_box = BoxComponent(layout="vertical", contents=[header_text], padding_bottom="md")

                body_text = TextComponent(text=title, weight="bold", wrap=True, size="md")
                body_box = BoxComponent(layout="vertical", contents=[body_text], spacing="sm", padding_all="md")

                button = ButtonComponent(
                    action=URIAction(label="閱讀全文", uri=short_url),
                    style="primary",
                    color="#1f76e3"
                )
                footer_box = BoxComponent(layout="vertical", contents=[button], padding_top="sm")

                bubble = BubbleContainer(
                    header=header_box,
                    body=body_box,
                    footer=footer_box,
                    size="kilo"
                )
                bubbles.append(bubble)

        # 將所有 bubble 放入 carousel 容器
        carousel = CarouselContainer(contents=bubbles)

        flex_message = FlexSendMessage(
            alt_text="Google 新聞摘要",
            contents=carousel
        )

        return flex_message

    except requests.RequestException as e:
        logger.error(f"Failed to retrieve Google News content: {e}")
        return TextSendMessage(text="無法取得新聞內容")


def shorten_url(long_url):
    """縮短 URL"""
    api_url = "https://tinyurl.com/api-create.php"
    params = {"url": long_url}

    try:
        response = requests.get(api_url, params=params, timeout=5, verify=False)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"URL shortening failed: {e}")
        return long_url


def get_news_topic_menu():
    """生成新聞主題選單"""
    title = TextComponent(
        text="📰 新聞主題",
        weight="bold",
        size="xl",
        align="center",
        color="#FFFFFF",
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇新聞主題",
        size="sm",
        color="#E0E0E0",
        align="center",
        wrap=True,
        margin="sm"
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[
            title,
            subtitle,
            SeparatorComponent(margin="lg", color="#666666")
        ],
        spacing="md",
        padding_all="lg",
        background_color="#404040"
    )

    buttons = []
    for topic_id, topic_name in TOPIC_NAMES.items():
        buttons.append(
            ButtonComponent(
                action=PostbackAction(
                    label=f"📰 {topic_name}",
                    data=f"news_topic={topic_id}"
                ),
                style="primary",
                color="#FF7777",
                margin="sm",
                height="sm"
            )
        )

    footer_box = BoxComponent(
        layout="vertical",
        contents=buttons,
        spacing="sm",
        padding_all="lg",
        background_color="#404040"
    )

    bubble = BubbleContainer(
        body=body_box,
        footer=footer_box,
        styles=BubbleStyle(
            body=BlockStyle(background_color="#404040"),
            footer=BlockStyle(background_color="#404040")
        )
    )

    return FlexSendMessage(alt_text="新聞主題選單", contents=bubble)


def get_news_count_menu(topic_id: str):
    """生成新聞數量選單"""
    topic_name = TOPIC_NAMES.get(topic_id, '新聞')

    title = TextComponent(
        text=f"📰 {topic_name}新聞",
        weight="bold",
        size="xl",
        align="center",
        color="#FFFFFF",
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇要顯示的新聞數量",
        size="sm",
        color="#E0E0E0",
        align="center",
        wrap=True,
        margin="sm"
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[
            title,
            subtitle,
            SeparatorComponent(margin="lg", color="#666666")
        ],
        spacing="md",
        padding_all="lg",
        background_color="#404040"
    )

    buttons = []
    for count in range(1, 11):
        buttons.append(
            ButtonComponent(
                action=PostbackAction(
                    label=f"{count} 則",
                    data=f"news_count={topic_id}/{count}"
                ),
                style="primary",
                color="#FF7777",
                margin="sm",
                height="sm"
            )
        )

    footer_box = BoxComponent(
        layout="vertical",
        contents=buttons,
        spacing="sm",
        padding_all="lg",
        background_color="#404040"
    )

    bubble = BubbleContainer(
        body=body_box,
        footer=footer_box,
        styles=BubbleStyle(
            body=BlockStyle(background_color="#404040"),
            footer=BlockStyle(background_color="#404040")
        )
    )

    return FlexSendMessage(alt_text="新聞數量選單", contents=bubble)
