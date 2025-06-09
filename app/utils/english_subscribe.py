import logging
from datetime import datetime
from typing import List, Dict, Optional

from linebot.models import (
    FlexSendMessage, BubbleContainer, BoxComponent,
    TextComponent, ButtonComponent, PostbackAction,
    BubbleStyle, BlockStyle, SeparatorComponent,
    TextSendMessage
)

from app.utils.english_words import DIFFICULTY_NAMES

logger = logging.getLogger(__name__)

# 訂閱時段
SUBSCRIPTION_TIMES = {
    '1': '09:00',
    '2': '12:00',
    '3': '15:00',
    '4': '18:00',
    '5': '21:00'
}

# 記憶體儲存訂閱資訊
_subscriptions: Dict[str, Dict] = {}


def save_subscription(user_id: str, difficulty_id: str, count: int, times: List[str]) -> None:
    """儲存訂閱設定"""
    _subscriptions[user_id] = {
        'difficulty_id': difficulty_id,
        'difficulty_name': DIFFICULTY_NAMES.get(difficulty_id, '未知難度'),
        'count': count,
        'times': times,
        'created_at': datetime.now().isoformat()
    }


def get_subscription(user_id: str) -> Optional[Dict]:
    """獲取訂閱設定"""
    return _subscriptions.get(user_id)


def cancel_subscription(user_id: str) -> bool:
    """取消訂閱"""
    if user_id in _subscriptions:
        del _subscriptions[user_id]
        return True
    return False


def handle_subscription_time(data: dict) -> tuple:
    """處理訂閱時段選擇"""
    difficulty_id, count, time_id = data['english_subscribe_time'][0].split('/')
    # 從現有訂閱中獲取已選擇的時段
    user_id = data.get('user_id', [''])[0]
    current_subscription = get_subscription(user_id)
    selected_times = current_subscription.get('times', []) if current_subscription else []

    # 如果時段已存在則移除，否則添加
    if time_id in selected_times:
        selected_times.remove(time_id)
    else:
        selected_times.append(time_id)

    return difficulty_id, int(count), selected_times


def handle_subscription_save(data: Dict, user_id: str) -> TextSendMessage:
    """處理訂閱儲存"""
    difficulty_id, count, times = data['english_subscribe_save'][0].split('/')
    save_subscription(
        user_id=user_id,
        difficulty_id=difficulty_id,
        count=int(count),
        times=times.split(',')
    )
    return TextSendMessage(text="訂閱設定已儲存！")


def handle_subscription_view(user_id: str) -> TextSendMessage:
    """處理訂閱查詢"""
    subscription = get_subscription(user_id)
    if subscription:
        return TextSendMessage(
            text=f"您的訂閱設定：\n"
                 f"難度：{subscription['difficulty_name']}\n"
                 f"數量：{subscription['count']} 個單字\n"
                 f"時段：{', '.join(subscription['times'])}"
        )
    return TextSendMessage(text="您目前沒有訂閱！")


def handle_subscription_cancel(user_id: str) -> TextSendMessage:
    """處理訂閱取消"""
    if cancel_subscription(user_id):
        return TextSendMessage(text="已取消訂閱！")
    return TextSendMessage(text="您目前沒有訂閱！")


def get_subscription_menu() -> FlexSendMessage:
    """生成英文訂閱選單"""
    title = TextComponent(
        text="📚 英文單字訂閱",
        weight="bold",
        size="xl",
        align="center",
        color="#FFFFFF",
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇訂閱選項",
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

    buttons = [
        ButtonComponent(
            action=PostbackAction(
                label="📖 設定訂閱",
                data="action=english_subscribe_setup"
            ),
            style="primary",
            color="#FFB366",
            margin="sm",
            height="sm"
        ),
        ButtonComponent(
            action=PostbackAction(
                label="📋 查閱訂閱",
                data="action=english_subscribe_view"
            ),
            style="primary",
            color="#FFB366",
            margin="sm",
            height="sm"
        ),
        ButtonComponent(
            action=PostbackAction(
                label="❌ 取消訂閱",
                data="action=english_subscribe_cancel"
            ),
            style="secondary",
            color="#FF7777",
            margin="sm",
            height="sm"
        )
    ]

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

    return FlexSendMessage(alt_text="英文訂閱選單", contents=bubble)


def get_difficulty_menu() -> FlexSendMessage:
    """生成訂閱難度選單"""
    title = TextComponent(
        text="📚 選擇單字難度",
        weight="bold",
        size="xl",
        align="center",
        color="#FFFFFF",
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇訂閱的單字難度等級",
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
    for level_id, level_name in DIFFICULTY_NAMES.items():
        button = ButtonComponent(
            action=PostbackAction(
                label=f"📖 {level_name}",
                data=f"english_subscribe_difficulty={level_id}"
            ),
            style="primary",
            color="#FFB366",
            margin="sm",
            height="sm"
        )
        buttons.append(button)

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

    return FlexSendMessage(alt_text="訂閱難度選單", contents=bubble)


def get_count_menu(difficulty_id: str) -> FlexSendMessage:
    """生成訂閱數量選單"""
    difficulty_name = DIFFICULTY_NAMES.get(difficulty_id, "英文單字")

    title = TextComponent(
        text=f"📚 {difficulty_name}",
        weight="bold",
        size="xl",
        align="center",
        color="#FFFFFF",
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇每次發送的單字數量",
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
    for count in range(1, 6):
        button = ButtonComponent(
            action=PostbackAction(
                label=f"📖 {count} 個單字",
                data=f"english_subscribe_count={difficulty_id}/{count}"
            ),
            style="primary",
            color="#FFB366",
            margin="sm",
            height="sm"
        )
        buttons.append(button)

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

    return FlexSendMessage(alt_text="訂閱數量選單", contents=bubble)


def get_time_menu(difficulty_id: str, count: int) -> FlexSendMessage:
    """生成訂閱時間選單"""
    title = TextComponent(
        text="⏰ 選擇訂閱時間",
        weight="bold",
        size="xl",
        align="center",
        color="#FFFFFF",
        wrap=True
    )

    subtitle = TextComponent(
        text="請選擇接收單字的時間（可多選）",
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
    for time_id, time_name in SUBSCRIPTION_TIMES.items():
        button = ButtonComponent(
            action=PostbackAction(
                label=f"⏰ {time_name}",
                data=f"english_subscribe_time={difficulty_id}/{count}/{time_id}"
            ),
            style="primary",
            color="#FFB366",
            margin="sm",
            height="sm"
        )
        buttons.append(button)

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

    return FlexSendMessage(alt_text="訂閱時間選單", contents=bubble)


def get_subscription_confirm(difficulty_id: str, count: int, selected_times: list) -> FlexSendMessage:
    """生成訂閱確認訊息"""
    difficulty_name = DIFFICULTY_NAMES.get(difficulty_id, "未知難度")
    time_names = [SUBSCRIPTION_TIMES.get(t, "未知時段") for t in selected_times]

    title = TextComponent(
        text="📝 訂閱確認",
        weight="bold",
        size="xl",
        align="center",
        color="#FFFFFF",
        wrap=True
    )

    content = TextComponent(
        text=f"您將訂閱以下內容：\n\n"
             f"📚 難度：{difficulty_name}\n"
             f"📊 數量：{count} 個單字\n"
             f"⏰ 時段：\n" + "\n".join([f"• {time}" for time in time_names]) + "\n\n"
                                                                              f"確認要訂閱嗎？",
        size="md",
        color="#E0E0E0",
        align="center",
        wrap=True,
        margin="lg"
    )

    body_box = BoxComponent(
        layout="vertical",
        contents=[
            title,
            SeparatorComponent(margin="lg", color="#666666"),
            content
        ],
        spacing="md",
        padding_all="lg",
        background_color="#404040"
    )

    confirm_button = ButtonComponent(
        action=PostbackAction(
            label="✅ 確認訂閱",
            data=f"english_subscribe_save={difficulty_id}/{count}/{','.join(selected_times)}"
        ),
        style="primary",
        color="#FFB366",
        margin="sm",
        height="sm"
    )

    footer_box = BoxComponent(
        layout="vertical",
        contents=[confirm_button],
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

    return FlexSendMessage(alt_text="訂閱確認", contents=bubble)
