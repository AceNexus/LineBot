import logging
import re

from bs4 import BeautifulSoup
from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent,
    ButtonComponent, URIAction, CarouselContainer, ImageComponent
)
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)
MAX_MOVIES = 12
LINE_TODAY_URL = "https://today.line.me/tw/v2/movie/chart/trending"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
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
        hero = None
        if movie.get('圖片'):
            hero = ImageComponent(
                url=movie['圖片'],
                size="full",
                aspectRatio="2:3",
                aspectMode="cover"
            )

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

        movie_info = [
            (movie.get('片長'), '⏱️'),
            (movie.get('類型'), '🎬'),
            (movie.get('上映時間'), '📅')
        ]

        for info, icon in movie_info:
            if info:
                contents.append(
                    TextComponent(text=f"{icon} {info}", size="sm", color="#666666", wrap=True, margin="xs"))

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
            hero=hero,
            body=BoxComponent(layout="vertical", contents=contents, spacing="sm", paddingAll="20px"),
            footer=footer
        )
    except Exception as e:
        logger.error(f"建立電影卡片失敗: {e}")
        return None


def get_line_today_top_movies():
    """LINE TODAY 電影爬蟲"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.set_extra_http_headers(HEADERS)
            page.goto(LINE_TODAY_URL, timeout=20000)

            # 等待並滾動載入
            page.wait_for_selector('li.detailList-item', timeout=15000)
            load_content(page)

            return parse_movies_from_html(page.content())
        except PlaywrightTimeoutError:
            logger.warning("載入超時")
            return []
        finally:
            browser.close()


def load_content(page):
    """一次性載入內容"""
    # 滾動到底部
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1000)

    # 觸發懶載入圖片
    page.evaluate("""
        document.querySelectorAll('figure.detailListItem-posterImage').forEach(el => {
            const src = el.getAttribute('data-bg') || el.getAttribute('data-src');
            if (src) el.style.backgroundImage = `url(${src})`;
        });
    """)
    page.wait_for_timeout(2000)


def parse_movies_from_html(html):
    """從 HTML 解析電影資料"""
    soup = BeautifulSoup(html, 'html.parser')
    movies = []

    for item in soup.find_all('li', class_='detailList-item'):
        movie = extract_movie_info(item)
        if movie.get('中文片名'):  # 只有有片名的才加入
            movies.append(movie)

    logger.info(f"共抓到 {len(movies)} 部電影，其中 {sum(1 for m in movies if '圖片' in m)} 部有圖片")
    return movies


def extract_movie_info(item):
    """從單一項目中提取電影資訊"""
    movie = {}

    # 圖片
    movie['圖片'] = extract_image_url(item)

    # 基本資訊
    movie['中文片名'] = extract_text_content(item, 'h2', 'detailListItem-title')
    movie['英文片名'] = extract_text_content(item, 'h3', 'detailListItem-engTitle')
    movie['評分'] = extract_text_content(item, 'span', 'iconInfo-text')

    # 分級
    cert_div = item.find('div', class_='detailListItem-certificate')
    if cert_div:
        badge = cert_div.find('span', class_='glnBadge-text')
        if badge:
            movie['分級'] = badge.get_text(strip=True)

    # 狀態資訊（片長/上映時間）
    extract_status_info(item, movie)

    # 類型
    extract_category_info(item, movie)

    # 預告片連結
    trailer = item.find('a', class_='detailListItem-trailer')
    if trailer and trailer.has_attr('href'):
        movie['預告片連結'] = f"https://today.line.me{trailer['href']}"

    return movie


def extract_image_url(item):
    """提取圖片 URL"""
    figure = item.find('figure', class_='detailListItem-posterImage')
    if not figure or not figure.has_attr('style'):
        return ""

    style = figure['style']
    patterns = [
        r"background-image:\s*url\(['\"]?(.*?)['\"]?\)",
        r"background:\s*url\(['\"]?(.*?)['\"]?\)",
        r"url\(['\"]?(.*?)['\"]?\)",
    ]

    for pattern in patterns:
        match = re.search(pattern, style, re.IGNORECASE)
        if match:
            img_url = match.group(1).strip('\'"').strip()
            if img_url and not img_url.startswith('data:'):
                return img_url
    return ""


def extract_text_content(item, tag, class_name):
    """提取文字內容的通用方法"""
    element = item.find(tag, class_=class_name)
    return element.get_text(strip=True) if element else ""


def extract_status_info(item, movie):
    """提取狀態資訊（片長和上映時間）"""
    status = item.find('div', class_='detailListItem-status')
    if status:
        text = status.get_text(strip=True)

        # 片長
        duration_match = re.search(r'(\d+小時\d+分)', text)
        if duration_match:
            movie['片長'] = duration_match.group(1)

        # 上映時間
        release_match = re.search(r'上映(\d+週|\d+天)', text)
        if release_match:
            movie['上映時間'] = f"上映{release_match.group(1)}"


def extract_category_info(item, movie):
    """提取類型資訊"""
    category = item.find('div', class_='detailListItem-category')
    if category:
        text = category.get_text(strip=True)
        if '級' in text:
            types = text.split('級')[-1]
            type_list = [t for t in re.split(r'[•\s]+', types) if t]
            if type_list:
                movie['類型'] = ' • '.join(type_list)
