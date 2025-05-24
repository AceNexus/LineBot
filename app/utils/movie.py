import re

import requests
from bs4 import BeautifulSoup
from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent,
    ButtonComponent, URIAction,
    CarouselContainer
)


def get_movies():
    """取得 LINE TODAY 電影排行榜並產生 Flex Message"""
    # 取得電影資料
    movies = get_line_today_top_movies()

    if not movies:
        return None

    # 產生 Flex Message carousel（最多顯示前10部電影）
    bubbles = []
    for movie in movies[:10]:  # 限制最多 10 個 bubble
        bubble = create_movie_bubble(movie)
        if bubble:
            bubbles.append(bubble)

    if bubbles:
        carousel_container = CarouselContainer(contents=bubbles)
        flex_message = FlexSendMessage(
            alt_text="電影排行榜",
            contents=carousel_container
        )
        return flex_message

    return None


def create_movie_bubble(movie_data):
    """為 single 電影資料創建 Flex Bubble"""
    try:
        body_contents = []

        title_box = BoxComponent(
            layout="horizontal",
            contents=[
                TextComponent(
                    text=f"#{movie_data.get('排名', 'N/A')}",
                    weight="bold",
                    color="#FF6B6B",
                    size="lg",
                    flex=0
                ),
                TextComponent(
                    text=movie_data.get('中文片名', '未知電影'),
                    weight="bold",
                    size="lg",
                    wrap=True,
                    flex=1,
                    margin="sm"
                )
            ],
            spacing="sm"
        )
        body_contents.append(title_box)

        # 英文片名
        if movie_data.get('英文片名'):
            body_contents.append(
                TextComponent(
                    text=movie_data['英文片名'],
                    size="sm",
                    color="#666666",
                    wrap=True,
                    margin="xs"
                )
            )

        # 評分和分級
        info_contents = []
        if movie_data.get('評分'):
            info_contents.append(
                TextComponent(
                    text=f"⭐ {movie_data['評分']}",
                    size="sm",
                    color="#FFD700",
                    flex=1
                )
            )

        if movie_data.get('分級'):
            info_contents.append(
                TextComponent(
                    text=f"🔞 {movie_data['分級']}",
                    size="sm",
                    color="#FF4757",
                    flex=1
                )
            )

        if info_contents:
            info_box = BoxComponent(
                layout="horizontal",
                contents=info_contents,
                spacing="sm"
            )
            body_contents.append(info_box)

        # 片長和類型
        detail_contents = []
        if movie_data.get('片長'):
            detail_contents.append(
                TextComponent(
                    text=f"⏱️ {movie_data['片長']}",
                    size="sm",
                    color="#666666"
                )
            )

        if movie_data.get('類型'):
            detail_contents.append(
                TextComponent(
                    text=f"🎬 {movie_data['類型']}",
                    size="sm",
                    color="#666666",
                    wrap=True
                )
            )

        for content in detail_contents:
            body_contents.append(content)

        # 上映時間
        if movie_data.get('上映時間'):
            body_contents.append(
                TextComponent(
                    text=f"📅 {movie_data['上映時間']}",
                    size="sm",
                    color="#666666"
                )
            )

        # 排名變化
        if movie_data.get('排名變化'):
            change_color = "#2ED573" if "↑" in movie_data['排名變化'] else "#FF4757"
            body_contents.append(
                TextComponent(
                    text=f"📈 {movie_data['排名變化']}",
                    size="sm",
                    color=change_color
                )
            )

        # 建立 body
        body = BoxComponent(
            layout="vertical",
            contents=body_contents,
            spacing="sm",
            padding_all="20px"
        )

        # 建立 footer（如果有預告片連結）
        footer = None
        if movie_data.get('預告片連結'):
            footer = BoxComponent(
                layout="vertical",
                contents=[
                    ButtonComponent(
                        action=URIAction(
                            label="觀看預告片",
                            uri=movie_data['預告片連結']
                        ),
                        style="primary",
                        color="#FF6B6B"
                    )
                ],
                spacing="sm",
                padding_all="20px"
            )

        bubble = BubbleContainer(
            body=body,
            footer=footer
        )

        return bubble

    except Exception as e:
        print(f"創建電影bubble失敗: {e}")
        return None


def get_line_today_top_movies():
    """爬取 LINE TODAY 電影排行榜"""
    url = "https://today.line.me/tw/v2/movie/chart/trending"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        movie_list = []
        movie_items = soup.find_all('li', class_='detailList-item')

        for item in movie_items:
            movie_data = {}

            # 排名
            ranking_elem = item.find('div', class_='detailListItem-ranking')
            if ranking_elem:
                rank_badge = ranking_elem.find('span', class_='glnBadge-text')
                if rank_badge:
                    movie_data['排名'] = rank_badge.get_text(strip=True)

                # 排名變化
                rank_change = ranking_elem.find('span', class_='rankingBadge-rankChange')
                if rank_change:
                    movie_data['排名變化'] = rank_change.get_text(strip=True)

            # 中文片名
            title_elem = item.find('h2', class_='detailListItem-title')
            if title_elem:
                movie_data['中文片名'] = title_elem.get_text(strip=True)

            # 英文片名
            eng_title_elem = item.find('h3', class_='detailListItem-engTitle')
            if eng_title_elem:
                movie_data['英文片名'] = eng_title_elem.get_text(strip=True)

            # 評分
            rating_elem = item.find('span', class_='iconInfo-text')
            if rating_elem:
                movie_data['評分'] = rating_elem.get_text(strip=True)

            # 片長和上映時間
            status_elem = item.find('div', class_='detailListItem-status')
            if status_elem:
                status_text = status_elem.get_text(strip=True)
                duration_match = re.search(r'(\d+小時\d+分)', status_text)
                if duration_match:
                    movie_data['片長'] = duration_match.group(1)
                screening_match = re.search(r'上映(\d+週|\d+天)', status_text)
                if screening_match:
                    movie_data['上映時間'] = screening_match.group(0)

            # 分級
            certificate_elem = item.find('div', class_='detailListItem-certificate')
            if certificate_elem:
                cert_text = certificate_elem.find('span', class_='glnBadge-text')
                if cert_text:
                    movie_data['分級'] = cert_text.get_text(strip=True)

            # 類型
            category_elem = item.find('div', class_='detailListItem-category')
            if category_elem:
                category_text = category_elem.get_text(strip=True)
                types = re.findall(r'[^•\s]+', category_text.split('級')[-1])
                if types:
                    movie_data['類型'] = ' • '.join([t.strip() for t in types if t.strip()])

            # 預告片連結
            trailer_elem = item.find('a', class_='detailListItem-trailer')
            if trailer_elem and trailer_elem.get('href'):
                movie_data['預告片連結'] = f"https://today.line.me{trailer_elem['href']}"

            # 背景圖片
            bg_image_elem = item.find('img', class_='detailListItem-backgroundImage')
            if bg_image_elem and bg_image_elem.get('src'):
                movie_data['背景圖片'] = bg_image_elem['src']
            else:
                # 嘗試其他可能的圖片選擇器
                img_elem = item.find('img')
                if img_elem and img_elem.get('src'):
                    movie_data['背景圖片'] = img_elem['src']

            if movie_data:
                movie_list.append(movie_data)

        return movie_list

    except Exception as e:
        print(f"LINE TODAY 爬取失敗: {e}")
        return []
