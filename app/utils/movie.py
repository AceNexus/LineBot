import logging
import re

import requests
from bs4 import BeautifulSoup
from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent,
    ButtonComponent, URIAction, CarouselContainer
)

logger = logging.getLogger(__name__)
MAX_MOVIES = 10
LINE_TODAY_URL = "https://today.line.me/tw/v2/movie/chart/trending"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def get_movies():
    """取得電影排行榜，回傳 Flex Message"""
    movie_list = get_line_today_top_movies()
    if not movie_list:
        logger.warning("無法取得電影資料")
        return None

    bubbles = [create_movie_bubble(movie) for movie in movie_list[:MAX_MOVIES]]
    bubbles = [b for b in bubbles if b]  # 過濾 None

    if bubbles:
        return FlexSendMessage(alt_text="電影排行榜", contents=CarouselContainer(contents=bubbles))
    return None


def create_movie_bubble(movie):
    """建立單一電影 Flex 卡片"""
    try:
        contents = [
            TextComponent(text=movie.get('中文片名', '未知電影'), weight="bold", size="lg", wrap=True)
        ]

        if movie.get('英文片名'):
            contents.append(TextComponent(text=movie['英文片名'], size="sm", color="#666666", wrap=True, margin="xs"))

        rating_box = []
        if movie.get('評分'):
            rating_box.append(TextComponent(text=f"⭐ {movie['評分']}", size="sm", color="#FFD700", flex=1))
        if movie.get('分級'):
            rating_box.append(TextComponent(text=f"🔞 {movie['分級']}", size="sm", color="#FF4757", flex=1))
        if rating_box:
            contents.append(BoxComponent(layout="horizontal", contents=rating_box, margin="sm"))

        for key, icon in [('片長', '⏱️'), ('類型', '🎬'), ('上映時間', '📅')]:
            if movie.get(key):
                contents.append(
                    TextComponent(text=f"{icon} {movie[key]}", size="sm", color="#666666", wrap=True, margin="xs"))

        footer = None
        if movie.get('預告片連結'):
            footer = BoxComponent(
                layout="vertical",
                contents=[ButtonComponent(
                    action=URIAction(label="觀看預告片", uri=movie['預告片連結']),
                    style="primary", color="#FF6B6B"
                )],
                paddingAll="20px"
            )

        return BubbleContainer(
            body=BoxComponent(layout="vertical", contents=contents, spacing="sm", paddingAll="20px"),
            footer=footer
        )
    except Exception as e:
        logger.error(f"建立電影卡片失敗: {e}")
        return None


def get_line_today_top_movies():
    """爬取 LINE TODAY 熱門電影榜單"""
    try:
        res = requests.get(LINE_TODAY_URL, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        movies = []
        for item in soup.find_all('li', class_='detailList-item'):
            movie = {}

            # 中文片名
            title = item.find('h2', class_='detailListItem-title')
            if title:
                movie['中文片名'] = title.get_text(strip=True)

            # 英文片名
            eng_title = item.find('h3', class_='detailListItem-engTitle')
            if eng_title:
                movie['英文片名'] = eng_title.get_text(strip=True)

            # 評分
            rating = item.find('span', class_='iconInfo-text')
            if rating:
                movie['評分'] = rating.get_text(strip=True)

            # 分級
            cert = item.find('div', class_='detailListItem-certificate')
            if cert:
                badge = cert.find('span', class_='glnBadge-text')
                if badge:
                    movie['分級'] = badge.get_text(strip=True)

            # 狀態資訊（片長/上映時間）
            status = item.find('div', class_='detailListItem-status')
            if status:
                text = status.get_text(strip=True)
                match = re.search(r'(\d+小時\d+分)', text)
                if match:
                    movie['片長'] = match.group(1)
                match = re.search(r'上映(\d+週|\d+天)', text)
                if match:
                    movie['上映時間'] = f"上映{match.group(1)}"

            # 類型
            category = item.find('div', class_='detailListItem-category')
            if category:
                text = category.get_text(strip=True)
                if '級' in text:
                    types = text.split('級')[-1]
                    type_list = [t for t in re.split(r'[•\s]+', types) if t]
                    if type_list:
                        movie['類型'] = ' • '.join(type_list)

            # 預告片
            trailer = item.find('a', class_='detailListItem-trailer')
            if trailer and trailer.has_attr('href'):
                movie['預告片連結'] = f"https://today.line.me{trailer['href']}"

            if movie.get('中文片名'):
                movies.append(movie)

        logger.info(f"共抓到 {len(movies)} 部電影")
        return movies

    except requests.RequestException as e:
        logger.error(f"網路請求失敗: {e}")
    except Exception as e:
        logger.error(f"解析失敗: {e}")
    return []
