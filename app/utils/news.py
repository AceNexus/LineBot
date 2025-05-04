import logging
import random
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup
from linebot.models import (
    FlexSendMessage, TextSendMessage,
    CarouselContainer, BubbleContainer,
    BoxComponent, TextComponent, ButtonComponent,
    URIAction
)

logger = logging.getLogger(__name__)
URL = 'https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant'


def get_news(count):
    return fetch_google_news_flex(count)


def fetch_google_news_flex(count):
    try:
        response = requests.get(URL, timeout=10)
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
                header_text = TextComponent(text="焦點新聞", weight="bold", color="#1f76e3", size="sm")
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
    api_url = "https://tinyurl.com/api-create.php"
    params = {"url": long_url}

    try:
        response = requests.get(api_url, params=params, timeout=5, verify=False)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"URL shortening failed: {e}")
        return long_url
