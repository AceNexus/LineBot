import logging
import random
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
URL = 'https://news.google.com/topics/CAAqKggKIiRDQkFTRlFvSUwyMHZNRFZxYUdjU0JYcG9MVlJYR2dKVVZ5Z0FQAQ?hl=zh-TW&gl=TW&ceid=TW%3Azh-Hant'


def get_news():
    return fetch_google_news_text(1)


def fetch_google_news_text(count=1):
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        news_links = soup.find_all('a', class_='gPFEn')

        random.shuffle(news_links)

        results = []
        for link in news_links:
            title = link.text.strip()
            href = link.get('href', '')
            if href:
                full_url = unquote(urljoin('https://news.google.com/', href))
                short_url = shorten_url(full_url)
                results.append((title, short_url))

                # 檢查是否已獲取足夠數量的新聞，如果是則跳出循環
                if len(results) >= count:
                    break

        return '\n'.join([f"{title}\n{short_url}" for title, short_url in results])

    except requests.RequestException as e:
        logger.error(f"Failed to retrieve Google News content: {e}")
        return "無法取得新聞內容"


def shorten_url(long_url):
    api_url = "https://tinyurl.com/api-create.php"
    params = {"url": long_url}

    try:
        response = requests.get(api_url, params=params, timeout=5)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"URL shortening failed: {e}")
        return long_url
