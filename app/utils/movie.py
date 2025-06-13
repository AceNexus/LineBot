import logging
import re
import time
import urllib.parse
from typing import Optional, List, Dict

from bs4 import BeautifulSoup
from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent,
    ButtonComponent, URIAction, CarouselContainer, ImageComponent
)
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from app.utils.theme import COLOR_THEME

logger = logging.getLogger(__name__)

# 配置
MAX_MOVIES = 12
LINE_TODAY_URL = "https://today.line.me/tw/v2/movie/chart/trending"
CACHE_TTL = 6 * 60 * 60  # 6 小時快取

# 快取
_cache = {'message': None, 'timestamp': 0}

# 請求標頭
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def get_movies(force_refresh: bool = False) -> Optional[FlexSendMessage]:
    """取得電影排行榜"""
    # 檢查快取
    if not force_refresh and _is_cache_valid():
        logger.info("使用快取")
        return _cache['message']

    # 取得新資料
    logger.info("取得新資料")
    movies = scrape_movies()
    if not movies:
        return None

    # 建立 Flex Message
    bubbles = [create_bubble(movie) for movie in movies[:MAX_MOVIES]]
    bubbles = [b for b in bubbles if b]

    if bubbles:
        flex_msg = FlexSendMessage(
            alt_text="電影排行榜",
            contents=CarouselContainer(contents=bubbles)
        )
        # 更新快取
        _cache.update({'message': flex_msg, 'timestamp': time.time()})
        return flex_msg

    return None


def _is_cache_valid() -> bool:
    """檢查快取是否有效"""
    return (_cache['message'] is not None and
            time.time() - _cache['timestamp'] < CACHE_TTL)


def scrape_movies() -> List[Dict]:
    """爬取電影資料"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.set_extra_http_headers(HEADERS)
            page.goto(LINE_TODAY_URL, timeout=20000)
            page.wait_for_selector('li.detailList-item', timeout=15000)

            # 滾動載入內容
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)

            # 觸發圖片懶載入
            page.evaluate("""
                document.querySelectorAll('figure.detailListItem-posterImage').forEach(el => {
                    const src = el.getAttribute('data-bg') || el.getAttribute('data-src');
                    if (src) el.style.backgroundImage = `url(${src})`;
                });
            """)
            page.wait_for_timeout(2000)

            return parse_html(page.content())

        except PlaywrightTimeoutError:
            logger.warning("請求逾時")
            return []
        finally:
            browser.close()


def parse_html(html: str) -> List[Dict]:
    """解析 HTML 取得電影資訊"""
    soup = BeautifulSoup(html, 'html.parser')
    movies = []

    for item in soup.find_all('li', class_='detailList-item'):
        movie = extract_movie_data(item)
        if movie.get('title'):
            movies.append(movie)

    logger.info(f"取得到 {len(movies)} 部電影")
    return movies


def extract_movie_data(item) -> Dict:
    """提取單一電影資料"""
    movie = {}

    # 基本資訊
    movie['title'] = get_text(item, 'h2', 'detailListItem-title')
    movie['eng_title'] = get_text(item, 'h3', 'detailListItem-engTitle')
    movie['rating'] = get_text(item, 'span', 'iconInfo-text')

    # 圖片
    movie['image'] = extract_image(item)

    # 分級
    cert_div = item.find('div', class_='detailListItem-certificate')
    if cert_div:
        badge = cert_div.find('span', class_='glnBadge-text')
        if badge:
            movie['cert'] = badge.get_text(strip=True)

    # 狀態資訊（片長、上映時間）
    status_div = item.find('div', class_='detailListItem-status')
    if status_div:
        text = status_div.get_text(strip=True)
        duration_match = re.search(r'(\d+小時\d+分)', text)
        if duration_match:
            movie['duration'] = duration_match.group(1)

        release_match = re.search(r'上映(\d+週|\d+天)', text)
        if release_match:
            movie['release'] = f"上映{release_match.group(1)}"

    # 類型
    category_div = item.find('div', class_='detailListItem-category')
    if category_div:
        text = category_div.get_text(strip=True)
        if '級' in text:
            types = text.split('級')[-1]
            type_list = [t for t in re.split(r'[•\s]+', types) if t]
            if type_list:
                movie['genre'] = ' • '.join(type_list)

    # 預告片連結
    trailer = item.find('a', class_='detailListItem-trailer')
    if trailer and trailer.has_attr('href'):
        movie['trailer'] = f"https://today.line.me{trailer['href']}"

    return movie


def get_text(item, tag: str, class_name: str) -> str:
    """取得文字內容"""
    element = item.find(tag, class_=class_name)
    return element.get_text(strip=True) if element else ""


def extract_image(item) -> str:
    """提取圖片URL"""
    figure = item.find('figure', class_='detailListItem-posterImage')
    if not figure or not figure.has_attr('style'):
        return ""

    style = figure['style']
    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style, re.IGNORECASE)
    if match:
        img_url = match.group(1).strip('\'"').strip()
        if img_url and not img_url.startswith('data:'):
            return img_url
    return ""


def create_bubble(movie: Dict) -> Optional[BubbleContainer]:
    """建立電影卡片"""
    try:
        # 圖片
        hero = None
        if movie.get('image'):
            hero = ImageComponent(
                url=movie['image'],
                size="full",
                aspectRatio="2:3",
                aspectMode="cover"
            )

        # 內容
        contents = [
            TextComponent(text=movie.get('title', '未知電影'), weight="bold", size="lg", wrap=True)
        ]

        if movie.get('eng_title'):
            contents.append(TextComponent(
                text=movie['eng_title'],
                size="sm",
                color=COLOR_THEME['text_secondary'],
                wrap=True,
                margin="xs"
            ))

        # 評分和分級
        rating_box = []
        if movie.get('rating'):
            rating_box.append(
                TextComponent(text=f"⭐ {movie['rating']}", size="sm", color=COLOR_THEME['warning'], flex=1))
        if movie.get('cert'):
            rating_box.append(TextComponent(text=f"🔞 {movie['cert']}", size="sm", color=COLOR_THEME['error'], flex=1))
        if rating_box:
            contents.append(BoxComponent(layout="horizontal", contents=rating_box, margin="sm"))

        # 其他資訊
        for info, icon in [(movie.get('duration'), '⏱️'), (movie.get('genre'), '🎬'), (movie.get('release'), '📅')]:
            if info:
                contents.append(
                    TextComponent(text=f"{icon} {info}", size="sm", color=COLOR_THEME['text_secondary'], wrap=True,
                                  margin="xs"))

        # 按鈕
        buttons = []
        if movie.get('trailer'):
            buttons.append(ButtonComponent(
                action=URIAction(label="官方預告", uri=movie['trailer']),
                style="primary",
                color=COLOR_THEME['primary'],
                margin="sm",
                height="sm",
                flex=1
            ))

        # YouTube搜尋連結
        youtube_url = create_youtube_link(movie.get('title', ''))
        buttons.append(ButtonComponent(
            action=URIAction(label="YouTube預告", uri=youtube_url),
            style="secondary",
            color=COLOR_THEME['info'],
            margin="sm",
            height="sm",
            flex=1
        ))

        footer = None
        if buttons:
            footer = BoxComponent(
                layout="vertical",
                contents=[BoxComponent(layout="horizontal", contents=buttons, spacing="sm")],
                padding_all="lg"
            )

        return BubbleContainer(
            hero=hero,
            body=BoxComponent(layout="vertical", contents=contents, spacing="sm", paddingAll="20px"),
            footer=footer
        )

    except Exception as e:
        logger.error(f"建立卡片失敗: {e}")
        return None


def create_youtube_link(title: str) -> str:
    """建立 YouTube 搜尋連結"""
    clean_title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', title.strip())
    query = f"{clean_title} 官方預告片"
    return f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
