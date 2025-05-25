import logging
import re

from bs4 import BeautifulSoup
from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent,
    ButtonComponent, URIAction, CarouselContainer, ImageComponent
)
from playwright.sync_api import sync_playwright

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
            hero=hero,
            body=BoxComponent(layout="vertical", contents=contents, spacing="sm", paddingAll="20px"),
            footer=footer
        )
    except Exception as e:
        logger.error(f"建立電影卡片失敗: {e}")
        return None


def get_line_today_top_movies():
    """用 Playwright 爬取 LINE TODAY 熱門電影榜單，確保動態載入的背景圖片完全載入"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # 設定 User-Agent 和其他標頭
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            })

            # 設定視窗大小
            page.set_viewport_size({"width": 1920, "height": 1080})

            page.goto(LINE_TODAY_URL, timeout=20000)

            # 等待電影列表載入
            page.wait_for_selector('li.detailList-item', timeout=15000)

            # 多次滾動載入策略
            for i in range(3):
                # 慢慢滾動到底部
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)")
                page.wait_for_timeout(1000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                page.wait_for_timeout(1000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)

                # 滾回頂部
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(1000)

            # 強制觸發圖片載入 - 使用 JavaScript 直接操作
            page.evaluate("""
                // 強制觸發所有圖片載入
                const figures = document.querySelectorAll('figure.detailListItem-posterImage');
                figures.forEach(figure => {
                    // 觸發重繪
                    figure.style.display = 'none';
                    figure.offsetHeight; // 強制重排
                    figure.style.display = '';

                    // 如果有 data-src 屬性，複製到 style
                    const dataSrc = figure.getAttribute('data-bg') || figure.getAttribute('data-background');
                    if (dataSrc && !figure.style.backgroundImage) {
                        figure.style.backgroundImage = `url(${dataSrc})`;
                    }
                });
            """)

            # 再等待一下
            page.wait_for_timeout(3000)

            # 檢查是否有圖片載入
            image_count = page.evaluate("""
                document.querySelectorAll('figure.detailListItem-posterImage[style*="background-image"]').length
            """)
            logger.info(f"頁面中找到 {image_count} 個有背景圖片的元素")

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')

        movies = []
        for item in soup.find_all('li', class_='detailList-item'):
            movie = {}

            # 圖片
            figure = item.find('figure', class_='detailListItem-posterImage')
            if figure:
                img_found = False

                # 從 style 屬性擷取背景圖片
                if figure.has_attr('style') and not img_found:
                    style = figure['style']
                    # 更強健的正則表達式
                    patterns = [
                        r"background-image:\s*url\(['\"]?(.*?)['\"]?\)",
                        r"background:\s*url\(['\"]?(.*?)['\"]?\)",
                        r"url\(['\"]?(.*?)['\"]?\)",
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, style, re.IGNORECASE)
                        if match:
                            img_url = match.group(1)
                            # 清理URL
                            img_url = img_url.strip('\'"').strip()
                            if img_url and not img_url.startswith('data:'):
                                movie['圖片'] = img_url
                                img_found = True
                                break

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
                # 片長
                match = re.search(r'(\d+小時\d+分)', text)
                if match:
                    movie['片長'] = match.group(1)
                # 上映時間
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

            # 預告片連結
            trailer = item.find('a', class_='detailListItem-trailer')
            if trailer and trailer.has_attr('href'):
                movie['預告片連結'] = f"https://today.line.me{trailer['href']}"

            # 只有有片名的才加入結果
            if movie.get('中文片名'):
                movies.append(movie)

        logger.info(f"共抓到 {len(movies)} 部電影，其中 {sum(1 for m in movies if '圖片' in m)} 部有圖片")
        return movies

    except Exception as e:
        logger.error(f"動態載入電影資料失敗: {e}")
        return []
